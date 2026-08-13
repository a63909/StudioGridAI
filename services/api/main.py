"""FastAPI application entry point for StudioGrid AI Tool Server."""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .core.event_bus import LocalEventBus
from .core.tool_registry import ToolRegistry
from .db.local_store import LocalStateStore
from .routers import events, production, scenes, shots, schedule, continuity, risks, report, tools

logger = logging.getLogger(__name__)

# Shared state
store = LocalStateStore()
event_bus = LocalEventBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load LAST LIGHT dataset on startup."""
    persistence = None
    package_path = Path(__file__).parent.parent.parent / "demo" / "last_light" / "production_package.json"
    if package_path.exists():
        with open(package_path, encoding="utf-8") as f:
            data = json.load(f)
        store.load_from_production_package(data)

        # Set shoot day to ACTIVE
        from .domain.enums import ShootDayStatus
        day = store.get_active_shoot_day()
        if day and store.production:
            updated_day = day.model_copy(update={"status": ShootDayStatus.ACTIVE})
            days = list(store.production.shootDays)
            idx = days.index(day)
            days[idx] = updated_day
            store.production = store.production.model_copy(update={"shootDays": days})

        if settings.STUDIOGRID_FIRESTORE_ENABLED:
            from .db.firestore_store import FirestoreStateStore
            from agents.google_adk.runtime import mark_runtime_error

            try:
                persistence = FirestoreStateStore(
                    project_id=settings.GOOGLE_CLOUD_PROJECT,
                    production_id=settings.STUDIOGRID_PRODUCTION_ID,
                    database=settings.FIRESTORE_DATABASE,
                )
                await persistence.healthcheck()
                durable_state = await persistence.get_application_state()
                if durable_state is None:
                    await persistence.save_application_state(store)
                else:
                    store.restore_application_state(durable_state)
            except Exception as exc:
                mark_runtime_error("FIRESTORE_UNAVAILABLE")
                settings.STUDIOGRID_AI_ENABLED = False
                logger.error(
                    "firestore_startup_failed",
                    extra={"errorCode": type(exc).__name__},
                )
                if persistence is not None:
                    await persistence.close()
                persistence = None

        app.state.persistence = persistence
        app.state.registry = ToolRegistry(
            store=store,
            event_bus=event_bus,
            persistence=persistence,
        )

        if settings.STUDIOGRID_AGENT_TOOL_SERVER_ONLY:
            # The private Cloud Run receiver exposes typed agent tools only.
            # Human routes stay available in the local/full application mode.
            app.state.orchestrator = None
        else:
            from agents.orchestrator import ProductionOrchestrator
            orchestrator = ProductionOrchestrator(store=store, event_bus=event_bus)
            app.state.orchestrator = orchestrator

        logger.info("last_light_dataset_loaded", extra={"productionId": data["productionId"]})
    else:
        logger.warning("last_light_dataset_not_found", extra={"path": str(package_path)})

    yield
    if persistence is not None:
        await persistence.close()
    logger.info("studiogrid_api_shutdown")


app = FastAPI(
    title="StudioGrid AI — Tool Server",
    description="Production control system for film shoots. Phase 2: Real Gemini AI.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def private_agent_tool_boundary(request: Request, call_next):
    """Hide every non-agent route in the private Cloud Run deployment."""
    if settings.STUDIOGRID_AGENT_TOOL_SERVER_ONLY:
        path = request.url.path
        if path != "/health" and not path.startswith("/tools/agent/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
    return await call_next(request)

# Inject shared state into routers
app.state.store = store
app.state.event_bus = event_bus
app.state.persistence = None
app.state.registry = ToolRegistry(store=store, event_bus=event_bus)

# Register routers
app.include_router(production.router, prefix="/production", tags=["production"])
app.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
app.include_router(shots.router, prefix="/shots", tags=["shots"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(continuity.router, prefix="/continuity", tags=["continuity"])
app.include_router(risks.router, prefix="/risks", tags=["risks"])
app.include_router(report.router, prefix="/report", tags=["report"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(tools.router, prefix="/tools", tags=["agent-tools"])


@app.get("/health")
async def health():
    """Health check — includes real AI runtime status."""
    ai_enabled = settings.STUDIOGRID_AI_ENABLED

    runtime_status = {"adkRuntime": "NOT_CONNECTED", "geminiStatus": "NOT_CONNECTED"}
    try:
        import agents.google_adk.runtime as rt
        runtime_status = rt.get_runtime_status()
    except Exception:
        pass

    return {
        "status": "ok",
        "version": "2.0.0",
        "agentMode": "PRODUCTION" if ai_enabled else "DEV",
        "aiEnabled": ai_enabled,
        "aiRuntime": runtime_status.get("adkRuntime", "NOT_CONNECTED"),
        "geminiStatus": runtime_status.get("geminiStatus", "NOT_CONNECTED"),
        "lastExecutionId": runtime_status.get("lastExecutionId"),
        "modelName": runtime_status.get("modelName", settings.GEMINI_MODEL),
        "connectionErrorCode": runtime_status.get("connectionErrorCode"),
        "modelLocation": runtime_status.get("modelLocation", settings.GOOGLE_CLOUD_LOCATION),
        "firestoreStatus": (
            "CONNECTED" if app.state.persistence is not None else "NOT_CONNECTED"
        ),
        "partnerStatus": "NOT_CONFIGURED",
    }

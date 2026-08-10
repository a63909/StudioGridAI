"""FastAPI application entry point for StudioGrid AI Tool Server."""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .core.event_bus import LocalEventBus
from .db.local_store import LocalStateStore
from .routers import events, production, scenes, shots, schedule, continuity, risks, report

logger = logging.getLogger(__name__)

# Shared state
store = LocalStateStore()
event_bus = LocalEventBus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load LAST LIGHT dataset on startup."""
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

        # Wire up orchestrator
        from agents.orchestrator import ProductionOrchestrator
        orchestrator = ProductionOrchestrator(store=store, event_bus=event_bus)
        app.state.orchestrator = orchestrator

        logger.info("last_light_dataset_loaded", extra={"productionId": data["productionId"]})
    else:
        logger.warning("last_light_dataset_not_found", extra={"path": str(package_path)})

    yield
    logger.info("studiogrid_api_shutdown")


app = FastAPI(
    title="StudioGrid AI — Tool Server",
    description="Production control system for film shoots. Phase 1: DEV MODE.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject shared state into routers
app.state.store = store
app.state.event_bus = event_bus

# Register routers
app.include_router(production.router, prefix="/production", tags=["production"])
app.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
app.include_router(shots.router, prefix="/shots", tags=["shots"])
app.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
app.include_router(continuity.router, prefix="/continuity", tags=["continuity"])
app.include_router(risks.router, prefix="/risks", tags=["risks"])
app.include_router(report.router, prefix="/report", tags=["report"])
app.include_router(events.router, prefix="/events", tags=["events"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agentMode": "DEV",
        "aiConnected": False,
        "partnerStatus": "NOT_CONFIGURED",
    }

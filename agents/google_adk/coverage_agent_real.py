"""Real Gemini Coverage Agent executed by the Google ADK orchestrator."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from pydantic import BaseModel, Field

from agents.interfaces import BaseAgent
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode, AlertStatus, EventType, OriginType, Severity
from services.api.domain.events import ProductionEvent
from services.api.domain.models import ToolCall
from services.api.tools.contracts import CreateCoverageAlertInput
from services.api.tools.http_client import AgentToolGateway

from .agent_graph import build_coverage_orchestrator
from .production_context import build_coverage_context
from .runtime import (
    MODEL_NAME,
    build_execution_trace,
    configure_vertex_ai,
    mark_runtime_error,
    mark_runtime_success,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "COVERAGE_AGENT"


class CoverageAgentToolSchema(BaseModel):
    scene_id: str
    missing_shot_ids: list[str] = Field(min_length=1)
    severity: Severity
    description: str = Field(min_length=8, max_length=1000)


class _CoverageToolContext:
    def __init__(
        self,
        *,
        store: LocalStateStore,
        gateway: AgentToolGateway,
        event: ProductionEvent,
        execution_id: str,
        factual_missing_ids: set[str],
    ) -> None:
        self.store = store
        self.gateway = gateway
        self.event = event
        self.execution_id = execution_id
        self.factual_missing_ids = factual_missing_ids
        self.created_alert_ids: list[str] = []
        self.tool_calls: list[ToolCall] = []


def _make_coverage_tool(ctx: _CoverageToolContext):
    async def create_coverage_alert(
        scene_id: str,
        missing_shot_ids: list[str],
        severity: str,
        description: str,
    ) -> dict[str, Any]:
        """Create one coverage alert using exactly the supplied factual missing shot IDs."""
        called_at = datetime.utcnow()
        safe_args = {"sceneId": scene_id, "missingShotIds": missing_shot_ids}
        try:
            parsed = CoverageAgentToolSchema(
                scene_id=scene_id,
                missing_shot_ids=missing_shot_ids,
                severity=severity,
                description=description,
            )
            if ctx.created_alert_ids:
                raise ValueError("Coverage Agent may create only one alert")
            if parsed.scene_id != ctx.event.payload.get("sceneId"):
                raise ValueError("Coverage alert scene does not match event scene")
            if set(parsed.missing_shot_ids) != ctx.factual_missing_ids:
                raise ValueError("Coverage Agent output does not match factual missing shots")
            day = ctx.store.get_active_shoot_day()
            if day is None:
                raise ValueError("No active shoot day")
            alert = await ctx.gateway.create_coverage_alert(
                CreateCoverageAlertInput(
                    sceneId=parsed.scene_id,
                    missingShotIds=parsed.missing_shot_ids,
                    severity=parsed.severity,
                    description=f"[INFERENCE] {parsed.description}",
                ),
                caller_id=AGENT_NAME,
                correlation_id=ctx.event.correlationId,
                shoot_day_id=day.shootDayId,
            )
            ctx.created_alert_ids.append(alert.alertId)
            result = {"alertId": alert.alertId, "status": alert.status.value}
            ctx.tool_calls.append(
                ToolCall(
                    toolName="create_coverage_alert",
                    callerType=OriginType.AGENT,
                    callerId=AGENT_NAME,
                    arguments=safe_args,
                    result=result,
                    status="OK",
                    calledAt=called_at,
                    completedAt=datetime.utcnow(),
                )
            )
            return result
        except Exception as exc:
            ctx.tool_calls.append(
                ToolCall(
                    toolName="create_coverage_alert",
                    callerType=OriginType.AGENT,
                    callerId=AGENT_NAME,
                    arguments=safe_args,
                    result={"errorCode": type(exc).__name__},
                    status="ERROR",
                    calledAt=called_at,
                    completedAt=datetime.utcnow(),
                )
            )
            raise

    return create_coverage_alert


class RealCoverageAgent(BaseAgent):
    mode: AgentMode = AgentMode.PRODUCTION

    def __init__(self, store: LocalStateStore, gateway: AgentToolGateway) -> None:
        self._store = store
        self._gateway = gateway
        configure_vertex_ai()

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        if event.type != EventType.SHOT_COMPLETED:
            return
        scene_id = event.payload.get("sceneId")
        if not scene_id:
            return
        stats = self._store.compute_coverage(scene_id)
        if not stats.missingShotIds:
            for alert in self._store.coverage_alerts.values():
                if alert.sceneId == scene_id and alert.status == AlertStatus.OPEN:
                    self._store.upsert_coverage_alert(
                        alert.model_copy(update={"status": AlertStatus.RESOLVED})
                    )
            return

        started_at = datetime.utcnow()
        execution_id = str(uuid.uuid4())
        context = self._context_json(scene_id)
        ctx = _CoverageToolContext(
            store=self._store,
            gateway=self._gateway,
            event=event,
            execution_id=execution_id,
            factual_missing_ids=set(stats.missingShotIds),
        )
        status = "ERROR"
        error_code: str | None = None
        try:
            await self._run_adk(ctx, context)
            if len(ctx.created_alert_ids) != 1:
                raise ValueError("Expected exactly one validated coverage alert")
            status = "SUCCESS"
        except Exception as exc:
            error_code = type(exc).__name__
            logger.error("coverage_agent_execution_failed", extra={"errorCode": error_code})

        completed_at = datetime.utcnow()
        trace = build_execution_trace(
            execution_id=execution_id,
            agent_name=AGENT_NAME,
            model_name=MODEL_NAME,
            event_id=event.eventId,
            correlation_id=event.correlationId,
            started_at=started_at,
            completed_at=completed_at,
            tool_calls=ctx.tool_calls,
            status=status,
            error_code=error_code,
            evidence_references=ctx.created_alert_ids,
            short_rationale=(
                f"Compared planned and completed shots for {scene_id}; "
                f"missing={len(stats.missingShotIds)}; alerts={len(ctx.created_alert_ids)}."
            ),
        )
        try:
            await self._gateway.record_agent_execution(
                trace,
                caller_id=AGENT_NAME,
                correlation_id=event.correlationId,
            )
        except Exception as exc:
            mark_runtime_error(type(exc).__name__)
            return
        if status == "SUCCESS":
            mark_runtime_success(execution_id, MODEL_NAME)
        else:
            mark_runtime_error(error_code or "AGENT_EXECUTION_ERROR")

    def _context_json(self, scene_id: str) -> str:
        return json.dumps(build_coverage_context(self._store, scene_id), ensure_ascii=False)

    async def _run_adk(self, ctx: _CoverageToolContext, context_json: str) -> None:
        root_agent = build_coverage_orchestrator(_make_coverage_tool(ctx))
        async with InMemoryRunner(agent=root_agent, app_name="studiogrid_ai") as runner:
            session = await runner.session_service.create_session(
                app_name="studiogrid_ai", user_id="production-runtime"
            )
            async for adk_event in runner.run_async(
                user_id="production-runtime",
                session_id=session.id,
                new_message=Content(
                    role="user",
                    parts=[Part(text="Handle this typed SHOT_COMPLETED event.\n\n" + context_json)],
                ),
            ):
                logger.debug(
                    "adk_coverage_event",
                    extra={"eventType": type(adk_event).__name__, "executionId": ctx.execution_id},
                )

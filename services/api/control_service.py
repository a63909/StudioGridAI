"""Private cloud demo control plane for the synthetic LAST LIGHT production."""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.google_adk.production_context import build_schedule_context
from agents.google_adk.remote_client import (
    RemoteAgentEngineClient,
    RemoteAgentEngineError,
    RemoteInvocation,
)
from agents.google_adk.runtime import MODEL_NAME, mark_runtime_error, mark_runtime_success

from .config import settings
from .core.tool_registry import ToolRegistry
from .db.firestore_store import FirestoreStateStore
from .db.local_store import LocalStateStore
from .domain.enums import EventType, OriginType, ProposalStatus, ShootDayStatus, ShotStatus
from .domain.events import ProductionEvent
from .domain.models import AgentExecution, CoverageAlert, ScheduleProposal

logger = logging.getLogger(__name__)

DEMO_ACTORS = {
    "ACT_02": {"name": "Maya Reed", "delayMinutes": 45, "reason": "synthetic traffic delay"},
    "ACT_03": {"name": "Daniel Osei", "delayMinutes": 30, "reason": "synthetic unit transport delay"},
}
DEMO_COVERAGE_SCENE_ID = "SC_05"
DEMO_COVERAGE_COMPLETED_SHOT_ID = "SH_11"
DEMO_HUMAN_ID = "hackathon_demo_human"


class ControlPlaneError(RuntimeError):
    """Safe application error returned without infrastructure details."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.message = message
        self.status_code = status_code


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


class DemoControlService:
    """Serializes trusted demo operations over canonical Firestore state."""

    def __init__(
        self,
        *,
        store: LocalStateStore,
        registry: ToolRegistry,
        persistence: FirestoreStateStore,
        remote: RemoteAgentEngineClient | None = None,
        package_path: Path | None = None,
    ) -> None:
        if persistence.production_id != FirestoreStateStore.DEMO_PRODUCTION_ID:
            raise ValueError("Control API is restricted to last-light-demo")
        self.store = store
        self.registry = registry
        self.persistence = persistence
        self.remote = remote or RemoteAgentEngineClient()
        self.package_path = package_path or (
            Path(__file__).parent.parent.parent
            / "demo"
            / "last_light"
            / "production_package.json"
        )
        self._mutation_lock = asyncio.Lock()
        self._agent_health: tuple[float, str] | None = None

    async def _sync_state(self) -> None:
        durable = await self.persistence.get_application_state()
        if durable is None:
            raise ControlPlaneError(
                "DEMO_STATE_MISSING",
                "The LAST LIGHT demo state is not available.",
                503,
            )
        self.store.restore_application_state(durable)

    def _day(self):
        day = self.store.get_active_shoot_day()
        if day is None or self.store.production is None:
            raise ControlPlaneError("DEMO_STATE_INVALID", "No active shooting day.", 503)
        return day

    def _schedule(self) -> list[dict[str, Any]]:
        day = self._day()
        return [
            {
                "position": item.position,
                "sceneId": item.sceneId,
                "title": self.store.scenes[item.sceneId].title,
                "plannedStartTime": item.plannedStartTime,
                "estimatedDurationMinutes": item.estimatedDurationMinutes,
            }
            for item in day.scheduledScenes
        ]

    async def _ensure_session(self, demo_session_id: str) -> dict[str, Any]:
        session = await self.persistence.get_demo_session(demo_session_id)
        if session is not None:
            return session
        initial = {
            "status": "READY",
            "correlationIds": [],
            "activeProposalId": None,
            "activeCoverageAlertId": None,
            "beforeSchedule": self._schedule(),
            "afterSchedule": None,
            "runtime": {
                "agentEngine": "NOT_CHECKED",
                "gemini": "NOT_CHECKED",
                "privateToolServer": "NOT_CHECKED",
                "firestore": "CONNECTED",
            },
        }
        await self.persistence.save_demo_session(demo_session_id, initial, merge=False)
        return (await self.persistence.get_demo_session(demo_session_id)) or initial

    async def _agent_engine_health(self) -> str:
        now = time.monotonic()
        if self._agent_health and now - self._agent_health[0] < 30:
            return self._agent_health[1]
        try:
            await self.remote.healthcheck()
            status = "CONNECTED"
        except RemoteAgentEngineError:
            status = "ERROR"
        self._agent_health = (now, status)
        return status

    async def health(self) -> dict[str, Any]:
        firestore_status = "ERROR"
        try:
            await self.persistence.healthcheck()
            firestore_status = "CONNECTED"
        except Exception:
            pass
        return {
            "status": "ok" if firestore_status == "CONNECTED" else "degraded",
            "service": "studiogrid-control-api",
            "productionNamespace": FirestoreStateStore.DEMO_PRODUCTION_ID,
            "agentEngine": await self._agent_engine_health(),
            "firestore": firestore_status,
        }

    async def reset(self, demo_session_id: str) -> dict[str, Any]:
        """Reset only canonical synthetic state; never delete evidence documents."""
        async with self._mutation_lock:
            if not self.package_path.exists():
                raise ControlPlaneError("DEMO_PACKAGE_MISSING", "Demo package missing.", 503)
            seed = LocalStateStore()
            seed.load_from_production_package(
                json.loads(self.package_path.read_text(encoding="utf-8"))
            )
            # The deterministic judge journey starts after the establishing scene.
            # This preserves real dependency checks while guaranteeing viable,
            # actor-independent alternatives for both golden delay actions.
            for shot_id, shot in list(seed.shots.items()):
                if shot.sceneId == "SC_01":
                    seed.shots[shot_id] = shot.model_copy(
                        update={"status": ShotStatus.COMPLETE}
                    )
            day = seed.get_active_shoot_day()
            if day is None or seed.production is None:
                raise ControlPlaneError("DEMO_PACKAGE_INVALID", "Demo package invalid.", 503)
            active_day = day.model_copy(update={"status": ShootDayStatus.ACTIVE})
            seed.production = seed.production.model_copy(update={"shootDays": [active_day]})
            await self.persistence.save_application_state(seed)
            self.store.restore_application_state(
                (await self.persistence.get_application_state()) or {}
            )
            reset_doc = {
                "status": "RESET",
                "resetAt": datetime.utcnow().isoformat(),
                "correlationIds": [],
                "activeProposalId": None,
                "activeCoverageAlertId": None,
                "lastAgentSessionId": None,
                "lastExecutionId": None,
                "lastCorrelationId": None,
                "fact": None,
                "inference": None,
                "beforeSchedule": self._schedule(),
                "afterSchedule": None,
                "runtime": {
                    "agentEngine": await self._agent_engine_health(),
                    "gemini": "NOT_CHECKED",
                    "privateToolServer": "NOT_CHECKED",
                    "firestore": "CONNECTED",
                },
            }
            await self.persistence.save_demo_session(
                demo_session_id,
                reset_doc,
                merge=False,
            )
        return await self.get_state(demo_session_id)

    def _event_for(self, event_type: EventType, correlation_id: str) -> ProductionEvent:
        for event in reversed(self.store.events):
            if event.type == event_type and event.correlationId == correlation_id:
                return event
        raise ControlPlaneError("AUDIT_EVENT_MISSING", "Durable fact event missing.", 500)

    async def _persist_plain_event(self, event: ProductionEvent) -> None:
        self.store.add_event(event)
        await self.persistence.save_event(event)

    async def _load_trace(self, execution_id: str) -> AgentExecution:
        for attempt in range(6):
            raw = await self.persistence.get_agent_execution(execution_id)
            if raw is not None:
                return AgentExecution.model_validate(raw)
            if attempt < 5:
                await asyncio.sleep(0.25)
        raise ControlPlaneError(
            "REMOTE_TRACE_MISSING",
            "The agent completed without durable execution evidence.",
            502,
        )

    async def _load_proposal(self, proposal_id: str) -> ScheduleProposal:
        raw = await self.persistence.get_proposal(proposal_id)
        if raw is None:
            raise ControlPlaneError(
                "REMOTE_PROPOSAL_MISSING",
                "The agent completed without a durable proposal.",
                502,
            )
        return ScheduleProposal.model_validate(raw)

    async def _load_coverage_alert(self, alert_id: str) -> CoverageAlert:
        raw = await self.persistence.get_coverage_alert(alert_id)
        if raw is None:
            raise ControlPlaneError(
                "REMOTE_COVERAGE_MISSING",
                "The agent completed without a durable coverage alert.",
                502,
            )
        return CoverageAlert.model_validate(raw)

    def _runtime_from_trace(self, trace: AgentExecution) -> dict[str, str]:
        tool_connected = any(call.status == "OK" for call in trace.toolCalls)
        success = trace.status == "SUCCESS"
        return {
            "agentEngine": "CONNECTED" if success else "ERROR",
            "gemini": (
                "CONNECTED" if success and trace.modelName == MODEL_NAME else "ERROR"
            ),
            "privateToolServer": (
                "CONNECTED" if success and tool_connected else "ERROR"
            ),
            "firestore": "CONNECTED",
        }

    def _safe_trace(self, trace: AgentExecution, session_id: str) -> dict[str, Any]:
        return {
            "provider": "Google Vertex AI Agent Engine",
            "agentName": trace.agentName,
            "modelName": trace.modelName,
            "executionId": trace.executionId,
            "sessionId": session_id,
            "correlationId": trace.correlationId,
            "durationMs": trace.durationMs,
            "status": trace.status,
            "toolNames": [call.toolName for call in trace.toolCalls],
            "evidenceReferences": trace.evidenceReferences,
            "shortRationale": trace.shortRationale,
        }

    async def simulate_actor_delay(
        self,
        demo_session_id: str,
        actor_id: str,
        delay_minutes: int,
    ) -> dict[str, Any]:
        actor_demo = DEMO_ACTORS.get(actor_id)
        if actor_demo is None or actor_demo["delayMinutes"] != delay_minutes:
            raise ControlPlaneError(
                "OPERATION_NOT_ALLOWED",
                "Only predefined LAST LIGHT actor-delay scenarios are allowed.",
            )
        async with self._mutation_lock:
            await self._sync_state()
            session = await self._ensure_session(demo_session_id)
            active_id = session.get("activeProposalId")
            if active_id:
                active = await self.persistence.get_proposal(str(active_id))
                if active and active.get("status") == ProposalStatus.PENDING.value:
                    raise ControlPlaneError(
                        "PENDING_DECISION_REQUIRED",
                        "Approve, reject, or reset the current proposal first.",
                        409,
                    )
            before = self._schedule()
            day = self._day()
            correlation_id = f"demo-{demo_session_id[:12]}-{uuid.uuid4()}"
            await self.registry.report_actor_delay(
                actor_id=actor_id,
                delay_minutes=delay_minutes,
                reason=str(actor_demo["reason"]),
                shoot_day_id=day.shootDayId,
                caller_type=OriginType.HUMAN,
                caller_id=DEMO_HUMAN_ID,
                correlation_id=correlation_id,
            )
            fact_event = self._event_for(EventType.ACTOR_DELAYED, correlation_id)
            schedule_context = build_schedule_context(self.store, fact_event)
            inference = {
                "classification": "INFERENCE",
                "messageCode": "ACTOR_SCENES_BLOCKED",
                "blockedSceneIds": schedule_context["blockedSceneIds"],
                "eligibleSceneIds": [
                    item["sceneId"] for item in schedule_context["eligibleScenes"]
                ],
                "correlationId": correlation_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
            correlations = list(dict.fromkeys([
                *session.get("correlationIds", []),
                correlation_id,
            ]))
            try:
                invocation = await self.remote.invoke_schedule(
                    self.store,
                    fact_event,
                    demo_session_id,
                )
                if (
                    not invocation.tool_attempted
                    or not invocation.proposal_created
                    or invocation.last_error_code
                ):
                    raise RemoteAgentEngineError(
                        invocation.last_error_code or "AGENT_PROPOSAL_NOT_CREATED"
                    )
                proposal_id = str(invocation.last_result.get("proposalId") or "")
                proposal = await self._load_proposal(proposal_id)
                trace = await self._load_trace(invocation.execution_id)
                if (
                    proposal.status != ProposalStatus.PENDING
                    or proposal.correlationId != correlation_id
                    or proposal.agentExecutionId != trace.executionId
                    or trace.status != "SUCCESS"
                ):
                    raise ControlPlaneError(
                        "REMOTE_EVIDENCE_MISMATCH",
                        "Remote proposal evidence did not match this demo action.",
                        502,
                    )
                self.store.upsert_proposal(proposal)
                runtime = self._runtime_from_trace(trace)
                mark_runtime_success(trace.executionId, trace.modelName or MODEL_NAME)
                await self.persistence.save_demo_session(
                    demo_session_id,
                    {
                        "status": "PROPOSAL_PENDING",
                        "correlationIds": correlations,
                        "activeProposalId": proposal.proposalId,
                        "beforeSchedule": before,
                        "afterSchedule": None,
                        "fact": fact_event.model_dump(mode="json"),
                        "inference": inference,
                        "lastAgentSessionId": invocation.session_id,
                        "lastExecutionId": trace.executionId,
                        "lastCorrelationId": correlation_id,
                        "runtime": runtime,
                        "technicalEvidence": self._safe_trace(trace, invocation.session_id),
                    },
                )
            except ControlPlaneError:
                raise
            except RemoteAgentEngineError as exc:
                mark_runtime_error(exc.code)
                await self.persistence.save_demo_session(
                    demo_session_id,
                    {
                        "status": "AGENT_ERROR",
                        "correlationIds": correlations,
                        "beforeSchedule": before,
                        "fact": fact_event.model_dump(mode="json"),
                        "inference": inference,
                        "lastCorrelationId": correlation_id,
                        "lastErrorCode": exc.code,
                        "runtime": {
                            "agentEngine": "ERROR",
                            "gemini": "ERROR",
                            "privateToolServer": "NOT_CHECKED",
                            "firestore": "CONNECTED",
                        },
                    },
                )
                logger.warning("demo_agent_delay_failed", extra={"errorCode": exc.code})
                raise ControlPlaneError(
                    "AGENT_ENGINE_ERROR",
                    "The cloud agent could not create a verified proposal. State was preserved.",
                    502,
                ) from exc
        return await self.get_state(demo_session_id)

    async def approve(
        self,
        demo_session_id: str,
        proposal_id: str,
    ) -> dict[str, Any]:
        return await self._decide(demo_session_id, proposal_id, approve=True)

    async def reject(
        self,
        demo_session_id: str,
        proposal_id: str,
    ) -> dict[str, Any]:
        return await self._decide(demo_session_id, proposal_id, approve=False)

    async def _decide(
        self,
        demo_session_id: str,
        proposal_id: str,
        *,
        approve: bool,
    ) -> dict[str, Any]:
        async with self._mutation_lock:
            await self._sync_state()
            session = await self._ensure_session(demo_session_id)
            if session.get("activeProposalId") != proposal_id:
                raise ControlPlaneError(
                    "PROPOSAL_NOT_OWNED_BY_SESSION",
                    "This proposal is not the active proposal for this demo session.",
                    403,
                )
            proposal = await self._load_proposal(proposal_id)
            if proposal.status != ProposalStatus.PENDING:
                raise ControlPlaneError(
                    "PROPOSAL_NOT_PENDING",
                    "The proposal no longer requires a decision.",
                    409,
                )
            self.store.upsert_proposal(proposal)
            day = self._day()
            correlation_id = str(proposal.correlationId or session.get("lastCorrelationId"))
            durable_before = await self.persistence.get_application_state()
            try:
                if approve:
                    await self.registry.approve_schedule_proposal(
                        proposal_id=proposal_id,
                        approved_by=DEMO_HUMAN_ID,
                        shoot_day_id=day.shootDayId,
                        caller_type=OriginType.HUMAN,
                        caller_id=DEMO_HUMAN_ID,
                        correlation_id=correlation_id,
                    )
                    status = "APPROVED_BY_HUMAN"
                    after = self._schedule()
                else:
                    await self.registry.reject_schedule_proposal(
                        proposal_id=proposal_id,
                        rejected_by=DEMO_HUMAN_ID,
                        reason="Rejected by the hackathon demo human operator",
                        shoot_day_id=day.shootDayId,
                        caller_type=OriginType.HUMAN,
                        caller_id=DEMO_HUMAN_ID,
                        correlation_id=correlation_id,
                    )
                    status = "REJECTED_BY_HUMAN"
                    after = None
            except Exception as exc:
                if durable_before is not None:
                    self.store.restore_application_state(durable_before)
                    try:
                        await self.persistence.save_application_state(self.store)
                    except Exception:
                        logger.error("demo_decision_rollback_failed")
                raise ControlPlaneError(
                    "HUMAN_DECISION_FAILED",
                    "The human decision was not applied; the proposal remains pending.",
                    502,
                ) from exc
            await self.persistence.save_demo_session(
                demo_session_id,
                {
                    "status": status,
                    "afterSchedule": after,
                    "humanDecision": {
                        "classification": "HUMAN_DECISION",
                        "decision": "APPROVED" if approve else "REJECTED",
                        "actorType": "HUMAN",
                        "actorId": DEMO_HUMAN_ID,
                        "proposalId": proposal_id,
                        "correlationId": correlation_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                },
            )
        return await self.get_state(demo_session_id)

    async def check_coverage(self, demo_session_id: str) -> dict[str, Any]:
        async with self._mutation_lock:
            await self._sync_state()
            session = await self._ensure_session(demo_session_id)
            day = self._day()
            correlation_id = f"demo-{demo_session_id[:12]}-{uuid.uuid4()}"
            shot = self.store.shots[DEMO_COVERAGE_COMPLETED_SHOT_ID]
            if shot.status == ShotStatus.PLANNED:
                await self.registry.record_shot_started(
                    shot_id=shot.shotId,
                    caller_type=OriginType.HUMAN,
                    caller_id=DEMO_HUMAN_ID,
                    correlation_id=correlation_id,
                )
                await self.registry.record_shot_completed(
                    shot_id=shot.shotId,
                    caller_type=OriginType.HUMAN,
                    caller_id=DEMO_HUMAN_ID,
                    correlation_id=correlation_id,
                )
            elif shot.status == ShotStatus.IN_PROGRESS:
                await self.registry.record_shot_completed(
                    shot_id=shot.shotId,
                    caller_type=OriginType.HUMAN,
                    caller_id=DEMO_HUMAN_ID,
                    correlation_id=correlation_id,
                )
            elif shot.status == ShotStatus.COMPLETE:
                event = ProductionEvent(
                    productionId=self.store.production.productionId,
                    shootDayId=day.shootDayId,
                    originType=OriginType.HUMAN,
                    originId=DEMO_HUMAN_ID,
                    type=EventType.SHOT_COMPLETED,
                    payload={
                        "shotId": shot.shotId,
                        "sceneId": DEMO_COVERAGE_SCENE_ID,
                        "alreadyComplete": True,
                    },
                    source=DEMO_HUMAN_ID,
                    correlationId=correlation_id,
                )
                await self._persist_plain_event(event)
            else:
                raise ControlPlaneError(
                    "COVERAGE_SCENARIO_UNAVAILABLE",
                    "The fixed coverage scenario is not in a valid state.",
                    409,
                )
            fact_event = self._event_for(EventType.SHOT_COMPLETED, correlation_id)
            coverage = self.store.compute_coverage(DEMO_COVERAGE_SCENE_ID)
            correlations = list(dict.fromkeys([
                *session.get("correlationIds", []),
                correlation_id,
            ]))
            invocation: RemoteInvocation | None = None
            try:
                for _ in range(3):
                    invocation = await self.remote.invoke_coverage(
                        self.store,
                        fact_event,
                        demo_session_id,
                    )
                    if invocation.tool_attempted:
                        break
                if (
                    invocation is None
                    or not invocation.tool_attempted
                    or not invocation.alert_created
                    or invocation.last_error_code
                ):
                    raise RemoteAgentEngineError(
                        invocation.last_error_code
                        if invocation and invocation.last_error_code
                        else "AGENT_COVERAGE_NOT_CREATED"
                    )
                alert_id = str(invocation.last_result.get("alertId") or "")
                alert = await self._load_coverage_alert(alert_id)
                trace = await self._load_trace(invocation.execution_id)
                if (
                    alert.sceneId != DEMO_COVERAGE_SCENE_ID
                    or set(alert.missingShotIds) != set(coverage.missingShotIds)
                    or trace.status != "SUCCESS"
                ):
                    raise ControlPlaneError(
                        "REMOTE_EVIDENCE_MISMATCH",
                        "Remote coverage evidence did not match factual shot state.",
                        502,
                    )
                self.store.upsert_coverage_alert(alert)
                runtime = self._runtime_from_trace(trace)
                mark_runtime_success(trace.executionId, trace.modelName or MODEL_NAME)
                await self.persistence.save_demo_session(
                    demo_session_id,
                    {
                        "status": "COVERAGE_READY",
                        "correlationIds": correlations,
                        "activeCoverageAlertId": alert.alertId,
                        "coverageFact": {
                            **coverage.model_dump(mode="json"),
                            "classification": "FACT",
                            "completedShotId": DEMO_COVERAGE_COMPLETED_SHOT_ID,
                        },
                        "lastAgentSessionId": invocation.session_id,
                        "lastExecutionId": trace.executionId,
                        "lastCorrelationId": correlation_id,
                        "runtime": runtime,
                        "technicalEvidence": self._safe_trace(trace, invocation.session_id),
                    },
                )
            except ControlPlaneError:
                raise
            except RemoteAgentEngineError as exc:
                mark_runtime_error(exc.code)
                await self.persistence.save_demo_session(
                    demo_session_id,
                    {
                        "status": "AGENT_ERROR",
                        "correlationIds": correlations,
                        "coverageFact": {
                            **coverage.model_dump(mode="json"),
                            "classification": "FACT",
                        },
                        "lastErrorCode": exc.code,
                        "runtime": {
                            "agentEngine": "ERROR",
                            "gemini": "ERROR",
                            "privateToolServer": "NOT_CHECKED",
                            "firestore": "CONNECTED",
                        },
                    },
                )
                raise ControlPlaneError(
                    "AGENT_ENGINE_ERROR",
                    "The cloud coverage agent did not produce verified evidence.",
                    502,
                ) from exc
        return await self.get_state(demo_session_id)

    async def _timeline(self, session: dict[str, Any]) -> list[dict[str, Any]]:
        correlations = set(str(item) for item in session.get("correlationIds", []))
        events = await self.persistence.list_events(limit=200)
        classification = {
            EventType.ACTOR_DELAYED.value: "FACT",
            EventType.SHOT_STARTED.value: "FACT",
            EventType.SHOT_COMPLETED.value: "FACT",
            EventType.SCHEDULE_PROPOSAL_CREATED.value: "RECOMMENDATION",
            EventType.SCHEDULE_PROPOSAL_APPROVED.value: "HUMAN_DECISION",
            EventType.SCHEDULE_PROPOSAL_REJECTED.value: "HUMAN_DECISION",
            EventType.COVERAGE_ALERT_CREATED.value: "INFERENCE",
        }
        safe_events = []
        for event in events:
            if str(event.get("correlationId")) not in correlations:
                continue
            event_type = str(event.get("type"))
            if event_type not in classification:
                continue
            safe_events.append(
                {
                    "eventId": str(event.get("eventId")),
                    "type": event_type,
                    "classification": classification[event_type],
                    "timestamp": _jsonable(event.get("timestamp")),
                    "originType": str(event.get("originType")),
                    "originId": str(event.get("originId")),
                    "correlationId": str(event.get("correlationId")),
                    "payload": _jsonable(event.get("payload") or {}),
                }
            )
        inference = session.get("inference")
        if isinstance(inference, dict):
            safe_events.append(
                {
                    "eventId": f"inference-{inference.get('correlationId')}",
                    "type": "ACTOR_SCENES_BLOCKED",
                    "classification": "INFERENCE",
                    "timestamp": inference.get("timestamp"),
                    "originType": "SYSTEM",
                    "originId": "studiogrid-control-api",
                    "correlationId": inference.get("correlationId"),
                    "payload": {
                        "blockedSceneIds": inference.get("blockedSceneIds", []),
                        "eligibleSceneIds": inference.get("eligibleSceneIds", []),
                    },
                }
            )
        safe_events.sort(key=lambda item: str(item.get("timestamp") or ""))
        return safe_events

    def _schedule_comparison(
        self,
        schedule: list[dict[str, Any]] | None,
        other: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]] | None:
        if schedule is None:
            return None
        other_positions = {
            str(item.get("sceneId")): item.get("position") for item in (other or [])
        }
        return [
            {
                **item,
                "changed": other_positions.get(str(item.get("sceneId"))) != item.get("position"),
            }
            for item in schedule
        ]

    async def get_state(self, demo_session_id: str) -> dict[str, Any]:
        await self._sync_state()
        session = await self._ensure_session(demo_session_id)
        day = self._day()
        proposal = None
        proposal_id = session.get("activeProposalId")
        if proposal_id:
            raw = await self.persistence.get_proposal(str(proposal_id))
            if raw:
                proposal = ScheduleProposal.model_validate(raw).model_dump(mode="json")
        coverage_alert = None
        alert_id = session.get("activeCoverageAlertId")
        if alert_id:
            raw_alert = await self.persistence.get_coverage_alert(str(alert_id))
            if raw_alert:
                coverage_alert = CoverageAlert.model_validate(raw_alert).model_dump(mode="json")
        current = self._schedule()
        before = _jsonable(session.get("beforeSchedule"))
        after = _jsonable(session.get("afterSchedule"))
        runtime = dict(session.get("runtime") or {})
        runtime["agentEngine"] = (
            runtime.get("agentEngine")
            if runtime.get("agentEngine") == "ERROR"
            else await self._agent_engine_health()
        )
        try:
            await self.persistence.healthcheck()
            runtime["firestore"] = "CONNECTED"
        except Exception:
            runtime["firestore"] = "ERROR"
        completed_shots = sum(
            1 for shot in self.store.shots.values() if shot.status == ShotStatus.COMPLETE
        )
        return {
            "demoSessionId": demo_session_id,
            "sessionStatus": session.get("status", "READY"),
            "production": {
                "title": self.store.production.title,
                "status": self.store.production.status.value,
                "sceneCount": len(self.store.scenes),
                "shotCount": len(self.store.shots),
                "completedShotCount": completed_shots,
                "actorCount": len(self.store.actors),
                "shootDayId": day.shootDayId,
                "shootDayStatus": day.status.value,
            },
            "actors": [
                {
                    **actor.model_dump(mode="json"),
                    "demoEnabled": actor.actorId in DEMO_ACTORS,
                    "defaultDelayMinutes": DEMO_ACTORS.get(actor.actorId, {}).get("delayMinutes"),
                }
                for actor in self.store.actors.values()
            ],
            "schedule": {
                "current": self._schedule_comparison(current, before),
                "before": self._schedule_comparison(before, after or current),
                "after": self._schedule_comparison(after, before),
            },
            "proposal": proposal,
            "coverage": {
                "fact": _jsonable(session.get("coverageFact")),
                "alert": coverage_alert,
            },
            "timeline": await self._timeline(session),
            "runtime": runtime,
            "technicalEvidence": _jsonable(session.get("technicalEvidence")),
            "lastErrorCode": session.get("lastErrorCode"),
            "humanDecision": _jsonable(session.get("humanDecision")),
        }

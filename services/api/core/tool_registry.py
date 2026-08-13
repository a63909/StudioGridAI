"""Tool Registry for StudioGrid AI.

Central registry that executes typed tool calls with:
  - Authorization check (who can call this tool)
  - Approval gate check (human-only operations)
  - Schema validation (Pydantic)
  - State mutation
  - Audit event emission
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..domain.enums import AlertStatus, EventType, OriginType, ProposalStatus, ShotStatus
from ..domain.events import ProductionEvent
from ..domain.models import (
    Actor,
    AgentExecution,
    ContinuityAlert,
    ContinuityFact,
    CoverageAlert,
    Evidence,
    Location,
    Risk,
    ScheduleChange,
    ScheduleProposal,
    Shot,
    ToolCall,
    WrapReport,
)
from ..tools.contracts import TOOL_REGISTRY_META
from .approval_gates import ApprovalGate, ApprovalRequiredError
from .event_bus import LocalEventBus

logger = logging.getLogger(__name__)


class ToolAuthorizationError(Exception):
    def __init__(self, tool_name: str, caller_type: OriginType) -> None:
        self.tool_name = tool_name
        self.caller_type = caller_type
        super().__init__(
            f"Caller type '{caller_type}' is not authorized to call tool '{tool_name}'."
        )


class ToolNotFoundError(Exception):
    def __init__(self, tool_name: str) -> None:
        super().__init__(f"Tool '{tool_name}' not found in registry.")


class ToolRegistry:
    """Executes tool calls with full authorization, approval, and audit chain."""

    def __init__(self, store: Any, event_bus: LocalEventBus, persistence: Any | None = None) -> None:
        self._store = store
        self._event_bus = event_bus
        self._persistence = persistence

    async def _record_event(self, event: ProductionEvent) -> None:
        self._store.add_event(event)
        if self._persistence is not None:
            await self._persistence.save_event(event)
        await self._event_bus.publish(event)

    async def _persist_state(self) -> None:
        if self._persistence is not None:
            await self._persistence.save_application_state(self._store)

    async def _persist_proposal(self, proposal: ScheduleProposal) -> None:
        if self._persistence is not None:
            await self._persistence.save_proposal(proposal)

    def _authorize(self, tool_name: str, caller_type: OriginType) -> None:
        """Check that the caller is allowed to use this tool."""
        meta = TOOL_REGISTRY_META.get(tool_name)
        if meta is None:
            raise ToolNotFoundError(tool_name)
        if caller_type not in meta.allowed_callers:
            raise ToolAuthorizationError(tool_name, caller_type)

    async def _audit(
        self,
        tool_name: str,
        caller_type: OriginType,
        caller_id: str,
        arguments: dict[str, Any],
        result: dict[str, Any] | None,
        status: str,
        correlation_id: str,
    ) -> None:
        """Emit a TOOL_CALLED audit event."""
        if self._store.production is None:
            return
        day = self._store.get_active_shoot_day()
        event = ProductionEvent(
            productionId=self._store.production.productionId,
            shootDayId=day.shootDayId if day else "UNKNOWN",
            originType=caller_type,
            originId=caller_id,
            type=EventType.TOOL_CALLED,
            payload={
                "toolName": tool_name,
                "arguments": arguments,
                "result": result,
                "status": status,
            },
            source="tool_registry",
            correlationId=correlation_id,
        )
        await self._record_event(event)

    # ─────────────────────────────────────────────────────────────────────────
    # Shot tools
    # ─────────────────────────────────────────────────────────────────────────

    async def record_shot_started(
        self,
        shot_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
        started_at: datetime | None = None,
    ) -> Shot:
        tool = "record_shot_started"
        self._authorize(tool, caller_type)
        shot = self._store.shots.get(shot_id)
        if shot is None:
            raise ValueError(f"Shot {shot_id} not found")
        if shot.status != ShotStatus.PLANNED:
            raise ValueError(f"Shot {shot_id} is {shot.status}, expected PLANNED")

        updated = shot.model_copy(update={
            "status": ShotStatus.IN_PROGRESS,
            "startedAt": started_at or datetime.utcnow(),
        })
        self._store.upsert_shot(updated)
        await self._persist_state()

        day = self._store.get_active_shoot_day()
        if day and self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=day.shootDayId,
                originType=caller_type,
                originId=caller_id,
                type=EventType.SHOT_STARTED,
                payload={"shotId": shot_id, "sceneId": shot.sceneId},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"shotId": shot_id}, None, "OK", correlation_id)
        return updated

    async def record_shot_completed(
        self,
        shot_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
        completed_at: datetime | None = None,
        actual_duration_minutes: int | None = None,
    ) -> Shot:
        tool = "record_shot_completed"
        self._authorize(tool, caller_type)
        shot = self._store.shots.get(shot_id)
        if shot is None:
            raise ValueError(f"Shot {shot_id} not found")
        if shot.status != ShotStatus.IN_PROGRESS:
            raise ValueError(f"Shot {shot_id} is {shot.status}, expected IN_PROGRESS")

        updated = shot.model_copy(update={
            "status": ShotStatus.COMPLETE,
            "completedAt": completed_at or datetime.utcnow(),
            "actualDurationMinutes": actual_duration_minutes,
        })
        self._store.upsert_shot(updated)
        await self._persist_state()

        day = self._store.get_active_shoot_day()
        if day and self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=day.shootDayId,
                originType=caller_type,
                originId=caller_id,
                type=EventType.SHOT_COMPLETED,
                payload={"shotId": shot_id, "sceneId": shot.sceneId},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"shotId": shot_id}, None, "OK", correlation_id)
        return updated

    # ─────────────────────────────────────────────────────────────────────────
    # Actor tools
    # ─────────────────────────────────────────────────────────────────────────

    async def report_actor_delay(
        self,
        actor_id: str,
        delay_minutes: int,
        reason: str,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> Actor:
        tool = "report_actor_delay"
        self._authorize(tool, caller_type)
        actor = self._store.actors.get(actor_id)
        if actor is None:
            raise ValueError(f"Actor {actor_id} not found")

        from ..domain.enums import ActorStatus
        updated = actor.model_copy(update={
            "currentStatus": ActorStatus.DELAYED,
            "delayMinutes": delay_minutes,
        })
        self._store.upsert_actor(updated)
        self._store.add_delay_minutes(delay_minutes)
        await self._persist_state()

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.ACTOR_DELAYED,
                payload={
                    "actorId": actor_id,
                    "actorName": actor.name,
                    "delayMinutes": delay_minutes,
                    "reason": reason,
                },
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"actorId": actor_id, "delayMinutes": delay_minutes}, None, "OK", correlation_id)
        return updated

    async def report_actor_available(
        self,
        actor_id: str,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> Actor:
        tool = "report_actor_available"
        self._authorize(tool, caller_type)
        actor = self._store.actors.get(actor_id)
        if actor is None:
            raise ValueError(f"Actor {actor_id} not found")

        from ..domain.enums import ActorStatus
        updated = actor.model_copy(update={
            "currentStatus": ActorStatus.AVAILABLE,
            "delayMinutes": 0,
        })
        self._store.upsert_actor(updated)
        await self._persist_state()

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.ACTOR_AVAILABLE,
                payload={"actorId": actor_id},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"actorId": actor_id}, None, "OK", correlation_id)
        return updated

    # ─────────────────────────────────────────────────────────────────────────
    # Continuity tools
    # ─────────────────────────────────────────────────────────────────────────

    async def record_continuity_fact(
        self,
        fact: ContinuityFact,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> ContinuityFact:
        tool = "record_continuity_fact"
        self._authorize(tool, caller_type)
        self._store.upsert_continuity_fact(fact)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.CONTINUITY_FACT_RECORDED,
                payload=fact.model_dump(),
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"factId": fact.factId}, None, "OK", correlation_id)
        return fact

    async def create_continuity_alert(
        self,
        alert: ContinuityAlert,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> ContinuityAlert:
        tool = "create_continuity_alert"
        self._authorize(tool, caller_type)
        self._store.upsert_continuity_alert(alert)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.CONTINUITY_ALERT_CREATED,
                payload={"alertId": alert.alertId, "severity": alert.severity},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"alertId": alert.alertId}, None, "OK", correlation_id)
        return alert

    # ─────────────────────────────────────────────────────────────────────────
    # Coverage tools
    # ─────────────────────────────────────────────────────────────────────────

    async def create_coverage_alert(
        self,
        alert: CoverageAlert,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> CoverageAlert:
        tool = "create_coverage_alert"
        self._authorize(tool, caller_type)
        if alert.sceneId not in self._store.scenes:
            raise ValueError(f"Scene {alert.sceneId} not found")
        if not alert.missingShotIds:
            raise ValueError("Coverage alert requires at least one missing planned shot")
        invalid_shots = [shot_id for shot_id in alert.missingShotIds if shot_id not in self._store.shots]
        if invalid_shots:
            raise ValueError(f"Unknown shot IDs: {invalid_shots}")
        wrong_scene = [
            shot_id for shot_id in alert.missingShotIds
            if self._store.shots[shot_id].sceneId != alert.sceneId
        ]
        if wrong_scene:
            raise ValueError(f"Shots do not belong to scene {alert.sceneId}: {wrong_scene}")
        completed = [
            shot_id for shot_id in alert.missingShotIds
            if self._store.shots[shot_id].status == ShotStatus.COMPLETE
        ]
        if completed:
            raise ValueError(f"Completed shots cannot be reported missing: {completed}")
        self._store.upsert_coverage_alert(alert)
        if self._persistence is not None:
            await self._persistence.save_coverage_alert(alert)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.COVERAGE_ALERT_CREATED,
                payload={"alertId": alert.alertId, "sceneId": alert.sceneId, "missingShotIds": alert.missingShotIds},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"alertId": alert.alertId}, None, "OK", correlation_id)
        return alert

    # ─────────────────────────────────────────────────────────────────────────
    # Schedule tools
    # ─────────────────────────────────────────────────────────────────────────

    async def create_schedule_proposal(
        self,
        proposal: ScheduleProposal,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> ScheduleProposal:
        tool = "create_schedule_proposal"
        self._authorize(tool, caller_type)
        if caller_type == OriginType.AGENT and proposal.originAgent != caller_id:
            raise ToolAuthorizationError(tool, caller_type)
        if proposal.status != ProposalStatus.PENDING:
            raise ValueError("Agents may only create PENDING schedule proposals")
        unknown_scenes = [
            change.sceneId for change in proposal.proposedChanges
            if change.sceneId not in self._store.scenes
        ]
        if unknown_scenes:
            raise ValueError(f"Unknown proposal scene IDs: {unknown_scenes}")
        self._store.upsert_proposal(proposal)
        await self._persist_proposal(proposal)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.SCHEDULE_PROPOSAL_CREATED,
                payload={"proposalId": proposal.proposalId, "why": proposal.why},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"proposalId": proposal.proposalId}, None, "OK", correlation_id)
        return proposal

    async def approve_schedule_proposal(
        self,
        proposal_id: str,
        approved_by: str,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> ScheduleProposal:
        tool = "approve_schedule_proposal"
        self._authorize(tool, caller_type)
        ApprovalGate.check(tool, caller_type)

        proposal = self._store.proposals.get(proposal_id)
        if proposal is None:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.status != ProposalStatus.PENDING:
            raise ValueError(f"Proposal {proposal_id} is {proposal.status}, expected PENDING")

        updated = proposal.model_copy(update={
            "status": ProposalStatus.APPROVED,
            "resolvedAt": datetime.utcnow(),
            "resolvedBy": approved_by,
        })
        self._store.upsert_proposal(updated)

        # Apply the schedule changes
        self._apply_schedule_changes(proposal, shoot_day_id)
        self._store.add_recovered_minutes(proposal.expectedBenefitMinutes)
        await self._persist_state()
        await self._persist_proposal(updated)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.SCHEDULE_PROPOSAL_APPROVED,
                payload={
                    "proposalId": proposal_id,
                    "approvedBy": approved_by,
                    "expectedBenefitMinutes": proposal.expectedBenefitMinutes,
                },
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"proposalId": proposal_id, "approvedBy": approved_by}, None, "OK", correlation_id)
        return updated

    async def reject_schedule_proposal(
        self,
        proposal_id: str,
        rejected_by: str,
        reason: str,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> ScheduleProposal:
        tool = "reject_schedule_proposal"
        self._authorize(tool, caller_type)
        ApprovalGate.check(tool, caller_type)

        proposal = self._store.proposals.get(proposal_id)
        if proposal is None:
            raise ValueError(f"Proposal {proposal_id} not found")

        updated = proposal.model_copy(update={
            "status": ProposalStatus.REJECTED,
            "resolvedAt": datetime.utcnow(),
            "resolvedBy": rejected_by,
        })
        self._store.upsert_proposal(updated)
        await self._persist_proposal(updated)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.SCHEDULE_PROPOSAL_REJECTED,
                payload={"proposalId": proposal_id, "rejectedBy": rejected_by, "reason": reason},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"proposalId": proposal_id}, None, "OK", correlation_id)
        return updated

    def _apply_schedule_changes(self, proposal: ScheduleProposal, shoot_day_id: str) -> None:
        """Apply approved schedule changes to the shoot day order."""
        day = self._store.get_active_shoot_day()
        if day is None:
            return

        current_schedule = list(day.scheduledScenes)
        for change in proposal.proposedChanges:
            if change.changeType == "REORDER" and change.fromPosition is not None and change.toPosition is not None:
                # Find and move the scene
                scene_entry = next(
                    (s for s in current_schedule if s.sceneId == change.sceneId),
                    None
                )
                if scene_entry:
                    current_schedule.remove(scene_entry)
                    current_schedule.insert(change.toPosition - 1, scene_entry)
                    # Renumber positions
                    for i, s in enumerate(current_schedule):
                        current_schedule[i] = s.model_copy(update={"position": i + 1})

        self._store.update_schedule_order(shoot_day_id, current_schedule)

    # ─────────────────────────────────────────────────────────────────────────
    # Safe AI execution trace tool
    # ─────────────────────────────────────────────────────────────────────────

    async def record_agent_execution(
        self,
        execution: AgentExecution,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> AgentExecution:
        tool = "record_agent_execution"
        self._authorize(tool, caller_type)
        if caller_type == OriginType.AGENT and execution.agentName != caller_id:
            raise ToolAuthorizationError(tool, caller_type)
        if execution.correlationId != correlation_id:
            raise ValueError("Execution correlationId does not match tool envelope")

        self._store.upsert_agent_execution(execution)
        if self._persistence is not None:
            await self._persistence.save_agent_execution(execution)

        await self._audit(
            tool,
            caller_type,
            caller_id,
            {"executionId": execution.executionId, "status": execution.status},
            {"stored": True},
            "OK",
            correlation_id,
        )
        return execution

    # ─────────────────────────────────────────────────────────────────────────
    # Risk tools
    # ─────────────────────────────────────────────────────────────────────────

    async def create_risk(
        self,
        risk: Risk,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> Risk:
        tool = "create_risk"
        self._authorize(tool, caller_type)
        self._store.upsert_risk(risk)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.RISK_CREATED,
                payload={"riskId": risk.riskId, "severity": risk.severity, "reason": risk.reason},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"riskId": risk.riskId}, None, "OK", correlation_id)
        return risk

    async def resolve_risk(
        self,
        risk_id: str,
        resolved_by: str,
        resolution: str,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> Risk:
        tool = "resolve_risk"
        self._authorize(tool, caller_type)
        risk = self._store.risks.get(risk_id)
        if risk is None:
            raise ValueError(f"Risk {risk_id} not found")

        # Severity gate check
        ApprovalGate.check(tool, caller_type, severity=risk.severity)

        from ..domain.enums import RiskStatus
        updated = risk.model_copy(update={
            "status": RiskStatus.RESOLVED,
            "resolvedAt": datetime.utcnow(),
            "resolvedBy": resolved_by,
        })
        self._store.upsert_risk(updated)

        if self._store.production:
            event = ProductionEvent(
                productionId=self._store.production.productionId,
                shootDayId=shoot_day_id,
                originType=caller_type,
                originId=caller_id,
                type=EventType.RISK_RESOLVED,
                payload={"riskId": risk_id, "resolvedBy": resolved_by},
                source=caller_id,
                correlationId=correlation_id,
            )
            await self._record_event(event)

        await self._audit(tool, caller_type, caller_id, {"riskId": risk_id}, None, "OK", correlation_id)
        return updated

    # ─────────────────────────────────────────────────────────────────────────
    # Wrap report
    # ─────────────────────────────────────────────────────────────────────────

    async def generate_wrap_report(
        self,
        shoot_day_id: str,
        caller_type: OriginType,
        caller_id: str,
        correlation_id: str,
    ) -> WrapReport:
        """Generate wrap report from actual state — never hardcoded."""
        tool = "generate_wrap_report"
        self._authorize(tool, caller_type)

        stats = self._store.compute_dashboard_stats(shoot_day_id)

        all_shots = list(self._store.shots.values())
        incomplete_shots = [s.shotId for s in all_shots if s.status not in {ShotStatus.COMPLETE, ShotStatus.SKIPPED}]
        incomplete_scenes = [
            sc.sceneId for sc in self._store.scenes.values()
            if self._store.compute_scene_status(sc.sceneId) not in {
                __import__("services.api.domain.enums", fromlist=["SceneStatus"]).SceneStatus.COMPLETE
            }
        ]

        from ..domain.enums import AlertStatus, RiskStatus, SceneStatus
        incomplete_scenes = [
            sc.sceneId for sc in self._store.scenes.values()
            if self._store.compute_scene_status(sc.sceneId) != SceneStatus.COMPLETE
        ]

        open_coverage = [
            a.alertId for a in self._store.coverage_alerts.values()
            if a.status == AlertStatus.OPEN
        ]
        resolved_continuity = [
            a.alertId for a in self._store.continuity_alerts.values()
            if a.status == AlertStatus.RESOLVED
        ]
        open_continuity = [
            a.alertId for a in self._store.continuity_alerts.values()
            if a.status == AlertStatus.OPEN
        ]
        approved_proposals = [
            p.proposalId for p in self._store.proposals.values()
            if p.status == ProposalStatus.APPROVED
        ]
        active_risks = [
            r.riskId for r in self._store.risks.values()
            if r.status in {RiskStatus.ACTIVE, RiskStatus.MONITORING}
        ]
        resolved_risks = [
            r.riskId for r in self._store.risks.values()
            if r.status == RiskStatus.RESOLVED
        ]

        skipped = sum(1 for s in all_shots if s.status == ShotStatus.SKIPPED)
        failed = sum(1 for s in all_shots if s.status == ShotStatus.FAILED)

        report = WrapReport(
            shootDayId=shoot_day_id,
            productionId=self._store.production.productionId if self._store.production else "UNKNOWN",
            plannedShotCount=stats.plannedShotCount,
            completedShotCount=stats.completedShotCount,
            failedShotCount=failed,
            skippedShotCount=skipped,
            plannedSceneCount=stats.plannedSceneCount,
            completedSceneCount=stats.completedSceneCount,
            partialSceneCount=stats.partialSceneCount,
            incompleteShotIds=incomplete_shots,
            incompleteSceneIds=incomplete_scenes,
            openCoverageAlerts=open_coverage,
            resolvedContinuityAlerts=resolved_continuity,
            openContinuityAlerts=open_continuity,
            totalDelayMinutes=stats.totalDelayMinutes,
            approvedScheduleChangeIds=approved_proposals,
            estimatedMinutesRecovered=stats.estimatedMinutesRecovered,
            activeRiskIds=active_risks,
            resolvedRiskIds=resolved_risks,
            nextDayPriorities=[],
        )
        self._store.wrap_report = report
        return report

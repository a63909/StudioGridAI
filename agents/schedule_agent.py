"""Schedule Agent — Phase 1 deterministic implementation.

Handles ACTOR_DELAYED events and creates schedule proposals.
In Phase 2, this logic is replaced by real Gemini inference via Google ADK.
The tool calls and state mutation paths remain identical.
"""
from __future__ import annotations

import logging
import uuid

from services.api.core.event_bus import LocalEventBus
from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import (
    AgentMode,
    EventType,
    OriginType,
    ProposalCategory,
    Severity,
)
from services.api.domain.events import ProductionEvent
from services.api.domain.models import (
    Evidence,
    ProposalRisk,
    ScheduleChange,
    ScheduleProposal,
)
from .interfaces import BaseAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "SCHEDULE_AGENT"


class ScheduleAgent(BaseAgent):
    """Detects scheduling conflicts and creates rescheduling proposals.

    Phase 1: deterministic logic.
    Phase 2: Gemini inference via Google ADK (same interface).
    """

    mode: AgentMode = AgentMode.DEV

    def __init__(self, store: LocalStateStore, registry: ToolRegistry) -> None:
        self._store = store
        self._registry = registry

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        if event.type == EventType.ACTOR_DELAYED:
            await self._handle_actor_delayed(event)

    async def _handle_actor_delayed(self, event: ProductionEvent) -> None:
        actor_id = event.payload.get("actorId")
        delay_minutes = event.payload.get("delayMinutes", 0)

        if not actor_id:
            return

        logger.info(
            "schedule_agent_analyzing_delay",
            extra={"actorId": actor_id, "delayMinutes": delay_minutes, "mode": "DEV"},
        )

        # Find scenes blocked by this actor
        blocked_scenes = self._store.get_scenes_blocked_by_actor(actor_id)
        if not blocked_scenes:
            logger.info("no_scenes_blocked_by_actor", extra={"actorId": actor_id})
            return

        # Find scenes that can be shot without this actor
        alternative_scenes = self._store.get_shootable_scenes_without_actor(actor_id)
        if not alternative_scenes:
            logger.info("no_alternative_scenes_available", extra={"actorId": actor_id})
            return

        # Build proposal for the first viable alternative
        target_scene_id = alternative_scenes[0]
        target_scene = self._store.scenes.get(target_scene_id)
        if target_scene is None:
            return

        # Get the current day's schedule
        day = self._store.get_active_shoot_day()
        if day is None:
            return

        # Find current position of the target scene
        target_pos = next(
            (s.position for s in day.scheduledScenes if s.sceneId == target_scene_id),
            None,
        )
        if target_pos is None:
            return

        # Estimate benefit: delay_minutes minus overhead
        estimated_benefit = max(0, delay_minutes - 8)

        # Build evidence
        actor = self._store.actors.get(actor_id)
        actor_name = actor.name if actor else actor_id
        location = self._store.locations.get(target_scene.locationId)
        location_available = location.status.value == "AVAILABLE" if location else False

        evidence = [
            Evidence(
                evidenceType="ACTOR_STATUS",
                description=f"{actor_name} is delayed {delay_minutes} minutes. "
                            f"Scenes requiring {actor_name}: {blocked_scenes}.",
                sceneIds=blocked_scenes,
            ),
            Evidence(
                evidenceType="SCENE_AVAILABILITY",
                description=f"Scene {target_scene_id} ({target_scene.title}) requires "
                            f"actors {target_scene.characterIds} — all currently available. "
                            f"Location {target_scene.locationId} status: "
                            f"{'AVAILABLE' if location_available else 'UNKNOWN'}.",
                sceneIds=[target_scene_id],
            ),
        ]

        # Check daylight constraint
        risks = []
        if location and location.daylightConstraint and location.daylightDeadlineTime:
            risks.append(ProposalRisk(
                description=f"Location {location.name} has daylight constraint — "
                            f"must wrap by {location.daylightDeadlineTime}.",
                severity=Severity.MEDIUM,
            ))

        # Check ACT_04 availability window (for SC_08 specifically)
        for char_id in target_scene.characterIds:
            char_actor = self._store.actors.get(char_id)
            if char_actor and char_actor.availableUntilTime <= "13:00":
                risks.append(ProposalRisk(
                    description=f"{char_actor.name} ({char_actor.characterName}) "
                                f"available only until {char_actor.availableUntilTime}. "
                                f"Moving {target_scene_id} forward reduces this risk.",
                    severity=Severity.HIGH,
                ))

        proposal = ScheduleProposal(
            shootDayId=day.shootDayId,
            originAgent=AGENT_NAME,
            category=ProposalCategory.RECOMMENDATION,
            proposedChanges=[
                ScheduleChange(
                    changeType="REORDER",
                    sceneId=target_scene_id,
                    fromPosition=target_pos,
                    toPosition=1,
                    reason=f"Move {target_scene_id} forward to avoid blocking during "
                           f"{actor_name}'s {delay_minutes}-minute delay.",
                )
            ],
            why=(
                f"{actor_name} is delayed {delay_minutes} minutes. "
                f"Scenes {blocked_scenes} are currently unavailable. "
                f"Scene {target_scene_id} ({target_scene.title}) can proceed immediately: "
                f"all required actors are present and the location is available."
            ),
            evidence=evidence,
            expectedBenefitMinutes=estimated_benefit,
            affectedScenes=blocked_scenes + [target_scene_id],
            risks=risks,
            confidence=0.87,
        )

        await self._registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.AGENT,
            caller_id=AGENT_NAME,
            correlation_id=event.correlationId,
        )

        logger.info(
            "schedule_proposal_created",
            extra={
                "proposalId": proposal.proposalId,
                "targetScene": target_scene_id,
                "expectedBenefit": estimated_benefit,
                "mode": "DEV",
            },
        )

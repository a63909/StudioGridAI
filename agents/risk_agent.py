"""Production Risk Agent — Phase 1 deterministic implementation.

Monitors all production events and maintains a risk registry.
Creates and updates risks based on: delays, coverage gaps, location deadlines, etc.
"""
from __future__ import annotations

import logging

from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode, EventType, OriginType, Severity
from services.api.domain.events import ProductionEvent
from services.api.domain.models import Evidence, Risk
from .interfaces import BaseAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "PRODUCTION_RISK_AGENT"


class ProductionRiskAgent(BaseAgent):
    """Aggregates and prioritizes production risks."""

    mode: AgentMode = AgentMode.DEV

    def __init__(self, store: LocalStateStore, registry: ToolRegistry) -> None:
        self._store = store
        self._registry = registry

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        if event.type == EventType.ACTOR_DELAYED:
            await self._risk_actor_delay(event)
        elif event.type == EventType.COVERAGE_ALERT_CREATED:
            await self._risk_coverage_gap(event)
        elif event.type == EventType.CONTINUITY_ALERT_CREATED:
            await self._risk_continuity(event)
        elif event.type == EventType.LOCATION_WARNING:
            await self._risk_location(event)

    async def _risk_actor_delay(self, event: ProductionEvent) -> None:
        actor_id = event.payload.get("actorId", "")
        delay_min = event.payload.get("delayMinutes", 0)
        actor_name = event.payload.get("actorName", actor_id)
        blocked = self._store.get_scenes_blocked_by_actor(actor_id)

        severity = Severity.HIGH if delay_min > 30 else Severity.MEDIUM

        risk = Risk(
            severity=severity,
            reason=f"{actor_name} delayed {delay_min} minutes. "
                   f"Scenes {blocked} cannot proceed.",
            evidence=[
                Evidence(
                    evidenceType="ACTOR_DELAY",
                    description=f"{actor_name} reported delayed {delay_min} minutes.",
                    sceneIds=blocked,
                )
            ],
            affectedScenes=blocked,
            suggestedAction="Review schedule proposal from SCHEDULE_AGENT and approve if viable.",
            confidence=0.95,
        )

        day = self._store.get_active_shoot_day()
        if day:
            await self._registry.create_risk(
                risk=risk,
                shoot_day_id=day.shootDayId,
                caller_type=OriginType.AGENT,
                caller_id=AGENT_NAME,
                correlation_id=event.correlationId,
            )

    async def _risk_coverage_gap(self, event: ProductionEvent) -> None:
        scene_id = event.payload.get("sceneId", "")
        missing = event.payload.get("missingShotIds", [])

        risk = Risk(
            severity=Severity.MEDIUM,
            reason=f"Scene {scene_id} has incomplete coverage. Missing: {missing}.",
            evidence=[
                Evidence(
                    evidenceType="COVERAGE_GAP",
                    description=f"Scene {scene_id} missing shots: {missing}.",
                    sceneIds=[scene_id],
                    shotIds=missing,
                )
            ],
            affectedScenes=[scene_id],
            suggestedAction=f"Complete missing shots for {scene_id} before wrap.",
            confidence=0.90,
        )

        day = self._store.get_active_shoot_day()
        if day:
            await self._registry.create_risk(
                risk=risk,
                shoot_day_id=day.shootDayId,
                caller_type=OriginType.AGENT,
                caller_id=AGENT_NAME,
                correlation_id=event.correlationId,
            )

    async def _risk_continuity(self, event: ProductionEvent) -> None:
        alert_id = event.payload.get("alertId", "")
        risk = Risk(
            severity=Severity.LOW,
            reason=f"Continuity alert {alert_id} created. Review before editing.",
            evidence=[
                Evidence(
                    evidenceType="CONTINUITY_ALERT",
                    description=f"Continuity alert {alert_id} requires review.",
                )
            ],
            affectedScenes=[],
            suggestedAction="Review continuity alert and resolve before end of day.",
            confidence=0.70,
        )

        day = self._store.get_active_shoot_day()
        if day:
            await self._registry.create_risk(
                risk=risk,
                shoot_day_id=day.shootDayId,
                caller_type=OriginType.AGENT,
                caller_id=AGENT_NAME,
                correlation_id=event.correlationId,
            )

    async def _risk_location(self, event: ProductionEvent) -> None:
        location_id = event.payload.get("locationId", "")
        warning = event.payload.get("warning", "")
        location = self._store.locations.get(location_id)
        loc_name = location.name if location else location_id

        risk = Risk(
            severity=Severity.MEDIUM,
            reason=f"Location {loc_name}: {warning}",
            evidence=[
                Evidence(
                    evidenceType="LOCATION_WARNING",
                    description=f"Location {loc_name} warning: {warning}",
                )
            ],
            affectedScenes=[
                sc.sceneId for sc in self._store.scenes.values()
                if sc.locationId == location_id
            ],
            suggestedAction=f"Monitor {loc_name} availability and plan contingency.",
            confidence=0.80,
        )

        day = self._store.get_active_shoot_day()
        if day:
            await self._registry.create_risk(
                risk=risk,
                shoot_day_id=day.shootDayId,
                caller_type=OriginType.AGENT,
                caller_id=AGENT_NAME,
                correlation_id=event.correlationId,
            )

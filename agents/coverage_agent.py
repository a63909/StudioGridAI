"""Coverage Agent — Phase 1 deterministic implementation.

Handles SHOT_COMPLETED events and checks for missing coverage.
Creates CoverageAlerts when scenes have incomplete shot coverage.
"""
from __future__ import annotations

import logging

from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode, AlertStatus, EventType, OriginType, Severity, ShotStatus
from services.api.domain.events import ProductionEvent
from services.api.domain.models import CoverageAlert
from .interfaces import BaseAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "COVERAGE_AGENT"


class CoverageAgent(BaseAgent):
    """Tracks planned vs completed shots and creates coverage alerts."""

    mode: AgentMode = AgentMode.DEV

    def __init__(self, store: LocalStateStore, registry: ToolRegistry) -> None:
        self._store = store
        self._registry = registry

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        if event.type == EventType.SHOT_COMPLETED:
            await self._check_scene_coverage(event)

    async def _check_scene_coverage(self, event: ProductionEvent) -> None:
        scene_id = event.payload.get("sceneId")
        if not scene_id:
            return

        stats = self._store.compute_coverage(scene_id)
        if not stats.missingShotIds:
            # All shots complete — resolve any open coverage alert for this scene
            for alert in self._store.coverage_alerts.values():
                if alert.sceneId == scene_id and alert.status == AlertStatus.OPEN:
                    resolved = alert.model_copy(update={"status": AlertStatus.RESOLVED})
                    self._store.upsert_coverage_alert(resolved)
                    logger.info("coverage_alert_auto_resolved", extra={"sceneId": scene_id})
            return

        # Check if an alert already exists for this scene
        existing = next(
            (a for a in self._store.coverage_alerts.values()
             if a.sceneId == scene_id and a.status == AlertStatus.OPEN),
            None,
        )
        if existing:
            # Update missing shots list
            updated = existing.model_copy(update={"missingShotIds": stats.missingShotIds})
            self._store.upsert_coverage_alert(updated)
            return

        # Determine severity based on coverage percentage
        if stats.coveragePercent < 50:
            severity = Severity.HIGH
        elif stats.coveragePercent < 80:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        scene = self._store.scenes.get(scene_id)
        scene_title = scene.title if scene else scene_id

        # Check if any missing shots require actors with tight availability
        at_risk_actors = []
        for shot_id in stats.missingShotIds:
            shot = self._store.shots.get(shot_id)
            if shot and shot.characterId:
                actor = self._store.actors.get(shot.characterId)
                if actor and actor.availableUntilTime <= "13:00":
                    at_risk_actors.append(f"{actor.name} (until {actor.availableUntilTime})")
                    severity = Severity.HIGH  # escalate if time-constrained actor needed

        description = (
            f"Scene {scene_id} ({scene_title}) has incomplete coverage. "
            f"Missing shots: {stats.missingShotIds}. "
            f"Coverage: {stats.coveragePercent}%."
        )
        if at_risk_actors:
            description += f" Time-constrained actors needed: {', '.join(at_risk_actors)}."

        day = self._store.get_active_shoot_day()
        if day is None:
            return

        alert = CoverageAlert(
            sceneId=scene_id,
            missingShotIds=stats.missingShotIds,
            severity=severity,
            description=description,
        )

        await self._registry.create_coverage_alert(
            alert=alert,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.AGENT,
            caller_id=AGENT_NAME,
            correlation_id=event.correlationId,
        )

        logger.info(
            "coverage_alert_created",
            extra={
                "alertId": alert.alertId,
                "sceneId": scene_id,
                "missingShots": stats.missingShotIds,
                "severity": severity,
                "mode": "DEV",
            },
        )

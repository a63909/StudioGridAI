"""Continuity Agent — Phase 1 deterministic implementation.

Handles CONTINUITY_FACT_RECORDED events and detects potential conflicts.
Creates ContinuityAlerts typed as INFERENCE — never as confirmed facts.
"""
from __future__ import annotations

import logging

from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode, AlertType, EventType, OriginType, Severity
from services.api.domain.events import ProductionEvent
from services.api.domain.models import ContinuityAlert, ContinuityFact
from .interfaces import BaseAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "CONTINUITY_AGENT"

# Attributes that are semantically related and may conflict
RELATED_ATTRIBUTES: dict[str, set[str]] = {
    "notebook_hand": {"notebook_position", "notebook_hand"},
    "notebook_position": {"notebook_hand", "notebook_position"},
    "jacket_state": {"jacket_state"},
    "scarf_position": {"scarf_position"},
}


class ContinuityAgent(BaseAgent):
    """Detects continuity conflicts between recorded facts.

    IMPORTANT: Alerts are always INFERENCE type, never FACT.
    The agent cannot confirm 100% that something is wrong — it flags
    potential conflicts for human review.
    """

    mode: AgentMode = AgentMode.DEV

    def __init__(self, store: LocalStateStore, registry: ToolRegistry) -> None:
        self._store = store
        self._registry = registry

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        if event.type == EventType.CONTINUITY_FACT_RECORDED:
            await self._check_for_conflicts(event)

    async def _check_for_conflicts(self, event: ProductionEvent) -> None:
        new_fact_data = event.payload
        new_fact_id = new_fact_data.get("factId")
        if not new_fact_id:
            return

        new_fact = self._store.continuity_facts.get(new_fact_id)
        if new_fact is None:
            return

        # Find related attributes to check against
        related = RELATED_ATTRIBUTES.get(new_fact.attribute, {new_fact.attribute})

        # Check all existing facts for the same prop or character
        for existing_fact in self._store.continuity_facts.values():
            if existing_fact.factId == new_fact_id:
                continue
            if existing_fact.sceneId == new_fact.sceneId:
                continue  # Same scene — no continuity issue

            # Check if they concern the same prop or character
            same_prop = (
                new_fact.propId is not None
                and existing_fact.propId == new_fact.propId
            )
            same_character = (
                new_fact.characterId is not None
                and existing_fact.characterId == new_fact.characterId
            )

            if not (same_prop or same_character):
                continue

            # Check if attributes are related
            if existing_fact.attribute not in related:
                continue

            # Check if values conflict (different values for related attributes)
            if not self._values_conflict(new_fact, existing_fact):
                continue

            # Check if an alert already exists for this pair
            already_exists = any(
                (a.factA.factId == existing_fact.factId and a.factB.factId == new_fact_id)
                or (a.factA.factId == new_fact_id and a.factB.factId == existing_fact.factId)
                for a in self._store.continuity_alerts.values()
            )
            if already_exists:
                continue

            await self._create_conflict_alert(new_fact, existing_fact, event.correlationId)

    def _values_conflict(self, fact_a: ContinuityFact, fact_b: ContinuityFact) -> bool:
        """Determine if two facts have conflicting values."""
        # Direct value conflict on same attribute
        if fact_a.attribute == fact_b.attribute and fact_a.value != fact_b.value:
            return True

        # Cross-attribute semantic conflict (notebook hand vs notebook position)
        if (
            fact_a.attribute == "notebook_hand"
            and fact_b.attribute == "notebook_position"
        ) or (
            fact_a.attribute == "notebook_position"
            and fact_b.attribute == "notebook_hand"
        ):
            # These are semantically related — any different values warrant review
            return True

        return False

    async def _create_conflict_alert(
        self,
        fact_a: ContinuityFact,
        fact_b: ContinuityFact,
        correlation_id: str,
    ) -> None:
        prop_id = fact_a.propId or fact_b.propId
        prop = self._store.props.get(prop_id) if prop_id else None
        prop_name = prop.name if prop else (prop_id or "unknown prop")

        char_id = fact_a.characterId or fact_b.characterId
        char_actor = self._store.actors.get(char_id) if char_id else None
        char_name = char_actor.characterName if char_actor else (char_id or "")

        description = (
            f"Potential continuity issue with {prop_name}"
            + (f" ({char_name})" if char_name else "")
            + f" between Scene {fact_a.sceneId} and Scene {fact_b.sceneId}. "
            f"In {fact_a.sceneId}: {fact_a.attribute} = {fact_a.value}. "
            f"In {fact_b.sceneId}: {fact_b.attribute} = {fact_b.value}. "
            "If these scenes are in direct continuity, the transition may be unexplained. "
            "Review before editing. (INFERENCE — not a confirmed error)"
        )

        alert = ContinuityAlert(
            alertType=AlertType.INFERENCE,  # Always INFERENCE — never claim confirmed error
            severity=Severity.MEDIUM,
            factA=fact_a,
            factB=fact_b,
            description=description,
        )

        day = self._store.get_active_shoot_day()
        if day is None:
            return

        await self._registry.create_continuity_alert(
            alert=alert,
            shoot_day_id=day.shootDayId,
            caller_type=OriginType.AGENT,
            caller_id=AGENT_NAME,
            correlation_id=correlation_id,
        )

        logger.info(
            "continuity_alert_created",
            extra={
                "alertId": alert.alertId,
                "alertType": "INFERENCE",
                "factAScene": fact_a.sceneId,
                "factBScene": fact_b.sceneId,
                "mode": "DEV",
            },
        )

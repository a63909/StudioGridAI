"""Wrap Report Agent — deterministic calculation from actual state.

This agent is deterministic in both Phase 1 and Phase 2.
No AI inference needed — it reads from actual state and calculates.
"""
from __future__ import annotations

import logging

from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode, EventType, OriginType
from services.api.domain.events import ProductionEvent
from services.api.domain.models import WrapReport
from .interfaces import BaseAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "WRAP_REPORT_AGENT"


class WrapReportAgent(BaseAgent):
    """Generates end-of-day report from actual state.

    Purely deterministic. Never hardcodes values.
    """

    mode: AgentMode = AgentMode.DEV

    def __init__(self, store: LocalStateStore, registry: ToolRegistry) -> None:
        self._store = store
        self._registry = registry

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        if event.type == EventType.SHOOT_DAY_WRAPPED:
            await self._generate_report(event)

    async def _generate_report(self, event: ProductionEvent) -> WrapReport:
        shoot_day_id = event.payload.get("shootDayId", event.shootDayId)
        logger.info("generating_wrap_report", extra={"shootDayId": shoot_day_id, "mode": "DEV"})

        report = await self._registry.generate_wrap_report(
            shoot_day_id=shoot_day_id,
            caller_type=OriginType.AGENT,
            caller_id=AGENT_NAME,
            correlation_id=event.correlationId,
        )

        logger.info(
            "wrap_report_generated",
            extra={
                "reportId": report.reportId,
                "completedShots": report.completedShotCount,
                "plannedShots": report.plannedShotCount,
                "mode": "DEV",
            },
        )
        return report

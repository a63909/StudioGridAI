"""Production Orchestrator — coordinates all agents.

Routes production events to the appropriate specialized agents.
In Phase 1: deterministic agents.
In Phase 2: replaced by Google Cloud Agent Builder orchestration.
"""
from __future__ import annotations

import logging

from services.api.core.event_bus import LocalEventBus
from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode
from services.api.domain.events import ProductionEvent
from .interfaces import BaseAgent
from .schedule_agent import ScheduleAgent
from .coverage_agent import CoverageAgent
from .continuity_agent import ContinuityAgent
from .risk_agent import ProductionRiskAgent
from .wrap_report_agent import WrapReportAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "PRODUCTION_ORCHESTRATOR"


class ProductionOrchestrator(BaseAgent):
    """Coordinates all specialized agents.

    Phase 1: routes events to deterministic agents.
    Phase 2: replaced by Google Cloud Agent Builder orchestration.
    All tool calls still flow through the same ToolRegistry.
    """

    mode: AgentMode = AgentMode.DEV

    def __init__(self, store: LocalStateStore, event_bus: LocalEventBus) -> None:
        registry = ToolRegistry(store=store, event_bus=event_bus)

        self._agents: list[BaseAgent] = [
            ScheduleAgent(store=store, registry=registry),
            CoverageAgent(store=store, registry=registry),
            ContinuityAgent(store=store, registry=registry),
            ProductionRiskAgent(store=store, registry=registry),
            WrapReportAgent(store=store, registry=registry),
        ]
        self._registry = registry
        self._store = store

        # Subscribe orchestrator to all events
        event_bus.subscribe_all(self.handle_event)

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        """Route event to all subscribed agents."""
        logger.debug(
            "orchestrator_routing_event",
            extra={
                "eventType": event.type,
                "correlationId": event.correlationId,
                "mode": "DEV",
                "agentCount": len(self._agents),
            },
        )
        for agent in self._agents:
            try:
                await agent.handle_event(event)
            except Exception as e:
                logger.error(
                    "agent_error",
                    extra={
                        "agentName": agent.agent_name,
                        "eventType": event.type,
                        "error": str(e),
                    },
                    exc_info=e,
                )

    def get_registry(self) -> ToolRegistry:
        return self._registry

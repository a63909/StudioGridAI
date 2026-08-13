"""Production Orchestrator — Phase 2 with real Google ADK agents.

Routes production events to specialized agents:
  - ACTOR_DELAYED → RealScheduleAgent (Gemini-powered)
  - SHOT_COMPLETED → RealCoverageAgent (Gemini-powered)
  - Other events → deterministic Phase 1 agents (unchanged)

Graceful degradation: if Gemini fails, no production state is corrupted.
The deterministic fallback agents remain available.

See: docs/adr/005-google-agent-runtime-integration.md
"""
from __future__ import annotations

import logging

from services.api.core.event_bus import LocalEventBus
from services.api.core.tool_registry import ToolRegistry
from services.api.db.local_store import LocalStateStore
from services.api.domain.enums import AgentMode
from services.api.domain.events import ProductionEvent
from services.api.config import settings
from services.api.tools.http_client import FastAPIToolGateway
from agents.interfaces import BaseAgent
from agents.continuity_agent import ContinuityAgent
from agents.risk_agent import ProductionRiskAgent
from agents.wrap_report_agent import WrapReportAgent

logger = logging.getLogger(__name__)

AGENT_NAME = "PRODUCTION_ORCHESTRATOR"


def _is_ai_enabled() -> bool:
    """Return True if real AI agents are enabled.

    Controlled by STUDIOGRID_AI_ENABLED=1 (set in .env.local for local dev).
    Defaults to False so Phase 1 behaviour is preserved unless explicitly enabled.
    """
    return settings.STUDIOGRID_AI_ENABLED


class ProductionOrchestrator(BaseAgent):
    """Orchestrates all agents — real AI for Phase 2 events, deterministic fallback.

    Phase 2 agent routing:
      ACTOR_DELAYED   → RealScheduleAgent (Gemini 3.6 Flash)
      SHOT_COMPLETED  → RealCoverageAgent (Gemini 3.6 Flash)
      other events    → deterministic Phase 1 agents

    If STUDIOGRID_AI_ENABLED=0 (default), uses deterministic agents only.
    """

    mode: AgentMode = AgentMode.PRODUCTION if _is_ai_enabled() else AgentMode.DEV

    def __init__(self, store: LocalStateStore, event_bus: LocalEventBus) -> None:
        registry = ToolRegistry(store=store, event_bus=event_bus)

        # Deterministic agents (Phase 1 — always active)
        from agents.schedule_agent import ScheduleAgent
        from agents.coverage_agent import CoverageAgent

        self._schedule_agent_det = ScheduleAgent(store=store, registry=registry)
        self._coverage_agent_det = CoverageAgent(store=store, registry=registry)
        self._continuity_agent = ContinuityAgent(store=store, registry=registry)
        self._risk_agent = ProductionRiskAgent(store=store, registry=registry)
        self._wrap_agent = WrapReportAgent(store=store, registry=registry)

        # AI agents (Phase 2 — active when STUDIOGRID_AI_ENABLED=1)
        self._ai_schedule_agent = None
        self._ai_coverage_agent = None

        if _is_ai_enabled():
            try:
                from agents.google_adk.schedule_agent_real import RealScheduleAgent
                from agents.google_adk.coverage_agent_real import RealCoverageAgent
                gateway = FastAPIToolGateway(settings.STUDIOGRID_TOOL_SERVER_URL)
                self._ai_schedule_agent = RealScheduleAgent(store=store, gateway=gateway)
                self._ai_coverage_agent = RealCoverageAgent(store=store, gateway=gateway)
                logger.info(
                    "ai_agents_initialized",
                    extra={"scheduleAgent": "RealScheduleAgent", "coverageAgent": "RealCoverageAgent"},
                )
            except Exception as e:
                from agents.google_adk.runtime import mark_runtime_error
                mark_runtime_error(f"AGENT_INIT_{type(e).__name__}")
                logger.error(
                    "ai_agent_init_failed",
                    extra={"error": str(e)},
                    exc_info=e,
                )
                # Keep the AI route blocked. An explicitly enabled runtime must
                # never be silently replaced with deterministic output.

        self._registry = registry
        self._store = store
        event_bus.subscribe_all(self.handle_event)

    @property
    def agent_name(self) -> str:
        return AGENT_NAME

    async def handle_event(self, event: ProductionEvent) -> None:
        logger.debug(
            "orchestrator_routing_event",
            extra={
                "eventType": event.type,
                "correlationId": event.correlationId,
                "aiEnabled": _is_ai_enabled(),
            },
        )

        from services.api.domain.enums import EventType

        # Deterministic handling is an explicit dev-mode choice, never a silent
        # substitute for a failed or unavailable Gemini runtime.
        if event.type == EventType.ACTOR_DELAYED:
            if _is_ai_enabled():
                if self._ai_schedule_agent is None:
                    logger.error(
                        "ai_route_blocked",
                        extra={"agentName": "SCHEDULE_AGENT", "eventType": event.type},
                    )
                else:
                    await self._run_agent(self._ai_schedule_agent, event)
            else:
                await self._run_agent(self._schedule_agent_det, event)

        elif event.type == EventType.SHOT_COMPLETED:
            if _is_ai_enabled():
                if self._ai_coverage_agent is None:
                    logger.error(
                        "ai_route_blocked",
                        extra={"agentName": "COVERAGE_AGENT", "eventType": event.type},
                    )
                else:
                    await self._run_agent(self._ai_coverage_agent, event)
            else:
                await self._run_agent(self._coverage_agent_det, event)

        # Deterministic agents always handle their events
        for agent in [self._continuity_agent, self._risk_agent, self._wrap_agent]:
            await self._run_agent(agent, event)

    async def _run_agent(self, agent: BaseAgent, event: ProductionEvent) -> None:
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

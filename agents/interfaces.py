"""Abstract agent interfaces for StudioGrid AI.

Phase 1: Deterministic implementations behind these interfaces.
Phase 2: Real Gemini + Agent Builder implementations replace internals.

The interface contract does not change between phases.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from services.api.domain.enums import AgentMode
from services.api.domain.events import ProductionEvent


class BaseAgent(ABC):
    """Abstract base for all StudioGrid AI agents.

    In Phase 1 (DEV mode): deterministic logic.
    In Phase 2 (PRODUCTION mode): real Gemini/Agent Builder inference.

    The tool contracts and state mutation paths are identical in both phases.
    """

    mode: AgentMode = AgentMode.DEV

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique agent identifier. Always English."""
        ...

    @abstractmethod
    async def handle_event(self, event: ProductionEvent) -> None:
        """Handle a production event.

        Args:
            event: The production event to handle.
        """
        ...

    def get_mode(self) -> AgentMode:
        return self.mode

    def is_dev_mode(self) -> bool:
        return self.mode == AgentMode.DEV

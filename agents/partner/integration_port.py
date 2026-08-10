"""PartnerIntegrationPort — neutral interface for contest partner services.

Concrete implementation provided only after official contest partner runtime
requirements are confirmed and verified.

States:
  NOT_CONFIGURED — no partner config present (default in Phase 1)
  NOT_CONNECTED  — config present, no live connection verified
  CONNECTED      — live verified connection active
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from services.api.domain.enums import PartnerIntegrationStatus
from services.api.domain.events import ProductionEvent


class PartnerIntegrationPort(ABC):
    """Abstract partner integration boundary.

    This interface is neutral — it does not assume IBM, Confluent, or any
    specific service. The concrete implementation is created only after
    official contest partner requirements are confirmed.

    See: docs/evidence/README.md — Blocking Compliance Question
    """

    @property
    @abstractmethod
    def status(self) -> PartnerIntegrationStatus:
        """Current connection status."""
        ...

    @abstractmethod
    async def publish_event(self, event: ProductionEvent) -> None:
        """Publish a production event to the partner service."""
        ...

    @abstractmethod
    async def health_check(self) -> PartnerIntegrationStatus:
        """Check the current connection status."""
        ...

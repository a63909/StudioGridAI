"""NullPartnerPort — default no-op partner integration.

Active until official partner requirements are confirmed and credentials provided.
Status is always NOT_CONFIGURED.

UI must show: PARTNER INTEGRATION: NOT CONFIGURED
"""
from __future__ import annotations

from services.api.domain.enums import PartnerIntegrationStatus
from services.api.domain.events import ProductionEvent
from .integration_port import PartnerIntegrationPort


class NullPartnerPort(PartnerIntegrationPort):
    """Default no-op implementation.

    Does nothing. Returns NOT_CONFIGURED for all status checks.

    This is intentional: we do not fake a connection that does not exist.
    """

    @property
    def status(self) -> PartnerIntegrationStatus:
        return PartnerIntegrationStatus.NOT_CONFIGURED

    async def publish_event(self, event: ProductionEvent) -> None:
        # Intentional no-op.
        # Events are not forwarded to any partner service in this mode.
        pass

    async def health_check(self) -> PartnerIntegrationStatus:
        return PartnerIntegrationStatus.NOT_CONFIGURED

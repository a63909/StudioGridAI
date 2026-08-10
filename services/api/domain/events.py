"""Domain events for StudioGrid AI.

ProductionEvent is the core primitive. All state changes are triggered by events.
Events are immutable once created.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import EventType, OriginType


def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


class ProductionEvent(BaseModel):
    """Immutable record of something that happened during a shoot day.

    Every state change in StudioGrid AI is triggered by a ProductionEvent.
    Events are never modified after creation — new events supersede old ones.
    """

    eventId: str = Field(default_factory=_new_id)
    productionId: str
    shootDayId: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    originType: OriginType
    originId: str
    type: EventType
    payload: dict[str, Any]
    source: str
    correlationId: str = Field(default_factory=_new_id)

    model_config = {"frozen": True}

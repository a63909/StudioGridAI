"""Tests for ProductionEvent creation and validation."""
import pytest
from datetime import datetime

from services.api.domain.enums import EventType, OriginType
from services.api.domain.events import ProductionEvent


def test_event_created_with_required_fields():
    event = ProductionEvent(
        productionId="PROD_001",
        shootDayId="DAY_001",
        originType=OriginType.HUMAN,
        originId="production_manager",
        type=EventType.SHOOT_DAY_STARTED,
        payload={"shootDayId": "DAY_001"},
        source="test",
    )
    assert event.eventId is not None
    assert event.correlationId is not None
    assert event.timestamp is not None
    assert event.productionId == "PROD_001"
    assert event.type == EventType.SHOOT_DAY_STARTED


def test_event_ids_are_unique():
    events = [
        ProductionEvent(
            productionId="PROD_001",
            shootDayId="DAY_001",
            originType=OriginType.SYSTEM,
            originId="system",
            type=EventType.SHOT_STARTED,
            payload={},
            source="test",
        )
        for _ in range(10)
    ]
    ids = [e.eventId for e in events]
    assert len(set(ids)) == 10


def test_event_is_frozen():
    """Events must be immutable once created."""
    event = ProductionEvent(
        productionId="PROD_001",
        shootDayId="DAY_001",
        originType=OriginType.HUMAN,
        originId="pm",
        type=EventType.SHOT_COMPLETED,
        payload={},
        source="test",
    )
    with pytest.raises(Exception):
        event.productionId = "CHANGED"  # type: ignore


def test_invalid_event_type_rejected():
    with pytest.raises(Exception):
        ProductionEvent(
            productionId="PROD_001",
            shootDayId="DAY_001",
            originType=OriginType.HUMAN,
            originId="pm",
            type="INVALID_TYPE",  # type: ignore
            payload={},
            source="test",
        )


def test_event_ordering_in_bus():
    """Events published to LocalEventBus are stored in order."""
    import asyncio
    from services.api.core.event_bus import LocalEventBus

    bus = LocalEventBus()
    events = [
        ProductionEvent(
            productionId="P",
            shootDayId="D",
            originType=OriginType.SYSTEM,
            originId="s",
            type=EventType.SHOT_STARTED,
            payload={"order": i},
            source="test",
        )
        for i in range(5)
    ]

    async def run():
        for e in events:
            await bus.publish(e)

    asyncio.run(run())
    log = bus.get_event_log()
    assert len(log) == 5
    for i, e in enumerate(log):
        assert e.payload["order"] == i

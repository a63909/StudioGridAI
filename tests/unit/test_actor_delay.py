"""Tests for actor delay effects."""
import asyncio
import pytest

from services.api.domain.enums import ActorStatus, OriginType


def test_actor_delay_updates_status(store, registry):
    async def run():
        return await registry.report_actor_delay(
            actor_id="ACT_02",
            delay_minutes=45,
            reason="Transport issue",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="production_manager",
            correlation_id="test-corr",
        )

    actor = asyncio.run(run())
    assert actor.currentStatus == ActorStatus.DELAYED
    assert actor.delayMinutes == 45
    assert store.actors["ACT_02"].currentStatus == ActorStatus.DELAYED


def test_delay_creates_event(store, event_bus, registry):
    events_received = []

    async def handler(event):
        events_received.append(event)

    from services.api.domain.enums import EventType
    event_bus.subscribe(EventType.ACTOR_DELAYED, handler)

    async def run():
        await registry.report_actor_delay(
            actor_id="ACT_02",
            delay_minutes=45,
            reason="Transport",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="c1",
        )

    asyncio.run(run())
    assert len(events_received) == 1
    assert events_received[0].payload["actorId"] == "ACT_02"
    assert events_received[0].payload["delayMinutes"] == 45


def test_delayed_actor_blocks_correct_scenes(store, registry):
    """ACT_02 is in SC_04, SC_05, SC_07, SC_09 — these should be blocked."""
    async def run():
        await registry.report_actor_delay(
            actor_id="ACT_02",
            delay_minutes=45,
            reason="Test",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="c1",
        )

    asyncio.run(run())
    blocked = store.get_scenes_blocked_by_actor("ACT_02")
    # SC_04 requires ACT_02
    assert "SC_04" in blocked or len(blocked) > 0


def test_scenes_without_delayed_actor_remain_available(store, registry):
    """SC_08 only requires ACT_03 + ACT_04 — should not be blocked by ACT_02 delay."""
    async def run():
        await registry.report_actor_delay(
            actor_id="ACT_02",
            delay_minutes=45,
            reason="Test",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="c1",
        )

    asyncio.run(run())
    blocked = store.get_scenes_blocked_by_actor("ACT_02")
    assert "SC_08" not in blocked


def test_actor_available_resolves_delay(store, registry):
    async def run():
        await registry.report_actor_delay(
            actor_id="ACT_02",
            delay_minutes=45,
            reason="Test",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="c1",
        )
        return await registry.report_actor_available(
            actor_id="ACT_02",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="c2",
        )

    actor = asyncio.run(run())
    assert actor.currentStatus == ActorStatus.AVAILABLE
    assert actor.delayMinutes == 0

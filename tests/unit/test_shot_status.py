"""Tests for shot status transitions and approval gates."""
import asyncio
import pytest

from services.api.domain.enums import OriginType, ShotStatus
from services.api.core.approval_gates import ApprovalRequiredError


def test_shot_starts_as_planned(store):
    shots = list(store.shots.values())
    assert all(s.status == ShotStatus.PLANNED for s in shots)


def test_valid_transition_planned_to_in_progress(store, registry):
    shot = next(iter(store.shots.values()))
    shot_id = shot.shotId

    async def run():
        return await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="test-corr",
        )

    updated = asyncio.run(run())
    assert updated.status == ShotStatus.IN_PROGRESS
    assert store.shots[shot_id].status == ShotStatus.IN_PROGRESS


def test_valid_transition_in_progress_to_complete(store, registry):
    shot = next(iter(store.shots.values()))
    shot_id = shot.shotId

    async def run():
        await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="corr-1",
        )
        return await registry.record_shot_completed(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="corr-2",
            actual_duration_minutes=15,
        )

    completed = asyncio.run(run())
    assert completed.status == ShotStatus.COMPLETE


def test_invalid_transition_planned_to_complete_raises(store, registry):
    """Cannot complete a shot that hasn't started."""
    shot = next(iter(store.shots.values()))

    async def run():
        return await registry.record_shot_completed(
            shot_id=shot.shotId,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="corr",
        )

    with pytest.raises(ValueError, match="IN_PROGRESS"):
        asyncio.run(run())


def test_complete_shot_cannot_be_started_again(store, registry):
    shot = next(iter(store.shots.values()))
    shot_id = shot.shotId

    async def run():
        await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="c1",
        )
        await registry.record_shot_completed(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="c2",
        )
        # Try to start again
        await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="c3",
        )

    with pytest.raises(ValueError):
        asyncio.run(run())

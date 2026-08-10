"""Tests for tool authorization."""
import asyncio
import pytest

from services.api.core.tool_registry import ToolAuthorizationError
from services.api.domain.enums import OriginType


def test_agent_cannot_start_shot(store, registry):
    """AGENT is not in allowed_callers for record_shot_started."""
    shot_id = list(store.shots.keys())[0]

    async def run():
        await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.AGENT,  # Not allowed
            caller_id="SOME_AGENT",
            correlation_id="test",
        )

    with pytest.raises(ToolAuthorizationError):
        asyncio.run(run())


def test_human_can_start_shot(store, registry):
    shot_id = list(store.shots.keys())[0]

    async def run():
        return await registry.record_shot_started(
            shot_id=shot_id,
            caller_type=OriginType.HUMAN,
            caller_id="first_ad",
            correlation_id="test",
        )

    result = asyncio.run(run())
    assert result is not None


def test_agent_can_create_schedule_proposal(store, registry):
    from services.api.domain.models import ScheduleProposal
    from services.api.domain.enums import ProposalCategory

    proposal = ScheduleProposal(
        shootDayId="DAY_001",
        originAgent="SCHEDULE_AGENT",
        category=ProposalCategory.RECOMMENDATION,
        proposedChanges=[],
        why="test",
        evidence=[],
        expectedBenefitMinutes=10,
        affectedScenes=[],
        risks=[],
        confidence=0.8,
    )

    async def run():
        return await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,  # AGENT is allowed to create
            caller_id="SCHEDULE_AGENT",
            correlation_id="test",
        )

    result = asyncio.run(run())
    assert result is not None

"""Tests for wrap report calculation."""
import asyncio
import pytest

from services.api.domain.enums import OriginType, ShotStatus


def test_wrap_report_counts_from_actual_state(store, registry):
    """Wrap report must reflect actual shot state, never hardcoded values."""
    # Complete 5 shots
    shot_ids = list(store.shots.keys())[:5]

    async def run():
        for sid in shot_ids:
            await registry.record_shot_started(
                shot_id=sid,
                caller_type=OriginType.HUMAN,
                caller_id="fa",
                correlation_id=f"c-{sid}",
            )
            await registry.record_shot_completed(
                shot_id=sid,
                caller_type=OriginType.HUMAN,
                caller_id="fa",
                correlation_id=f"cc-{sid}",
                actual_duration_minutes=10,
            )
        return await registry.generate_wrap_report(
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="wrap-corr",
        )

    report = asyncio.run(run())
    assert report.completedShotCount == 5
    assert report.plannedShotCount == len(store.shots)
    assert len(report.incompleteShotIds) == len(store.shots) - 5


def test_wrap_report_total_delay_reflects_actual_delays(store, registry):
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
        return await registry.generate_wrap_report(
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="wrap-corr",
        )

    report = asyncio.run(run())
    assert report.totalDelayMinutes == 45


def test_wrap_report_recovered_minutes_from_approved_proposal(store, registry):
    from services.api.domain.models import Evidence, ProposalRisk, ScheduleChange, ScheduleProposal
    from services.api.domain.enums import ProposalCategory, Severity

    proposal = ScheduleProposal(
        shootDayId="DAY_001",
        originAgent="SCHEDULE_AGENT",
        category=ProposalCategory.RECOMMENDATION,
        proposedChanges=[],
        why="Test",
        evidence=[],
        expectedBenefitMinutes=37,
        affectedScenes=[],
        risks=[],
        confidence=0.9,
    )

    async def run():
        await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,
            caller_id="SCHEDULE_AGENT",
            correlation_id="c1",
        )
        await registry.approve_schedule_proposal(
            proposal_id=proposal.proposalId,
            approved_by="pm",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="c2",
        )
        return await registry.generate_wrap_report(
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="pm",
            correlation_id="wrap",
        )

    report = asyncio.run(run())
    assert report.estimatedMinutesRecovered == 37
    assert proposal.proposalId in report.approvedScheduleChangeIds

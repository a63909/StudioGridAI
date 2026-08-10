"""Tests for schedule proposal creation, approval, and rejection."""
import asyncio
import pytest

from services.api.domain.enums import OriginType, ProposalCategory, ProposalStatus, Severity
from services.api.domain.models import Evidence, ProposalRisk, ScheduleChange, ScheduleProposal
from services.api.core.approval_gates import ApprovalRequiredError


def make_proposal(shoot_day_id: str = "DAY_001") -> ScheduleProposal:
    return ScheduleProposal(
        shootDayId=shoot_day_id,
        originAgent="SCHEDULE_AGENT",
        category=ProposalCategory.RECOMMENDATION,
        proposedChanges=[
            ScheduleChange(
                changeType="REORDER",
                sceneId="SC_08",
                fromPosition=4,
                toPosition=1,
                reason="Actor delay — move scene forward",
            )
        ],
        why="Actor delayed. SC_08 can proceed without them.",
        evidence=[
            Evidence(
                evidenceType="ACTOR_STATUS",
                description="ACT_02 delayed 45 minutes.",
                sceneIds=["SC_04", "SC_05"],
            )
        ],
        expectedBenefitMinutes=37,
        affectedScenes=["SC_04", "SC_05", "SC_08"],
        risks=[ProposalRisk(description="Location constraint", severity=Severity.MEDIUM)],
        confidence=0.87,
    )


def test_proposal_created_with_required_fields(store, registry):
    proposal = make_proposal()
    assert proposal.proposalId is not None
    assert proposal.status == ProposalStatus.PENDING
    assert proposal.why != ""
    assert len(proposal.evidence) > 0
    assert 0.0 <= proposal.confidence <= 1.0
    assert len(proposal.affectedScenes) > 0


def test_proposal_created_via_tool(store, registry):
    proposal = make_proposal()

    async def run():
        return await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,
            caller_id="SCHEDULE_AGENT",
            correlation_id="test-corr",
        )

    result = asyncio.run(run())
    assert result.proposalId in store.proposals
    assert store.proposals[result.proposalId].status == ProposalStatus.PENDING


def test_approved_proposal_changes_status(store, registry):
    proposal = make_proposal()

    async def run():
        await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,
            caller_id="SCHEDULE_AGENT",
            correlation_id="c1",
        )
        return await registry.approve_schedule_proposal(
            proposal_id=proposal.proposalId,
            approved_by="production_manager",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="production_manager",
            correlation_id="c2",
        )

    result = asyncio.run(run())
    assert result.status == ProposalStatus.APPROVED
    assert result.resolvedBy == "production_manager"


def test_rejected_proposal_does_not_change_schedule(store, registry):
    proposal = make_proposal()

    async def run():
        await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,
            caller_id="SCHEDULE_AGENT",
            correlation_id="c1",
        )
        return await registry.reject_schedule_proposal(
            proposal_id=proposal.proposalId,
            rejected_by="production_manager",
            reason="Not needed",
            shoot_day_id="DAY_001",
            caller_type=OriginType.HUMAN,
            caller_id="production_manager",
            correlation_id="c2",
        )

    result = asyncio.run(run())
    assert result.status == ProposalStatus.REJECTED


def test_agent_cannot_approve_proposal(store, registry):
    """Agents must not be able to approve their own proposals."""
    proposal = make_proposal()

    async def run():
        await registry.create_schedule_proposal(
            proposal=proposal,
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,
            caller_id="SCHEDULE_AGENT",
            correlation_id="c1",
        )
        # AGENT tries to approve — must fail
        await registry.approve_schedule_proposal(
            proposal_id=proposal.proposalId,
            approved_by="SCHEDULE_AGENT",
            shoot_day_id="DAY_001",
            caller_type=OriginType.AGENT,  # <-- agent, not human
            caller_id="SCHEDULE_AGENT",
            correlation_id="c2",
        )

    with pytest.raises((ApprovalRequiredError, Exception)):
        asyncio.run(run())

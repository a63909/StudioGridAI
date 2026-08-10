"""Tests for Pydantic schema validation."""
import pytest
from pydantic import ValidationError

from services.api.domain.events import ProductionEvent
from services.api.domain.models import ScheduleProposal, Risk, ContinuityFact
from services.api.domain.enums import EventType, OriginType, ProposalCategory, Severity, FactSource


def test_production_event_validates_correctly():
    event = ProductionEvent(
        productionId="P1",
        shootDayId="D1",
        originType=OriginType.HUMAN,
        originId="pm",
        type=EventType.SHOT_STARTED,
        payload={"shotId": "SH_01"},
        source="test",
    )
    assert event.productionId == "P1"
    assert event.type == EventType.SHOT_STARTED


def test_production_event_missing_required_field():
    with pytest.raises(ValidationError):
        ProductionEvent(
            # Missing productionId
            shootDayId="D1",
            originType=OriginType.HUMAN,
            originId="pm",
            type=EventType.SHOT_STARTED,
            payload={},
            source="test",
        )


def test_schedule_proposal_confidence_bounds():
    """Confidence must be between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        ScheduleProposal(
            shootDayId="D1",
            originAgent="AGENT",
            category=ProposalCategory.RECOMMENDATION,
            proposedChanges=[],
            why="test",
            evidence=[],
            expectedBenefitMinutes=10,
            affectedScenes=[],
            risks=[],
            confidence=1.5,  # Invalid
        )


def test_schedule_proposal_valid():
    p = ScheduleProposal(
        shootDayId="D1",
        originAgent="AGENT",
        category=ProposalCategory.RECOMMENDATION,
        proposedChanges=[],
        why="test",
        evidence=[],
        expectedBenefitMinutes=10,
        affectedScenes=["SC_01"],
        risks=[],
        confidence=0.85,
    )
    assert p.confidence == 0.85


def test_risk_confidence_bounds():
    with pytest.raises(ValidationError):
        Risk(
            severity=Severity.HIGH,
            reason="test",
            evidence=[],
            affectedScenes=[],
            suggestedAction="do something",
            confidence=-0.1,  # Invalid
        )


def test_continuity_fact_validates():
    fact = ContinuityFact(
        sceneId="SC_05",
        attribute="notebook_hand",
        value="LEFT",
        source=FactSource.SCRIPT,
    )
    assert fact.factId is not None
    assert fact.attribute == "notebook_hand"

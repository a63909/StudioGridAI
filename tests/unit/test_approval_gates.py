"""Tests for approval gates."""
import asyncio
import pytest

from services.api.core.approval_gates import ApprovalGate, ApprovalRequiredError
from services.api.domain.enums import OriginType, Severity


def test_human_caller_always_passes():
    """Human callers should never be blocked by ApprovalGate."""
    # Should not raise
    ApprovalGate.check("approve_schedule_proposal", OriginType.HUMAN)
    ApprovalGate.check("wrap_shoot_day", OriginType.HUMAN)
    ApprovalGate.check("resolve_risk", OriginType.HUMAN, severity=Severity.CRITICAL)


def test_agent_blocked_from_approve_schedule():
    with pytest.raises(ApprovalRequiredError) as exc_info:
        ApprovalGate.check("approve_schedule_proposal", OriginType.AGENT)
    assert exc_info.value.tool_name == "approve_schedule_proposal"


def test_agent_blocked_from_wrap_day():
    with pytest.raises(ApprovalRequiredError):
        ApprovalGate.check("wrap_shoot_day", OriginType.AGENT)


def test_agent_blocked_from_critical_risk_resolution():
    with pytest.raises(ApprovalRequiredError):
        ApprovalGate.check("resolve_risk", OriginType.AGENT, severity=Severity.CRITICAL)


def test_agent_blocked_from_high_risk_resolution():
    with pytest.raises(ApprovalRequiredError):
        ApprovalGate.check("resolve_risk", OriginType.AGENT, severity=Severity.HIGH)


def test_agent_allowed_to_resolve_low_risk():
    """Agents can resolve LOW severity risks without human approval."""
    # Should not raise
    ApprovalGate.check("resolve_risk", OriginType.AGENT, severity=Severity.LOW)


def test_agent_allowed_to_resolve_medium_risk():
    """Agents can resolve MEDIUM severity risks without human approval."""
    ApprovalGate.check("resolve_risk", OriginType.AGENT, severity=Severity.MEDIUM)


def test_system_blocked_from_human_only_tools():
    with pytest.raises(ApprovalRequiredError):
        ApprovalGate.check("approve_schedule_proposal", OriginType.SYSTEM)

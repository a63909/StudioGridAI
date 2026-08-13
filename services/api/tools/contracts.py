"""Typed Tool Contracts for StudioGrid AI.

All state mutations in StudioGrid AI happen through these typed tools.
Agents call tools. Tools validate, authorize, apply changes, and audit.

Tool categories:
  - Shot tools: record shot lifecycle events
  - Actor tools: report actor delays and availability
  - Location tools: report location status changes
  - Continuity tools: record facts and manage alerts
  - Coverage tools: manage coverage alerts
  - Schedule tools: create and resolve schedule proposals
  - Risk tools: create and resolve production risks
  - Report tools: generate wrap reports
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..domain.enums import (
    AlertStatus,
    FactSource,
    OriginType,
    ProposalCategory,
    RiskStatus,
    Severity,
)
from ..domain.models import (
    AgentExecution,
    ContinuityFact,
    Evidence,
    ProposalRisk,
    ScheduleChange,
)


# ─────────────────────────────────────────────────────────────────────────────
# Tool metadata — authorization and approval requirements
# ─────────────────────────────────────────────────────────────────────────────

class ToolMeta(BaseModel):
    name: str
    description: str
    allowed_callers: list[OriginType]
    requires_human_approval: bool
    approval_reason: str | None = None


TOOL_REGISTRY_META: dict[str, ToolMeta] = {
    "record_shot_started": ToolMeta(
        name="record_shot_started",
        description="Record that a shot has started rolling.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "record_shot_completed": ToolMeta(
        name="record_shot_completed",
        description="Record that a shot has been completed successfully.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "record_shot_failed": ToolMeta(
        name="record_shot_failed",
        description="Record that a shot attempt failed.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "record_shot_skipped": ToolMeta(
        name="record_shot_skipped",
        description="Record that a shot was skipped for this session.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "report_actor_delay": ToolMeta(
        name="report_actor_delay",
        description="Report that an actor is delayed.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "report_actor_available": ToolMeta(
        name="report_actor_available",
        description="Report that a delayed actor is now available.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "record_location_warning": ToolMeta(
        name="record_location_warning",
        description="Record a warning about location availability.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "record_location_unavailable": ToolMeta(
        name="record_location_unavailable",
        description="Record that a location has become unavailable.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "record_continuity_fact": ToolMeta(
        name="record_continuity_fact",
        description="Record a continuity fact about a shot or scene.",
        allowed_callers=[OriginType.HUMAN, OriginType.SYSTEM, OriginType.AGENT],
        requires_human_approval=False,
    ),
    "create_continuity_alert": ToolMeta(
        name="create_continuity_alert",
        description="Create a continuity alert for a potential conflict between two facts.",
        allowed_callers=[OriginType.AGENT, OriginType.HUMAN],
        requires_human_approval=False,
    ),
    "resolve_continuity_alert": ToolMeta(
        name="resolve_continuity_alert",
        description="Resolve a continuity alert. HIGH/CRITICAL require human approval.",
        allowed_callers=[OriginType.HUMAN, OriginType.AGENT],
        requires_human_approval=False,  # enforced by ApprovalGate for HIGH/CRITICAL
        approval_reason="HIGH/CRITICAL continuity alert override requires human approval.",
    ),
    "create_coverage_alert": ToolMeta(
        name="create_coverage_alert",
        description="Create a coverage alert for a scene with missing shots.",
        allowed_callers=[OriginType.AGENT, OriginType.HUMAN],
        requires_human_approval=False,
    ),
    "resolve_coverage_alert": ToolMeta(
        name="resolve_coverage_alert",
        description="Resolve a coverage alert.",
        allowed_callers=[OriginType.HUMAN, OriginType.AGENT],
        requires_human_approval=False,
    ),
    "create_schedule_proposal": ToolMeta(
        name="create_schedule_proposal",
        description="Create a schedule change proposal. Requires human approval to take effect.",
        allowed_callers=[OriginType.AGENT, OriginType.HUMAN],
        requires_human_approval=False,  # creating is allowed; approving is not
    ),
    "record_agent_execution": ToolMeta(
        name="record_agent_execution",
        description="Persist a safe operational agent trace without chain-of-thought.",
        allowed_callers=[OriginType.AGENT, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
    "approve_schedule_proposal": ToolMeta(
        name="approve_schedule_proposal",
        description="Approve a pending schedule proposal. HUMAN ONLY.",
        allowed_callers=[OriginType.HUMAN],
        requires_human_approval=True,
        approval_reason="Schedule changes require explicit human approval.",
    ),
    "reject_schedule_proposal": ToolMeta(
        name="reject_schedule_proposal",
        description="Reject a pending schedule proposal. HUMAN ONLY.",
        allowed_callers=[OriginType.HUMAN],
        requires_human_approval=True,
        approval_reason="Schedule proposal rejection is a human decision.",
    ),
    "create_risk": ToolMeta(
        name="create_risk",
        description="Create a production risk record.",
        allowed_callers=[OriginType.AGENT, OriginType.HUMAN],
        requires_human_approval=False,
    ),
    "update_risk": ToolMeta(
        name="update_risk",
        description="Update an existing risk record.",
        allowed_callers=[OriginType.AGENT, OriginType.HUMAN],
        requires_human_approval=False,
    ),
    "resolve_risk": ToolMeta(
        name="resolve_risk",
        description="Resolve a risk. HIGH/CRITICAL require human approval.",
        allowed_callers=[OriginType.HUMAN, OriginType.AGENT],
        requires_human_approval=False,  # enforced by ApprovalGate for HIGH/CRITICAL
        approval_reason="HIGH/CRITICAL risk resolution requires human approval.",
    ),
    "wrap_shoot_day": ToolMeta(
        name="wrap_shoot_day",
        description="Wrap the current shoot day. HUMAN ONLY.",
        allowed_callers=[OriginType.HUMAN],
        requires_human_approval=True,
        approval_reason="Wrapping a shoot day is final and requires human confirmation.",
    ),
    "generate_wrap_report": ToolMeta(
        name="generate_wrap_report",
        description="Generate the wrap report from current state (read-only calculation).",
        allowed_callers=[OriginType.AGENT, OriginType.HUMAN, OriginType.SYSTEM],
        requires_human_approval=False,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Tool input schemas
# ─────────────────────────────────────────────────────────────────────────────

class RecordShotStartedInput(BaseModel):
    shotId: str
    shootDayId: str
    startedAt: datetime | None = None


class RecordShotCompletedInput(BaseModel):
    shotId: str
    shootDayId: str
    completedAt: datetime | None = None
    actualDurationMinutes: int | None = None


class RecordShotFailedInput(BaseModel):
    shotId: str
    shootDayId: str
    reason: str


class RecordShotSkippedInput(BaseModel):
    shotId: str
    shootDayId: str
    reason: str


class ReportActorDelayInput(BaseModel):
    actorId: str
    delayMinutes: int
    reason: str
    shootDayId: str


class ReportActorAvailableInput(BaseModel):
    actorId: str
    shootDayId: str


class RecordLocationWarningInput(BaseModel):
    locationId: str
    warning: str
    shootDayId: str


class RecordLocationUnavailableInput(BaseModel):
    locationId: str
    reason: str
    shootDayId: str


class RecordContinuityFactInput(BaseModel):
    sceneId: str
    attribute: str
    value: str
    source: FactSource
    shotId: str | None = None
    characterId: str | None = None
    propId: str | None = None


class CreateContinuityAlertInput(BaseModel):
    factAId: str
    factBId: str
    description: str
    severity: Severity


class ResolveContinuityAlertInput(BaseModel):
    alertId: str
    resolution: str
    resolvedBy: str
    override: bool = False


class CreateCoverageAlertInput(BaseModel):
    sceneId: str
    missingShotIds: list[str]
    severity: Severity
    description: str


class ResolveCoverageAlertInput(BaseModel):
    alertId: str
    resolution: str


class CreateScheduleProposalInput(BaseModel):
    shootDayId: str
    proposedChanges: list[ScheduleChange] = Field(min_length=1)
    why: str
    evidence: list[Evidence]
    expectedBenefitMinutes: int
    affectedScenes: list[str]
    risks: list[ProposalRisk]
    confidence: float = Field(ge=0.0, le=1.0)
    category: ProposalCategory = ProposalCategory.RECOMMENDATION
    originAgent: str = "SCHEDULE_AGENT"


class ApproveScheduleProposalInput(BaseModel):
    proposalId: str
    approvedBy: str


class RejectScheduleProposalInput(BaseModel):
    proposalId: str
    rejectedBy: str
    reason: str


class CreateRiskInput(BaseModel):
    severity: Severity
    reason: str
    evidence: list[Evidence]
    affectedScenes: list[str]
    suggestedAction: str
    confidence: float = Field(ge=0.0, le=1.0)


class UpdateRiskInput(BaseModel):
    riskId: str
    severity: Severity | None = None
    status: RiskStatus | None = None
    suggestedAction: str | None = None


class ResolveRiskInput(BaseModel):
    riskId: str
    resolvedBy: str
    resolution: str


class WrapShootDayInput(BaseModel):
    shootDayId: str
    wrappedBy: str


class GenerateWrapReportInput(BaseModel):
    shootDayId: str


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI agent tool server envelopes
# ─────────────────────────────────────────────────────────────────────────────

class AgentCreateScheduleProposalRequest(BaseModel):
    callerId: str = "SCHEDULE_AGENT"
    correlationId: str
    executionId: str
    input: CreateScheduleProposalInput


class AgentCreateCoverageAlertRequest(BaseModel):
    callerId: str = "COVERAGE_AGENT"
    correlationId: str
    shootDayId: str
    input: CreateCoverageAlertInput


class AgentExecutionRequest(BaseModel):
    callerId: str
    correlationId: str
    execution: AgentExecution

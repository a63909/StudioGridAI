"""Core domain models for StudioGrid AI.

All models use Pydantic v2. These are the single source of truth
for all backend validation and the TypeScript types generated from them.

Key separation enforced throughout:
  FACT         — recorded evidence
  INFERENCE    — AI-derived conclusion
  RECOMMENDATION — agent proposal
  HUMAN_DECISION — explicit human approval or rejection
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .enums import (
    ActorStatus,
    AgentMode,
    AlertStatus,
    AlertType,
    DependencyType,
    FactSource,
    LocationStatus,
    LocationType,
    OriginType,
    ProductionStatus,
    PropStatus,
    ProposalCategory,
    ProposalStatus,
    RiskStatus,
    SceneStatus,
    Severity,
    ShootDayStatus,
    ShotStatus,
    ShotType,
    TimeOfDay,
)


def _new_id() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# Supporting value objects
# ─────────────────────────────────────────────────────────────────────────────

class WardrobeNote(BaseModel):
    item: str
    description: str
    characterId: str


class SceneDependency(BaseModel):
    dependencyId: str = Field(default_factory=_new_id)
    sceneId: str
    dependsOnSceneId: str
    type: DependencyType
    reason: str


class Evidence(BaseModel):
    evidenceId: str = Field(default_factory=_new_id)
    evidenceType: str
    description: str
    factIds: list[str] = Field(default_factory=list)
    shotIds: list[str] = Field(default_factory=list)
    sceneIds: list[str] = Field(default_factory=list)


class ProposalRisk(BaseModel):
    description: str
    severity: Severity


class ScheduleChange(BaseModel):
    changeType: str
    sceneId: str
    fromPosition: int | None = None
    toPosition: int | None = None
    reason: str


class ToolCall(BaseModel):
    toolCallId: str = Field(default_factory=_new_id)
    toolName: str
    callerType: OriginType
    callerId: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    status: str = "PENDING"
    calledAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Continuity
# ─────────────────────────────────────────────────────────────────────────────

class ContinuityFact(BaseModel):
    """A recorded fact about production state at a specific shot.

    source=SCRIPT means from the original screenplay.
    source=CREW_REPORT means reported by on-set crew.
    source=AI_INFERENCE means derived by an agent (always marked as INFERENCE, never FACT).
    """
    factId: str = Field(default_factory=_new_id)
    sceneId: str
    shotId: str | None = None
    characterId: str | None = None
    propId: str | None = None
    attribute: str   # e.g. "notebook_hand", "jacket_color"
    value: str       # e.g. "LEFT", "BLUE"
    recordedAt: datetime = Field(default_factory=datetime.utcnow)
    source: FactSource


class ContinuityAlert(BaseModel):
    """Potential continuity conflict between two recorded facts.

    alertType=INFERENCE means the conflict is agent-detected, not confirmed.
    Never claim 100% error without sufficient evidence.
    """
    alertId: str = Field(default_factory=_new_id)
    alertType: AlertType
    severity: Severity
    factA: ContinuityFact
    factB: ContinuityFact
    description: str
    status: AlertStatus = AlertStatus.OPEN
    resolution: str | None = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    resolvedAt: datetime | None = None
    resolvedBy: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Coverage
# ─────────────────────────────────────────────────────────────────────────────

class CoverageAlert(BaseModel):
    """A scene may not have sufficient coverage for editing."""
    alertId: str = Field(default_factory=_new_id)
    sceneId: str
    missingShotIds: list[str]
    severity: Severity
    description: str
    status: AlertStatus = AlertStatus.OPEN
    resolution: str | None = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    resolvedAt: datetime | None = None


class CoverageStats(BaseModel):
    sceneId: str
    plannedShotCount: int
    completedShotCount: int
    missingShotIds: list[str]
    coveragePercent: float


# ─────────────────────────────────────────────────────────────────────────────
# Schedule proposals
# ─────────────────────────────────────────────────────────────────────────────

class ScheduleProposal(BaseModel):
    """An agent-generated proposal for a schedule change.

    Agents CREATE proposals. Humans APPROVE or REJECT them.
    Agents cannot approve their own proposals (enforced by ApprovalGate).

    category=RECOMMENDATION: the standard case.
    why, evidence, confidence are required — no "trust me" proposals.
    """
    proposalId: str = Field(default_factory=_new_id)
    shootDayId: str
    status: ProposalStatus = ProposalStatus.PENDING
    originAgent: str
    category: ProposalCategory
    proposedChanges: list[ScheduleChange]
    why: str
    evidence: list[Evidence]
    expectedBenefitMinutes: int
    affectedScenes: list[str]
    risks: list[ProposalRisk]
    confidence: float = Field(ge=0.0, le=1.0)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    resolvedAt: datetime | None = None
    resolvedBy: str | None = None   # set to approver/rejecter identity on resolution


# ─────────────────────────────────────────────────────────────────────────────
# Risks
# ─────────────────────────────────────────────────────────────────────────────

class Risk(BaseModel):
    riskId: str = Field(default_factory=_new_id)
    severity: Severity
    reason: str
    evidence: list[Evidence]
    affectedScenes: list[str]
    suggestedAction: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: RiskStatus = RiskStatus.ACTIVE
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    resolvedAt: datetime | None = None
    resolvedBy: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Production entities
# ─────────────────────────────────────────────────────────────────────────────

class Actor(BaseModel):
    actorId: str
    name: str
    characterName: str
    availableFromTime: str    # "HH:MM"
    availableUntilTime: str   # "HH:MM"
    currentStatus: ActorStatus = ActorStatus.AVAILABLE
    delayMinutes: int = 0


class Location(BaseModel):
    locationId: str
    name: str
    locationType: LocationType
    availableFromTime: str    # "HH:MM"
    availableUntilTime: str   # "HH:MM"
    daylightConstraint: bool
    daylightDeadlineTime: str | None = None   # "HH:MM" — only for EXT with daylight constraint
    status: LocationStatus = LocationStatus.AVAILABLE
    notes: str = ""


class Prop(BaseModel):
    propId: str
    name: str
    status: PropStatus = PropStatus.AVAILABLE
    requiredInScenes: list[str]


class Shot(BaseModel):
    shotId: str
    sceneId: str
    shotCode: str               # e.g. "SC08_MASTER", "SC05_CU_MAYA"
    shotType: ShotType
    description: str
    status: ShotStatus = ShotStatus.PLANNED
    characterId: str | None = None
    plannedDurationMinutes: int
    actualDurationMinutes: int | None = None
    startedAt: datetime | None = None
    completedAt: datetime | None = None


class Scene(BaseModel):
    sceneId: str
    sceneNumber: str
    title: str
    description: str
    status: SceneStatus = SceneStatus.PLANNED
    locationId: str
    timeOfDay: TimeOfDay
    characterIds: list[str]
    propIds: list[str]
    wardrobeNotes: list[WardrobeNote] = Field(default_factory=list)
    estimatedDurationMinutes: int
    dependencies: list[SceneDependency] = Field(default_factory=list)
    continuityFacts: list[ContinuityFact] = Field(default_factory=list)


class ScheduledScene(BaseModel):
    position: int
    sceneId: str
    plannedStartTime: str   # "HH:MM"
    estimatedDurationMinutes: int


class ShootDay(BaseModel):
    shootDayId: str
    productionId: str
    date: str   # ISO date "YYYY-MM-DD"
    status: ShootDayStatus = ShootDayStatus.PLANNED
    scheduledScenes: list[ScheduledScene] = Field(default_factory=list)


class Production(BaseModel):
    productionId: str
    title: str
    status: ProductionStatus = ProductionStatus.ACTIVE
    shootDays: list[ShootDay] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# Agent execution trace
# ─────────────────────────────────────────────────────────────────────────────

class AgentExecution(BaseModel):
    """Execution trace for an agent run.

    In DEV mode (Phase 1): model is None, toolCalls come from deterministic logic.
    In PRODUCTION mode (Phase 2): model is filled by Gemini, toolCalls from real inference.

    Never stores model chain-of-thought or internal reasoning.
    """
    executionId: str = Field(default_factory=_new_id)
    agentName: str
    model: str | None = None    # None in DEV mode
    startedAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: datetime | None = None
    toolCalls: list[ToolCall] = Field(default_factory=list)
    resultStatus: str = "PENDING"
    errorCode: str | None = None
    correlationId: str = Field(default_factory=_new_id)
    evidenceRefs: list[str] = Field(default_factory=list)
    mode: AgentMode = AgentMode.DEV


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard + reports
# ─────────────────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    """Calculated from actual state — never hardcoded."""
    shootDayId: str
    plannedShotCount: int
    completedShotCount: int
    failedShotCount: int
    plannedSceneCount: int
    completedSceneCount: int
    partialSceneCount: int
    blockedSceneCount: int
    atRiskCount: int
    openContinuityAlerts: int
    openCoverageAlerts: int
    pendingProposals: int
    totalDelayMinutes: int
    estimatedMinutesRecovered: int
    agentMode: AgentMode
    partnerStatus: str


class WrapReport(BaseModel):
    """End-of-day report calculated from actual state."""
    reportId: str = Field(default_factory=_new_id)
    shootDayId: str
    productionId: str
    generatedAt: datetime = Field(default_factory=datetime.utcnow)
    plannedShotCount: int
    completedShotCount: int
    failedShotCount: int
    skippedShotCount: int
    plannedSceneCount: int
    completedSceneCount: int
    partialSceneCount: int
    incompleteShotIds: list[str]
    incompleteSceneIds: list[str]
    openCoverageAlerts: list[str]
    resolvedContinuityAlerts: list[str]
    openContinuityAlerts: list[str]
    totalDelayMinutes: int
    approvedScheduleChangeIds: list[str]
    estimatedMinutesRecovered: int
    activeRiskIds: list[str]
    resolvedRiskIds: list[str]
    nextDayPriorities: list[str]

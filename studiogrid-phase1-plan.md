# StudioGrid AI вЂ” Phase 1 Implementation Plan
## Milestone: STUDIOGRID_AI_PRODUCTION_CONTROL_MVP_1

**Status:** APPROVED вЂ” ready for implementation
**Approved by user:** APPROVE STUDIOGRID PLAN
**Mode required:** Agent (for file creation and command execution)

---

## Top-Level Overview

Implement the complete Phase 1 foundation of StudioGrid AI вЂ” an AI production control room
for film shoots. Phase 1 establishes all structural, domain, and tool-contract layers so that
Phase 2 can plug in real Gemini + Agent Builder without rewriting business logic.

Phase 1 does NOT fake AI. The UI shows `DEV MODE вЂ” AI NOT CONNECTED` explicitly.
All dashboard counts are calculated from the LAST LIGHT dataset state, never hardcoded.

---

## Sub-Task 1 вЂ” Repository Scaffold

**Intent:** Create the clean project structure, root config files, and documentation stubs.

**Expected Outcomes:**
- All directories exist
- `.gitignore` covers Python, Node, .env files, Google credential JSON files
- `.env.example` shows all variables with comments, no real values
- `LICENSE` is MIT
- `SECURITY.md` describes the security model
- `README.md` (English) exists with full content
- `README.ru.md` (Russian) exists with full content
- `ARCHITECTURE.md` exists
- `docs/IBM_BOB_DEVELOPMENT_LOG.md` exists
- `docs/evidence/README.md` exists
- `docs/adr/` has 3 ADR files

**Todo List:**

1. Create `.gitignore` with entries for: Python cache, venv, Node modules, .next, .env*, .env.local, service-account*.json, gcloud-*.json, application_default_credentials.json, *.log, .DS_Store, coverage/
2. Create `.env.example` with commented variables (APP_ENV, API_HOST, API_PORT, CORS_ORIGINS, GOOGLE_CLOUD_PROJECT commented out, GEMINI_MODEL commented out, PARTNER_SERVICE commented out, NEXT_PUBLIC_API_URL, NEXT_PUBLIC_APP_ENV)
3. Create `LICENSE` вЂ” MIT License, copyright 2026 StudioGrid AI Contributors
4. Create `SECURITY.md` вЂ” security policy, trust boundaries, secrets policy, human approval gates list
5. Create `README.md` вЂ” full English documentation (see content spec below)
6. Create `README.ru.md` вЂ” full Russian documentation
7. Create `ARCHITECTURE.md` вЂ” architecture overview referencing the plan
8. Create `docs/IBM_BOB_DEVELOPMENT_LOG.md` вЂ” real-time log, first entry for Phase 1
9. Create `docs/evidence/README.md` вЂ” evidence index
10. Create `docs/adr/001-event-driven-state.md`
11. Create `docs/adr/002-agent-interfaces.md`
12. Create `docs/adr/003-human-approval-gates.md`

**README.md content spec:**
```
# StudioGrid AI

An AI production control room for film shoots.

## What StudioGrid AI Is
AI-powered dispatch system for film production. Continuously tracks planned vs actual
shooting state, detects problems, forecasts consequences, and proposes next best actions.

Not a chatbot. Not a script generator. Not a film generator. A coordination layer.

## The Problem
Film shoots lose time and money when actors are delayed, locations become unavailable,
coverage is incomplete, or continuity errors go unnoticed until editing. Production teams
need real-time intelligent coordination, not just spreadsheets.

## Why It Matters
A single day of principal photography for a feature film can cost $100,000+.
Intelligent coordination that recovers even 30 minutes per day compounds across the schedule.

## Multi-Agent Architecture
- PRODUCTION_ORCHESTRATOR вЂ” coordinates all agents
- SCRIPT_BREAKDOWN_AGENT вЂ” parses production package into typed domain model
- SCHEDULE_AGENT вЂ” detects conflicts, proposes rescheduling
- COVERAGE_AGENT вЂ” tracks planned vs completed shots
- CONTINUITY_AGENT вЂ” detects continuity conflicts between shots
- PRODUCTION_RISK_AGENT вЂ” aggregates and prioritizes risks
- WRAP_REPORT_AGENT вЂ” generates end-of-day report from actual state

## Google Cloud Architecture
- Gemini: AI inference for all agents (Phase 2)
- Google Cloud Agent Builder: Official agent runtime (Phase 2)
- Cloud Run: FastAPI tool server + Next.js frontend
- Firestore: Production state storage (Phase 2)
- Cloud Logging: Structured audit trail
- Secret Manager: Partner credentials only
- Authentication: Application Default Credentials, no key files

## Human Approval
All schedule changes, continuity overrides, and risk resolutions require
explicit human approval. AI proposes; humans decide.

## Security
- Agents never access Firestore directly
- All mutations: schema validation в†’ authorization в†’ approval gate в†’ audit log
- No secrets in code or Git
- ADC authentication, no key files

## Local Development
See PHASE_2_REQUIRED_USER_ACTIONS in the milestone report for setup instructions.

For Phase 1 (no Google Cloud required):
  cd services/api && pip install -r requirements.txt && uvicorn main:app --reload
  cd apps/web && npm install && npm run dev

## Tests
  cd services/api && pytest
  cd apps/web && npm test

## IBM Bob Usage
This project is built using IBM Bob. See docs/IBM_BOB_DEVELOPMENT_LOG.md.

## Partner Integration
Status: NOT_CONFIGURED pending official contest partner runtime confirmation.
See docs/adr/004-partner-integration.md (created when requirements confirmed).

## Demo
LAST LIGHT вЂ” a fully original synthetic film production package.
Demo scenario: 08:00 shoot day start through end-of-day wrap.

## Contest Compliance
- Real Gemini + Agent Builder: Phase 2
- IBM Bob development evidence: docs/IBM_BOB_DEVELOPMENT_LOG.md
- No third-party AI models (OpenAI, Anthropic, etc.)
- No secrets in Git
- Human approval gates enforced

## Known Limitations (Phase 1)
- AI not connected (DEV MODE)
- Firestore not connected (in-memory store)
- Partner integration not configured
- Single production (LAST LIGHT) only
```

**Status:** [ ] pending

---

## Sub-Task 2 вЂ” Domain Model (Python)

**Intent:** Define all core domain entities as Pydantic models with strict typing.
These become the single source of truth for all backend validation.

**Expected Outcomes:**
- `services/api/domain/enums.py` вЂ” all enums
- `services/api/domain/models.py` вЂ” all Pydantic domain models
- `services/api/domain/events.py` вЂ” ProductionEvent + EventType
- All models have required fields, no Optional without default
- Models enforce the FACT/INFERENCE/RECOMMENDATION/HUMAN_DECISION separation

**Files to create:**

### `services/api/domain/enums.py`

```python
from enum import Enum

class ProductionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WRAPPED = "WRAPPED"
    ARCHIVED = "ARCHIVED"

class ShootDayStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    WRAPPED = "WRAPPED"

class SceneStatus(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"

class ShotStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class ShotType(str, Enum):
    MASTER = "MASTER"
    CLOSE_UP = "CLOSE_UP"
    INSERT = "INSERT"
    OTS = "OTS"
    TWO_SHOT = "TWO_SHOT"
    ECU = "ECU"
    WIDE = "WIDE"
    POV = "POV"
    CUTAWAY = "CUTAWAY"

class ActorStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DELAYED = "DELAYED"
    UNAVAILABLE = "UNAVAILABLE"
    WRAPPED = "WRAPPED"

class LocationStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    WARNING = "WARNING"
    UNAVAILABLE = "UNAVAILABLE"

class LocationType(str, Enum):
    INT = "INT"
    EXT = "EXT"

class PropStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    IN_USE = "IN_USE"

class TimeOfDay(str, Enum):
    DAY = "DAY"
    GOLDEN_HOUR = "GOLDEN_HOUR"
    NIGHT = "NIGHT"
    INT = "INT"

class DependencyType(str, Enum):
    MUST_PRECEDE = "MUST_PRECEDE"
    SAME_DAY = "SAME_DAY"
    CONTINUITY_REQUIRED = "CONTINUITY_REQUIRED"

class FactSource(str, Enum):
    SCRIPT = "SCRIPT"
    CREW_REPORT = "CREW_REPORT"
    AI_INFERENCE = "AI_INFERENCE"

class AlertType(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    RECOMMENDATION = "RECOMMENDATION"

class AlertStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    OVERRIDDEN = "OVERRIDDEN"

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ProposalCategory(str, Enum):
    FACT = "FACT"
    INFERENCE = "INFERENCE"
    RECOMMENDATION = "RECOMMENDATION"

class RiskStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    ACCEPTED = "ACCEPTED"

class OriginType(str, Enum):
    HUMAN = "HUMAN"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"

class AgentMode(str, Enum):
    DEV = "DEV"
    PRODUCTION = "PRODUCTION"

class PartnerIntegrationStatus(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTED = "CONNECTED"

class EventType(str, Enum):
    SHOOT_DAY_STARTED = "SHOOT_DAY_STARTED"
    SHOOT_DAY_WRAPPED = "SHOOT_DAY_WRAPPED"
    SHOT_STARTED = "SHOT_STARTED"
    SHOT_COMPLETED = "SHOT_COMPLETED"
    SHOT_FAILED = "SHOT_FAILED"
    SHOT_SKIPPED = "SHOT_SKIPPED"
    ACTOR_DELAYED = "ACTOR_DELAYED"
    ACTOR_AVAILABLE = "ACTOR_AVAILABLE"
    LOCATION_WARNING = "LOCATION_WARNING"
    LOCATION_UNAVAILABLE = "LOCATION_UNAVAILABLE"
    LOCATION_AVAILABLE = "LOCATION_AVAILABLE"
    PROP_UNAVAILABLE = "PROP_UNAVAILABLE"
    PROP_AVAILABLE = "PROP_AVAILABLE"
    CONTINUITY_FACT_RECORDED = "CONTINUITY_FACT_RECORDED"
    CONTINUITY_ALERT_CREATED = "CONTINUITY_ALERT_CREATED"
    CONTINUITY_ALERT_RESOLVED = "CONTINUITY_ALERT_RESOLVED"
    COVERAGE_ALERT_CREATED = "COVERAGE_ALERT_CREATED"
    COVERAGE_ALERT_RESOLVED = "COVERAGE_ALERT_RESOLVED"
    SCHEDULE_PROPOSAL_CREATED = "SCHEDULE_PROPOSAL_CREATED"
    SCHEDULE_PROPOSAL_APPROVED = "SCHEDULE_PROPOSAL_APPROVED"
    SCHEDULE_PROPOSAL_REJECTED = "SCHEDULE_PROPOSAL_REJECTED"
    RISK_CREATED = "RISK_CREATED"
    RISK_UPDATED = "RISK_UPDATED"
    RISK_RESOLVED = "RISK_RESOLVED"
    TOOL_CALLED = "TOOL_CALLED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
```

### `services/api/domain/models.py`

All Pydantic v2 models. Key models:

```python
from __future__ import annotations
from datetime import datetime, date, time
from typing import Any
from pydantic import BaseModel, Field
from .enums import *
import uuid

def new_id() -> str:
    return str(uuid.uuid4())

class WardrobeNote(BaseModel):
    item: str
    description: str
    characterId: str

class SceneDependency(BaseModel):
    dependencyId: str = Field(default_factory=new_id)
    sceneId: str
    dependsOnSceneId: str
    type: DependencyType
    reason: str

class ContinuityFact(BaseModel):
    factId: str = Field(default_factory=new_id)
    sceneId: str
    shotId: str | None = None
    characterId: str | None = None
    propId: str | None = None
    attribute: str
    value: str
    recordedAt: datetime = Field(default_factory=datetime.utcnow)
    source: FactSource

class Evidence(BaseModel):
    evidenceId: str = Field(default_factory=new_id)
    type: str
    description: str
    factIds: list[str] = Field(default_factory=list)
    shotIds: list[str] = Field(default_factory=list)

class ContinuityAlert(BaseModel):
    alertId: str = Field(default_factory=new_id)
    alertType: AlertType
    severity: Severity
    factA: ContinuityFact
    factB: ContinuityFact
    description: str
    status: AlertStatus = AlertStatus.OPEN
    resolution: str | None = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    resolvedAt: datetime | None = None

class CoverageAlert(BaseModel):
    alertId: str = Field(default_factory=new_id)
    sceneId: str
    missingShotIds: list[str]
    severity: Severity
    description: str
    status: AlertStatus = AlertStatus.OPEN
    resolution: str | None = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class ProposalRisk(BaseModel):
    description: str
    severity: Severity

class ScheduleChange(BaseModel):
    changeType: str
    sceneId: str
    fromPosition: int | None = None
    toPosition: int | None = None
    reason: str

class ScheduleProposal(BaseModel):
    proposalId: str = Field(default_factory=new_id)
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
    resolvedBy: str | None = None  # HUMAN_DECISION

class Risk(BaseModel):
    riskId: str = Field(default_factory=new_id)
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

class ToolCall(BaseModel):
    toolCallId: str = Field(default_factory=new_id)
    toolName: str
    callerType: OriginType
    callerId: str
    arguments: dict[str, Any]
    result: dict[str, Any] | None = None
    status: str = "PENDING"
    calledAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: datetime | None = None

class AgentExecution(BaseModel):
    executionId: str = Field(default_factory=new_id)
    agentName: str
    model: str | None = None
    startedAt: datetime = Field(default_factory=datetime.utcnow)
    completedAt: datetime | None = None
    toolCalls: list[ToolCall] = Field(default_factory=list)
    resultStatus: str = "PENDING"
    errorCode: str | None = None
    correlationId: str
    evidenceRefs: list[str] = Field(default_factory=list)
    mode: AgentMode = AgentMode.DEV

class Actor(BaseModel):
    actorId: str
    name: str
    characterName: str
    availableFromTime: str   # "HH:MM" format
    availableUntilTime: str
    currentStatus: ActorStatus = ActorStatus.AVAILABLE
    delayMinutes: int = 0

class Location(BaseModel):
    locationId: str
    name: str
    locationType: LocationType
    availableFromTime: str
    availableUntilTime: str
    daylightConstraint: bool
    daylightDeadlineTime: str | None = None
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
    shotCode: str
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
    plannedStartTime: str
    estimatedDurationMinutes: int

class ShootDay(BaseModel):
    shootDayId: str
    productionId: str
    date: str   # ISO date string
    status: ShootDayStatus = ShootDayStatus.PLANNED
    scheduledScenes: list[ScheduledScene] = Field(default_factory=list)

class Production(BaseModel):
    productionId: str
    title: str
    status: ProductionStatus = ProductionStatus.ACTIVE
    shootDays: list[ShootDay] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class WrapReport(BaseModel):
    reportId: str = Field(default_factory=new_id)
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
    approvedScheduleChanges: list[str]
    estimatedMinutesRecovered: int
    activeRisks: list[str]
    resolvedRisks: list[str]
    nextDayPriorities: list[str]
```

### `services/api/domain/events.py`

```python
from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from .enums import EventType, OriginType
import uuid

def new_id() -> str:
    return str(uuid.uuid4())

class ProductionEvent(BaseModel):
    eventId: str = Field(default_factory=new_id)
    productionId: str
    shootDayId: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    originType: OriginType
    originId: str
    type: EventType
    payload: dict[str, Any]
    source: str
    correlationId: str = Field(default_factory=new_id)
```

**Status:** [ ] pending

---

## Sub-Task 3 вЂ” Event System

**Intent:** Implement LocalEventBus for development, with interface ready for
Cloud Pub/Sub replacement in Phase 2.

**Files to create:**

### `services/api/core/event_bus.py`

```python
from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Awaitable
from ..domain.events import ProductionEvent
from ..domain.enums import EventType

EventHandler = Callable[[ProductionEvent], Awaitable[None]]

class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: ProductionEvent) -> None: ...

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None: ...

    @abstractmethod
    def subscribe_all(self, handler: EventHandler) -> None: ...


class LocalEventBus(EventBus):
    """In-process event bus for Phase 1 development and testing."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []
        self._event_log: list[ProductionEvent] = []

    async def publish(self, event: ProductionEvent) -> None:
        self._event_log.append(event)
        handlers = self._handlers.get(event.type, []) + self._wildcard_handlers
        await asyncio.gather(*[h(event) for h in handlers], return_exceptions=True)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._wildcard_handlers.append(handler)

    def get_event_log(self) -> list[ProductionEvent]:
        return list(self._event_log)

    def clear(self) -> None:
        self._event_log.clear()
        self._handlers.clear()
        self._wildcard_handlers.clear()
```

**Status:** [ ] pending

---

## Sub-Task 4 вЂ” LAST LIGHT Dataset

**Intent:** Create the complete original synthetic production package for film "LAST LIGHT".
All names, characters, locations are fictional. No real IP used.

**File:** `demo/last_light/production_package.json`

Content structure: Production, Actors (4), Locations (3), Props (5), Scenes (10), Shots (22+),
SceneDependencies, ContinuityFacts (with built-in conflict for demo), ShootingSchedule.

Key data:

Actors:
- ACT_01: Marcus Elland, plays Thomas Hale (elderly), 07:00-19:00
- ACT_02: Maya Reed, plays Elara, 09:00-17:00 (KEY: delayed in demo at 10:12)
- ACT_03: Daniel Osei, plays Young Thomas, 08:00-14:00
- ACT_04: Sona Varga, plays Elena Hale (voice/shadow), 10:00-13:00

Locations:
- LOC_01: Hale House Main Room, INT, 07:00-20:00, no daylight constraint
- LOC_02: Hale House Garden, EXT, 08:00-18:00, daylight constraint deadline 17:00
- LOC_03: Hale House Attic, INT, 09:00-16:00, no daylight constraint

Scenes (10): SC_01 through SC_10 with dependencies as specified in plan
Shots (22): distributed across scenes, various shot types

Built-in continuity conflict for demo:
- FACT_A: SC_05 shot SC05_OTS_MAYA вЂ” Maya holds notebook in LEFT hand (attribute: notebook_hand, value: LEFT)
- FACT_B: SC_06 shot SC06_ECU_NOTEBOOK вЂ” notebook recorded on RIGHT side of table (attribute: notebook_position, value: RIGHT_SIDE)

**File:** `demo/scenarios/demo_day_01.json`

Event sequence for the demo:
- 08:00 SHOOT_DAY_STARTED
- 08:15 SHOT_STARTED SC01_MASTER
- 08:40 SHOT_COMPLETED SC01_MASTER
- 08:45 SHOT_STARTED SC01_CU_THOMAS
- 09:00 SHOT_COMPLETED SC01_CU_THOMAS
- 09:10 SHOT_STARTED SC02_MASTER
- 09:35 SHOT_COMPLETED SC02_MASTER
- 09:40 SHOT_STARTED SC03_MASTER
- 10:00 SHOT_COMPLETED SC03_MASTER
- 10:05 SHOT_STARTED SC03_CU_THOMAS
- 10:10 SHOT_COMPLETED SC03_CU_THOMAS
- 10:12 ACTOR_DELAYED ACT_02 (Maya Reed, 45 minutes) вЂ” TRIGGERS SCHEDULE AGENT
- (Schedule proposal created: move SC_08 before SC_05 вЂ” SC_08 needs only ACT_03+ACT_04, both present)
- (Human approves proposal)
- 10:20 SHOT_STARTED SC08_MASTER
- 10:45 SHOT_COMPLETED SC08_MASTER
- 10:50 SHOT_STARTED SC08_CU_YOUNG
- 11:05 SHOT_COMPLETED SC08_CU_YOUNG
- 11:08 COVERAGE_ALERT SC_08 missing SC08_CU_ELENA and SC08_INSERT_PHOTO вЂ” TRIGGERS COVERAGE AGENT
  (ACT_04 availability ends 13:00, flag as risk)
- 11:15 ACTOR_AVAILABLE ACT_02 (delay resolved)
- 11:20 CONTINUITY_FACT_RECORDED SC05 notebook=LEFT_HAND
- 11:25 CONTINUITY_FACT_RECORDED SC06 notebook=RIGHT_SIDE
- (CONTINUITY_ALERT created by Continuity Agent)
- ... rest of shots ...
- 18:00 SHOOT_DAY_WRAPPED
- (Wrap report generated from real state)

**Status:** [ ] pending

---

## Sub-Task 5 вЂ” Typed Tool Contracts

**Intent:** Define all tool signatures, authorization metadata, and approval gate declarations.
These are the ONLY way agents may mutate state.

**File:** `services/api/tools/contracts.py`

Each tool has:
- name (str)
- description (str)
- input schema (Pydantic model)
- output schema (Pydantic model)
- allowed_callers: list[OriginType]
- requires_approval: bool
- approval_reason: str | None

Tools list:
```
record_shot_started(shotId, shootDayId, startedAt) в†’ ShotStartedResult
record_shot_completed(shotId, shootDayId, completedAt, actualDurationMinutes) в†’ ShotCompletedResult
record_shot_failed(shotId, shootDayId, reason) в†’ ShotFailedResult

report_actor_delay(actorId, delayMinutes, reason, shootDayId) в†’ ActorDelayResult
report_actor_available(actorId, shootDayId) в†’ ActorAvailableResult

record_location_warning(locationId, warning, shootDayId) в†’ LocationWarningResult
record_location_unavailable(locationId, reason, shootDayId) в†’ LocationUnavailableResult

record_continuity_fact(sceneId, shotId, attribute, value, source, characterId?, propId?) в†’ ContinuityFact
create_continuity_alert(factAId, factBId, description, severity) в†’ ContinuityAlert  [AGENT only]
resolve_continuity_alert(alertId, resolution, resolvedBy) в†’ ContinuityAlert  [HUMAN approval required]

create_coverage_alert(sceneId, missingShotIds, severity, description) в†’ CoverageAlert  [AGENT only]
resolve_coverage_alert(alertId, resolution) в†’ CoverageAlert

create_schedule_proposal(shootDayId, proposedChanges, why, evidence, expectedBenefitMinutes, affectedScenes, risks, confidence) в†’ ScheduleProposal  [AGENT only]
approve_schedule_proposal(proposalId, approvedBy) в†’ ScheduleProposal  [HUMAN only, approval gate]
reject_schedule_proposal(proposalId, rejectedBy, reason) в†’ ScheduleProposal  [HUMAN only]

create_risk(severity, reason, evidence, affectedScenes, suggestedAction, confidence) в†’ Risk  [AGENT only]
update_risk(riskId, severity?, status?, suggestedAction?) в†’ Risk
resolve_risk(riskId, resolvedBy, resolution) в†’ Risk  [HUMAN approval required for HIGH/CRITICAL]

wrap_shoot_day(shootDayId, wrappedBy) в†’ WrapReport  [HUMAN only]
generate_wrap_report(shootDayId) в†’ WrapReport
```

**File:** `services/api/core/tool_registry.py`

- Registers all tools with their contracts
- `call_tool(name, caller_type, caller_id, args, correlation_id)` method
- Validates caller is in allowed_callers
- Checks approval gate if requires_approval
- Records ToolCall event
- Returns typed result

**File:** `services/api/core/approval_gates.py`

```python
class ApprovalRequiredError(Exception):
    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason

class ApprovalGate:
    PROTECTED_TOOLS = {
        "approve_schedule_proposal": "Schedule changes require human approval",
        "resolve_continuity_alert": "Continuity alert override requires human approval",
        "resolve_risk": "HIGH/CRITICAL risk resolution requires human approval",
        "wrap_shoot_day": "Wrapping shoot day requires human confirmation",
    }

    @classmethod
    def check(cls, tool_name: str, caller_type: OriginType) -> None:
        if tool_name in cls.PROTECTED_TOOLS and caller_type != OriginType.HUMAN:
            raise ApprovalRequiredError(tool_name, cls.PROTECTED_TOOLS[tool_name])
```

**Status:** [ ] pending

---

## Sub-Task 6 вЂ” In-Memory State Manager + Firestore Boundary

**Intent:** Implement LocalStateStore for Phase 1. Define Firestore interface boundary
for Phase 2 without implementing it.

**File:** `services/api/db/local_store.py`

In-memory store that holds:
- production: Production
- actors: dict[str, Actor]
- locations: dict[str, Location]
- props: dict[str, Prop]
- scenes: dict[str, Scene]
- shots: dict[str, Shot]
- events: list[ProductionEvent]
- proposals: dict[str, ScheduleProposal]
- continuity_alerts: dict[str, ContinuityAlert]
- coverage_alerts: dict[str, CoverageAlert]
- risks: dict[str, Risk]

Methods:
- get_production_state() в†’ full snapshot
- upsert_scene(scene), upsert_shot(shot), upsert_actor(actor), etc.
- add_event(event)
- get_events() в†’ list[ProductionEvent]
- compute_coverage(scene_id) в†’ CoverageStats
- compute_scene_status(scene_id) в†’ SceneStatus (based on shots + dependencies)
- compute_dashboard_stats() в†’ DashboardStats (never hardcoded)
- load_from_production_package(data: dict) в†’ None

**File:** `services/api/db/firestore_client.py`

```python
# Phase 2 вЂ” Firestore integration boundary
# This file is a placeholder defining the interface.
# Implementation uses Application Default Credentials (ADC).
# No service account JSON key files.

class FirestoreStateStore:
    """
    Phase 2 Firestore implementation.
    Activated when GOOGLE_CLOUD_PROJECT is set in environment.
    Uses ADC вЂ” no key files required.
    """
    def __init__(self):
        raise NotImplementedError(
            "FirestoreStateStore is a Phase 2 component. "
            "Set GOOGLE_CLOUD_PROJECT and ensure ADC is configured."
        )
```

**Status:** [ ] pending

---

## Sub-Task 7 вЂ” Agent Interfaces

**Intent:** Define abstract base classes for all agents. Phase 1 implements
deterministic logic behind these interfaces. Phase 2 replaces internals with
real Gemini / Agent Builder.

**File:** `agents/interfaces.py`

```python
from abc import ABC, abstractmethod
from services.api.domain.events import ProductionEvent
from services.api.domain.enums import AgentMode

class BaseAgent(ABC):
    mode: AgentMode = AgentMode.DEV

    @property
    @abstractmethod
    def agent_name(self) -> str: ...

    @abstractmethod
    async def handle_event(self, event: ProductionEvent) -> None: ...

    @abstractmethod
    def get_mode(self) -> AgentMode: ...
```

**File:** `agents/partner/integration_port.py`

```python
from abc import ABC, abstractmethod
from services.api.domain.enums import PartnerIntegrationStatus
from services.api.domain.events import ProductionEvent

class PartnerIntegrationPort(ABC):
    @property
    @abstractmethod
    def status(self) -> PartnerIntegrationStatus: ...

    @abstractmethod
    async def publish_event(self, event: ProductionEvent) -> None: ...

    @abstractmethod
    async def health_check(self) -> PartnerIntegrationStatus: ...
```

**File:** `agents/partner/null_port.py`

```python
class NullPartnerPort(PartnerIntegrationPort):
    """
    Default implementation. Does nothing.
    Active until official partner requirements are confirmed.
    Status: NOT_CONFIGURED
    """
    @property
    def status(self) -> PartnerIntegrationStatus:
        return PartnerIntegrationStatus.NOT_CONFIGURED

    async def publish_event(self, event: ProductionEvent) -> None:
        pass  # intentional no-op

    async def health_check(self) -> PartnerIntegrationStatus:
        return PartnerIntegrationStatus.NOT_CONFIGURED
```

**File:** `agents/google_adk/adk_adapter.py`

```python
"""
Google Cloud Agent Builder / ADK Integration Boundary.

Phase 1: This module is a placeholder. Real implementation added in Phase 2
after verifying current official Agent Builder SDK and API.

See: docs/adr/002-agent-interfaces.md
"""

AGENT_BUILDER_STATUS = "NOT_CONNECTED"
GEMINI_STATUS = "NOT_CONNECTED"

class AgentBuilderAdapter:
    """
    Phase 2: Will wrap real Google Cloud Agent Builder runtime.
    Implementation must verify current official SDK before coding.
    """
    def __init__(self):
        raise NotImplementedError(
            "AgentBuilderAdapter is a Phase 2 component. "
            "Verify current official Google Cloud Agent Builder SDK before implementing."
        )
```

**File:** `agents/google_adk/README.md`

Content:
```
# Google Cloud Agent Builder Integration

## Status: Phase 2

This directory will contain the real Google Cloud Agent Builder / Gemini integration.

## Requirements Before Implementation

1. Verify current official Agent Builder SDK version (API changes frequently)
2. Confirm GOOGLE_CLOUD_PROJECT is set
3. Ensure Application Default Credentials are configured:
   gcloud auth application-default login
4. Enable required APIs:
   - Vertex AI API
   - Agent Builder API (Dialogflow CX / Vertex AI Agent Builder)
5. Assign IAM roles:
   - roles/aiplatform.user (for Gemini)
   - roles/datastore.user (for Firestore)

## Authentication

NO service account JSON key files.
Use Application Default Credentials (ADC) exclusively.

## Phase 2 Implementation

See docs/adr/005-agent-builder-integration.md (created in Phase 2).
```

**File:** `agents/schedule_agent.py` (deterministic Phase 1 implementation)

Logic:
- Handles ACTOR_DELAYED event
- Finds scenes that require the delayed actor
- Finds alternative scenes that can be shot without the delayed actor
- Checks: actor availability, location availability, scene dependencies, daylight constraints
- Creates ScheduleProposal via tool call

**File:** `agents/coverage_agent.py` (deterministic Phase 1)

Logic:
- Handles SHOT_COMPLETED event
- Checks if scene has all required shots complete
- If missing shots found: creates CoverageAlert via tool call

**File:** `agents/continuity_agent.py` (deterministic Phase 1)

Logic:
- Handles CONTINUITY_FACT_RECORDED event
- Looks for conflicting facts (same scene/character/prop, conflicting attribute values)
- Creates ContinuityAlert (type=INFERENCE, not FACT) via tool call

**File:** `agents/risk_agent.py` (deterministic Phase 1)

Logic:
- Handles all events
- Maintains risk registry
- Creates/updates risks based on: coverage alerts, continuity alerts, actor delays, location warnings

**File:** `agents/wrap_report_agent.py` (deterministic, pure calculation)

Logic:
- Handles SHOOT_DAY_WRAPPED event
- Calculates all stats from actual state (never hardcoded)
- Calls generate_wrap_report tool

**File:** `agents/orchestrator.py`

Coordinates all agents. Receives events from EventBus. Routes to appropriate agents.
Shows AgentMode.DEV in all executions.

**Status:** [ ] pending

---

## Sub-Task 8 вЂ” FastAPI Tool Server

**Intent:** Build the complete FastAPI backend with all routers, Tool Registry,
and SSE endpoint.

**Files:**

`services/api/main.py` вЂ” FastAPI app, CORS, router registration, startup event (loads LAST LIGHT)

`services/api/config.py` вЂ” Settings from env vars using pydantic-settings

`services/api/routers/events.py` вЂ” POST /events/* endpoints + GET /events/stream (SSE)

`services/api/routers/shots.py` вЂ” GET/POST shot operations

`services/api/routers/scenes.py` вЂ” GET scene list, GET scene detail

`services/api/routers/schedule.py` вЂ” GET schedule, GET proposals, POST approve/reject proposal

`services/api/routers/continuity.py` вЂ” GET facts, GET alerts, POST resolve alert

`services/api/routers/risks.py` вЂ” GET risks, POST resolve risk

`services/api/routers/report.py` вЂ” GET wrap report, POST wrap day

`services/api/routers/production.py` вЂ” GET production state, GET dashboard stats

`services/api/routers/tools.py` вЂ” POST /tools/call (generic tool endpoint)

All routers use Pydantic models for request/response validation.
All mutations go through Tool Registry.

**pyproject.toml** dependencies:
- fastapi>=0.111.0
- uvicorn[standard]>=0.29.0
- pydantic>=2.7.0
- pydantic-settings>=2.2.0
- python-dotenv>=1.0.0
- pytest>=8.0.0
- httpx>=0.27.0 (for tests)
- pytest-asyncio>=0.23.0

**Status:** [ ] pending

---

## Sub-Task 9 вЂ” Next.js Frontend

**Intent:** Build the minimal dashboard with DEV MODE indicator, EN/RU localization,
and all Phase 1 screens. All counts calculated from API, never hardcoded.

**Tech stack:**
- Next.js 14+ (App Router)
- TypeScript
- next-intl for i18n
- Tailwind CSS (utility-first, professional dark theme)
- No shadcn, no heavy component library (keep it clean)

**package.json** dependencies:
- next@latest
- react@latest
- react-dom@latest
- next-intl@latest
- tailwindcss
- typescript
- @types/react
- @types/node

**i18n files:**

`apps/web/src/i18n/en.json`:
All English strings. Keys:
- nav.dashboard, nav.timeline, nav.sceneBoard, nav.coverage, nav.continuity, nav.schedule, nav.report
- status.planned, status.ready, status.inProgress, status.partial, status.complete, status.blocked
- status.available, status.delayed, status.unavailable
- shot.planned, shot.inProgress, shot.complete, shot.failed, shot.skipped
- alert.open, alert.underReview, alert.resolved, alert.overridden
- severity.low, severity.medium, severity.high, severity.critical
- proposal.pending, proposal.approved, proposal.rejected
- proposal.approve, proposal.reject, proposal.explain
- proposal.why, proposal.evidence, proposal.expectedBenefit, proposal.affectedScenes
- proposal.risks, proposal.confidence
- devMode.banner (= "DEV MODE вЂ” AI NOT CONNECTED")
- devMode.description
- partner.status, partner.notConfigured, partner.notConnected, partner.connected
- dashboard.title, dashboard.scenesPlanned, dashboard.scenesCompleted
- dashboard.shotsPlanned, dashboard.shotsCompleted, dashboard.atRisk
- dashboard.continuityAlerts, dashboard.coverageAlerts, dashboard.scheduleDelay
- dashboard.estimatedRecovered, dashboard.activeProposals
- common.approve, common.reject, common.explain, common.resolve, common.override
- common.loading, common.error, common.noData
- report.title, report.planned, report.completed, report.missing, etc.
- errors.approvalRequired, errors.toolNotFound, errors.invalidState

`apps/web/src/i18n/ru.json`:
Complete Russian translations for ALL same keys. No missing keys allowed.

**TypeScript types** (`apps/web/src/lib/types/`):
- Generated from domain model (manually typed in Phase 1, auto-generated in Phase 2)
- Mirror Python domain models exactly
- All enums mirrored as TypeScript const enums

**Key screens:**

`/[locale]/dashboard` вЂ” Production Dashboard
- DEV MODE banner (always visible in Phase 1)
- Stats grid: scenes planned/completed, shots planned/completed, at risk, alerts, delay, recovered
- All numbers from API /production/dashboard-stats
- Active proposals section
- Partner integration status badge

`/[locale]/schedule` вЂ” Schedule Control
- Current schedule (ordered scenes with times)
- Pending proposals section
- Each proposal shows: WHY, EVIDENCE, EXPECTED BENEFIT, AFFECTED SCENES, RISKS, CONFIDENCE
- APPROVE / REJECT / EXPLAIN buttons
- Approval confirmation dialog

`/[locale]/coverage` вЂ” Shot Coverage
- Per-scene breakdown: planned shots vs completed shots
- Missing shots highlighted
- Coverage alerts

`/[locale]/continuity` вЂ” Continuity Board
- Facts list with scene/character/attribute
- Alerts with INFERENCE label (never FACT unless it is one)
- APPROVE OVERRIDE button with confirmation

`/[locale]/scene-board` вЂ” Scene Board
- Grid of scenes with status badges
- Scene detail: shots, characters, location, dependencies

`/[locale]/timeline` вЂ” Live Timeline
- Chronological event stream from SSE
- Event type badges

`/[locale]/report` вЂ” End-of-Day Report
- Generated from actual state
- All numbers calculated

**Language switcher:** top-right, EN | RU, persisted in cookie

**Status:** [ ] pending

---

## Sub-Task 10 вЂ” Localization

**Intent:** Ensure EN and RU are complete, all UI strings go through i18n,
no hardcoded user-visible strings anywhere in components.

**Rules enforced:**
- All text in components uses `t('key')` from next-intl
- No string literals in JSX except inside i18n files
- Internal enums/API fields always English
- AI receives `requestedOutputLanguage` parameter

**Test:**
- Parse both JSON files, assert identical key sets
- Assert no key is an empty string in either locale

**Status:** [ ] pending

---

## Sub-Task 11 вЂ” Phase 1 Unit Tests

**Intent:** Comprehensive test coverage for all Phase 1 logic.

**Backend tests** (`tests/unit/`):

`test_events.py`:
- event created with all required fields
- event ordering preserved
- invalid event type rejected by Pydantic

`test_shot_status.py`:
- valid transitions: PLANNEDв†’IN_PROGRESS, IN_PROGRESSв†’COMPLETE
- invalid transition: PLANNEDв†’COMPLETE raises error
- invalid transition: COMPLETEв†’IN_PROGRESS raises error

`test_scene_status.py`:
- scene blocked when dependency incomplete
- scene ready when all dependencies met
- scene partial when some shots complete

`test_coverage.py`:
- 100% coverage computed correctly
- coverage alert created when required shots missing
- scene not markable COMPLETE with open coverage alert without human approval

`test_schedule_proposal.py`:
- proposal created with all required fields (why, evidence, confidence, affectedScenes)
- approved proposal changes schedule
- rejected proposal does not change schedule
- AGENT cannot call approve_schedule_proposal (ApprovalRequiredError)

`test_actor_delay.py`:
- delay creates ACTOR_DELAYED event with correct payload
- affected scenes computed correctly (scenes requiring delayed actor)
- scenes with no delayed actor remain READY

`test_dependencies.py`:
- scene with unmet dependency is BLOCKED
- dependency chain validation

`test_continuity.py`:
- conflicting facts create INFERENCE alert
- alert cannot be auto-resolved without human
- override requires human approval (ApprovalRequiredError for AGENT)

`test_risk.py`:
- risk created with required fields
- CRITICAL risk resolution by AGENT raises ApprovalRequiredError
- risk status transitions valid

`test_wrap_report.py`:
- report calculated from actual state
- planned vs completed counts match actual data
- never returns hardcoded values (inject state, assert matches)

`test_localization.py`:
- EN and RU have identical key sets
- no empty string values
- no keys contain hardcoded business logic

`test_schemas.py`:
- ProductionEvent schema validates
- ScheduleProposal schema validates
- invalid payload raises ValidationError

`test_tool_authorization.py`:
- AGENT cannot call approve_schedule_proposal
- AGENT cannot call wrap_shoot_day
- HUMAN can call approve_schedule_proposal

`test_approval_gates.py`:
- schedule change without approval raises ApprovalRequiredError
- continuity override without approval raises ApprovalRequiredError
- CRITICAL risk resolution without approval raises ApprovalRequiredError

**Frontend tests** (`apps/web/src/`) using Vitest:

`test_localization.spec.ts`:
- EN and RU JSON files have identical keys
- no empty values

`test_dashboard_stats.spec.ts`:
- DashboardStats computed from mock state (not hardcoded)

`test_proposal_component.spec.ts`:
- Proposal renders WHY, EVIDENCE, CONFIDENCE
- APPROVE button calls approve handler
- REJECT button calls reject handler
- Confirmation dialog shown before approve

**Status:** [ ] pending

---

## Sub-Task 12 вЂ” Git Init + Secret Scan + Commit

**Intent:** Initialize Git, verify no secrets staged, create checkpoint commit.

**Steps:**
1. `git init`
2. `git add -A`
3. Run secret scan: grep staged files for patterns: `api_key`, `private_key`, `password`, `secret`, `token`, `AKIA`, `-----BEGIN`, base64-looking long strings
4. `git diff --cached --check`
5. Verify `.gitignore` is working: `git status` should not show .env files
6. `git commit -m "STUDIOGRID_AI_FOUNDATION_MVP_1"`

**Commit message:**
```
STUDIOGRID_AI_FOUNDATION_MVP_1

Phase 1 implementation of StudioGrid AI production control system.

Includes:
- Domain model (Python Pydantic + TypeScript)
- Event system (EventType, ProductionEvent, LocalEventBus)
- LAST LIGHT original synthetic production dataset
- Typed tool contracts with authorization and approval gates
- FastAPI Tool Server skeleton (all routers, Tool Registry)
- Agent interfaces (BaseAgent, PartnerIntegrationPort, NullPartnerPort)
- Agent Builder boundary (Phase 2 placeholder)
- Deterministic agent implementations (Schedule, Coverage, Continuity, Risk, Wrap)
- Next.js minimal dashboard (DEV MODE вЂ” AI NOT CONNECTED)
- EN + RU localization (complete, no missing keys)
- Phase 1 unit tests (backend pytest + frontend Vitest)
- IBM Bob development log
- ADR documents

No secrets committed. No fake AI. No partner integration fabricated.
Partner status: NOT_CONFIGURED.
AI status: DEV MODE.

Milestone: STUDIOGRID_AI_PRODUCTION_CONTROL_MVP_1
```

**Status:** [ ] pending

---

## Final Validation Checklist

Before reporting completion, verify ALL:

- [ ] `cd services/api && pip install -e ".[dev]" && pytest` вЂ” all tests pass
- [ ] `cd apps/web && npm install && npm run lint` вЂ” no errors
- [ ] `cd apps/web && npm run typecheck` вЂ” no errors
- [ ] `cd apps/web && npm test` вЂ” all tests pass
- [ ] `cd apps/web && npm run build` вЂ” production build succeeds
- [ ] EN and RU locale files have identical key sets
- [ ] No hardcoded strings in any component
- [ ] No credentials anywhere in repo
- [ ] No .env files tracked by git
- [ ] DEV MODE banner visible on dashboard
- [ ] Partner status shows NOT_CONFIGURED
- [ ] git log shows STUDIOGRID_AI_FOUNDATION_MVP_1 commit
- [ ] git status clean

---

## Phase 2 Preparation Notes

Before Phase 2 implementation, the following MUST be confirmed:

1. **Google Cloud Project ID** вЂ” user must create project and provide ID
2. **APIs to enable:**
   - Vertex AI API (`aiplatform.googleapis.com`)
   - Firestore API (`firestore.googleapis.com`)
   - Cloud Run API (`run.googleapis.com`)
   - Cloud Logging API (`logging.googleapis.com`)
   - Cloud Storage API (`storage.googleapis.com`)
   - Secret Manager API (`secretmanager.googleapis.com`)
   - Agent Builder API вЂ” **must verify current product name and API endpoint** as this changes
3. **Authentication:** `gcloud auth application-default login`
4. **IAM roles for Cloud Run service account:**
   - `roles/aiplatform.user`
   - `roles/datastore.user`
   - `roles/logging.logWriter`
   - `roles/storage.objectViewer`
5. **Billing:** Yes, required for Cloud Run, Vertex AI, Firestore
6. **Agent Builder current integration path:** Must verify official docs before writing any SDK code. Do NOT use any API method names from memory. Create ADR 005 before Phase 2 coding.
7. **IBM/partner blocking question:** Does IBM Bob development evidence satisfy partner requirement, or must runtime call a specific IBM service?

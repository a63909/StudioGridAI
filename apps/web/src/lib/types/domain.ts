/**
 * StudioGrid AI — Shared TypeScript Types
 *
 * These mirror the Python Pydantic domain models exactly.
 * Internal field names are always English.
 *
 * Generated reference: services/api/domain/models.py
 */

// ─────────────────────────────────────────────────────────────────────────────
// Enums
// ─────────────────────────────────────────────────────────────────────────────

export const ProductionStatus = {
  ACTIVE: "ACTIVE",
  WRAPPED: "WRAPPED",
  ARCHIVED: "ARCHIVED",
} as const;
export type ProductionStatus = typeof ProductionStatus[keyof typeof ProductionStatus];

export const ShootDayStatus = {
  PLANNED: "PLANNED",
  ACTIVE: "ACTIVE",
  WRAPPED: "WRAPPED",
} as const;
export type ShootDayStatus = typeof ShootDayStatus[keyof typeof ShootDayStatus];

export const SceneStatus = {
  PLANNED: "PLANNED",
  READY: "READY",
  IN_PROGRESS: "IN_PROGRESS",
  PARTIAL: "PARTIAL",
  COMPLETE: "COMPLETE",
  BLOCKED: "BLOCKED",
} as const;
export type SceneStatus = typeof SceneStatus[keyof typeof SceneStatus];

export const ShotStatus = {
  PLANNED: "PLANNED",
  IN_PROGRESS: "IN_PROGRESS",
  COMPLETE: "COMPLETE",
  FAILED: "FAILED",
  SKIPPED: "SKIPPED",
} as const;
export type ShotStatus = typeof ShotStatus[keyof typeof ShotStatus];

export const ShotType = {
  MASTER: "MASTER",
  CLOSE_UP: "CLOSE_UP",
  INSERT: "INSERT",
  OTS: "OTS",
  TWO_SHOT: "TWO_SHOT",
  ECU: "ECU",
  WIDE: "WIDE",
  POV: "POV",
  CUTAWAY: "CUTAWAY",
} as const;
export type ShotType = typeof ShotType[keyof typeof ShotType];

export const ActorStatus = {
  AVAILABLE: "AVAILABLE",
  DELAYED: "DELAYED",
  UNAVAILABLE: "UNAVAILABLE",
  WRAPPED: "WRAPPED",
} as const;
export type ActorStatus = typeof ActorStatus[keyof typeof ActorStatus];

export const LocationStatus = {
  AVAILABLE: "AVAILABLE",
  WARNING: "WARNING",
  UNAVAILABLE: "UNAVAILABLE",
} as const;
export type LocationStatus = typeof LocationStatus[keyof typeof LocationStatus];

export const LocationType = {
  INT: "INT",
  EXT: "EXT",
} as const;
export type LocationType = typeof LocationType[keyof typeof LocationType];

export const PropStatus = {
  AVAILABLE: "AVAILABLE",
  MISSING: "MISSING",
  IN_USE: "IN_USE",
} as const;
export type PropStatus = typeof PropStatus[keyof typeof PropStatus];

export const TimeOfDay = {
  DAY: "DAY",
  GOLDEN_HOUR: "GOLDEN_HOUR",
  NIGHT: "NIGHT",
  INT: "INT",
} as const;
export type TimeOfDay = typeof TimeOfDay[keyof typeof TimeOfDay];

export const DependencyType = {
  MUST_PRECEDE: "MUST_PRECEDE",
  SAME_DAY: "SAME_DAY",
  CONTINUITY_REQUIRED: "CONTINUITY_REQUIRED",
} as const;
export type DependencyType = typeof DependencyType[keyof typeof DependencyType];

export const FactSource = {
  SCRIPT: "SCRIPT",
  CREW_REPORT: "CREW_REPORT",
  AI_INFERENCE: "AI_INFERENCE",
} as const;
export type FactSource = typeof FactSource[keyof typeof FactSource];

export const AlertType = {
  FACT: "FACT",
  INFERENCE: "INFERENCE",
  RECOMMENDATION: "RECOMMENDATION",
} as const;
export type AlertType = typeof AlertType[keyof typeof AlertType];

export const AlertStatus = {
  OPEN: "OPEN",
  UNDER_REVIEW: "UNDER_REVIEW",
  RESOLVED: "RESOLVED",
  OVERRIDDEN: "OVERRIDDEN",
} as const;
export type AlertStatus = typeof AlertStatus[keyof typeof AlertStatus];

export const Severity = {
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
  CRITICAL: "CRITICAL",
} as const;
export type Severity = typeof Severity[keyof typeof Severity];

export const ProposalStatus = {
  PENDING: "PENDING",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
} as const;
export type ProposalStatus = typeof ProposalStatus[keyof typeof ProposalStatus];

export const ProposalCategory = {
  FACT: "FACT",
  INFERENCE: "INFERENCE",
  RECOMMENDATION: "RECOMMENDATION",
} as const;
export type ProposalCategory = typeof ProposalCategory[keyof typeof ProposalCategory];

export const RiskStatus = {
  ACTIVE: "ACTIVE",
  MONITORING: "MONITORING",
  RESOLVED: "RESOLVED",
  ACCEPTED: "ACCEPTED",
} as const;
export type RiskStatus = typeof RiskStatus[keyof typeof RiskStatus];

export const OriginType = {
  HUMAN: "HUMAN",
  AGENT: "AGENT",
  SYSTEM: "SYSTEM",
} as const;
export type OriginType = typeof OriginType[keyof typeof OriginType];

export const AgentMode = {
  DEV: "DEV",
  PRODUCTION: "PRODUCTION",
} as const;
export type AgentMode = typeof AgentMode[keyof typeof AgentMode];

export const PartnerIntegrationStatus = {
  NOT_CONFIGURED: "NOT_CONFIGURED",
  NOT_CONNECTED: "NOT_CONNECTED",
  CONNECTED: "CONNECTED",
} as const;
export type PartnerIntegrationStatus =
  typeof PartnerIntegrationStatus[keyof typeof PartnerIntegrationStatus];

export const EventType = {
  SHOOT_DAY_STARTED: "SHOOT_DAY_STARTED",
  SHOOT_DAY_WRAPPED: "SHOOT_DAY_WRAPPED",
  SHOT_STARTED: "SHOT_STARTED",
  SHOT_COMPLETED: "SHOT_COMPLETED",
  SHOT_FAILED: "SHOT_FAILED",
  SHOT_SKIPPED: "SHOT_SKIPPED",
  ACTOR_DELAYED: "ACTOR_DELAYED",
  ACTOR_AVAILABLE: "ACTOR_AVAILABLE",
  LOCATION_WARNING: "LOCATION_WARNING",
  LOCATION_UNAVAILABLE: "LOCATION_UNAVAILABLE",
  LOCATION_AVAILABLE: "LOCATION_AVAILABLE",
  PROP_UNAVAILABLE: "PROP_UNAVAILABLE",
  PROP_AVAILABLE: "PROP_AVAILABLE",
  CONTINUITY_FACT_RECORDED: "CONTINUITY_FACT_RECORDED",
  CONTINUITY_ALERT_CREATED: "CONTINUITY_ALERT_CREATED",
  CONTINUITY_ALERT_RESOLVED: "CONTINUITY_ALERT_RESOLVED",
  COVERAGE_ALERT_CREATED: "COVERAGE_ALERT_CREATED",
  COVERAGE_ALERT_RESOLVED: "COVERAGE_ALERT_RESOLVED",
  SCHEDULE_PROPOSAL_CREATED: "SCHEDULE_PROPOSAL_CREATED",
  SCHEDULE_PROPOSAL_APPROVED: "SCHEDULE_PROPOSAL_APPROVED",
  SCHEDULE_PROPOSAL_REJECTED: "SCHEDULE_PROPOSAL_REJECTED",
  RISK_CREATED: "RISK_CREATED",
  RISK_UPDATED: "RISK_UPDATED",
  RISK_RESOLVED: "RISK_RESOLVED",
  TOOL_CALLED: "TOOL_CALLED",
  APPROVAL_REQUIRED: "APPROVAL_REQUIRED",
  APPROVAL_GRANTED: "APPROVAL_GRANTED",
  APPROVAL_DENIED: "APPROVAL_DENIED",
} as const;
export type EventType = typeof EventType[keyof typeof EventType];

// ─────────────────────────────────────────────────────────────────────────────
// Domain models
// ─────────────────────────────────────────────────────────────────────────────

export interface ProductionEvent {
  eventId: string;
  productionId: string;
  shootDayId: string;
  timestamp: string; // ISO 8601
  originType: OriginType;
  originId: string;
  type: EventType;
  payload: Record<string, unknown>;
  source: string;
  correlationId: string;
}

export interface WardrobeNote {
  item: string;
  description: string;
  characterId: string;
}

export interface SceneDependency {
  dependencyId: string;
  sceneId: string;
  dependsOnSceneId: string;
  type: DependencyType;
  reason: string;
}

export interface Evidence {
  evidenceId: string;
  evidenceType: string;
  description: string;
  factIds: string[];
  shotIds: string[];
  sceneIds: string[];
}

export interface ProposalRisk {
  description: string;
  severity: Severity;
}

export interface ScheduleChange {
  changeType: string;
  sceneId: string;
  fromPosition: number | null;
  toPosition: number | null;
  reason: string;
}

export interface ContinuityFact {
  factId: string;
  sceneId: string;
  shotId: string | null;
  characterId: string | null;
  propId: string | null;
  attribute: string;
  value: string;
  recordedAt: string;
  source: FactSource;
}

export interface ContinuityAlert {
  alertId: string;
  alertType: AlertType;
  severity: Severity;
  factA: ContinuityFact;
  factB: ContinuityFact;
  description: string;
  status: AlertStatus;
  resolution: string | null;
  createdAt: string;
  resolvedAt: string | null;
  resolvedBy: string | null;
}

export interface CoverageAlert {
  alertId: string;
  sceneId: string;
  missingShotIds: string[];
  severity: Severity;
  description: string;
  status: AlertStatus;
  resolution: string | null;
  createdAt: string;
  resolvedAt: string | null;
}

export interface CoverageStats {
  sceneId: string;
  plannedShotCount: number;
  completedShotCount: number;
  missingShotIds: string[];
  coveragePercent: number;
}

export interface ScheduleProposal {
  proposalId: string;
  shootDayId: string;
  status: ProposalStatus;
  originAgent: string;
  category: ProposalCategory;
  proposedChanges: ScheduleChange[];
  why: string;
  evidence: Evidence[];
  expectedBenefitMinutes: number;
  affectedScenes: string[];
  risks: ProposalRisk[];
  confidence: number;
  agentExecutionId: string | null;
  correlationId: string | null;
  modelName: string | null;
  durationMs: number | null;
  createdAt: string;
  resolvedAt: string | null;
  resolvedBy: string | null;
}

export interface Risk {
  riskId: string;
  severity: Severity;
  reason: string;
  evidence: Evidence[];
  affectedScenes: string[];
  suggestedAction: string;
  confidence: number;
  status: RiskStatus;
  createdAt: string;
  updatedAt: string;
  resolvedAt: string | null;
  resolvedBy: string | null;
}

export interface Actor {
  actorId: string;
  name: string;
  characterName: string;
  availableFromTime: string;
  availableUntilTime: string;
  currentStatus: ActorStatus;
  delayMinutes: number;
}

export interface Location {
  locationId: string;
  name: string;
  locationType: LocationType;
  availableFromTime: string;
  availableUntilTime: string;
  daylightConstraint: boolean;
  daylightDeadlineTime: string | null;
  status: LocationStatus;
  notes: string;
}

export interface Prop {
  propId: string;
  name: string;
  status: PropStatus;
  requiredInScenes: string[];
}

export interface Shot {
  shotId: string;
  sceneId: string;
  shotCode: string;
  shotType: ShotType;
  description: string;
  status: ShotStatus;
  characterId: string | null;
  plannedDurationMinutes: number;
  actualDurationMinutes: number | null;
  startedAt: string | null;
  completedAt: string | null;
}

export interface Scene {
  sceneId: string;
  sceneNumber: string;
  title: string;
  description: string;
  status: SceneStatus;
  locationId: string;
  timeOfDay: TimeOfDay;
  characterIds: string[];
  propIds: string[];
  wardrobeNotes: WardrobeNote[];
  estimatedDurationMinutes: number;
  dependencies: SceneDependency[];
  continuityFacts: ContinuityFact[];
}

export interface ScheduledScene {
  position: number;
  sceneId: string;
  plannedStartTime: string;
  estimatedDurationMinutes: number;
}

export interface ShootDay {
  shootDayId: string;
  productionId: string;
  date: string;
  status: ShootDayStatus;
  scheduledScenes: ScheduledScene[];
}

export interface Production {
  productionId: string;
  title: string;
  status: ProductionStatus;
  shootDays: ShootDay[];
  createdAt: string;
}

export interface DashboardStats {
  shootDayId: string;
  plannedShotCount: number;
  completedShotCount: number;
  failedShotCount: number;
  plannedSceneCount: number;
  completedSceneCount: number;
  partialSceneCount: number;
  blockedSceneCount: number;
  atRiskCount: number;
  openContinuityAlerts: number;
  openCoverageAlerts: number;
  pendingProposals: number;
  totalDelayMinutes: number;
  estimatedMinutesRecovered: number;
  agentMode: AgentMode;
  partnerStatus: string;
}

export interface WrapReport {
  reportId: string;
  shootDayId: string;
  productionId: string;
  generatedAt: string;
  plannedShotCount: number;
  completedShotCount: number;
  failedShotCount: number;
  skippedShotCount: number;
  plannedSceneCount: number;
  completedSceneCount: number;
  partialSceneCount: number;
  incompleteShotIds: string[];
  incompleteSceneIds: string[];
  openCoverageAlerts: string[];
  resolvedContinuityAlerts: string[];
  openContinuityAlerts: string[];
  totalDelayMinutes: number;
  approvedScheduleChangeIds: string[];
  estimatedMinutesRecovered: number;
  activeRiskIds: string[];
  resolvedRiskIds: string[];
  nextDayPriorities: string[];
}

export interface AgentExecution {
  executionId: string;
  correlationId: string;
  agentName: string;
  modelName: string | null;
  eventId: string | null;
  startedAt: string;
  completedAt: string | null;
  durationMs: number | null;
  toolCalls: ToolCallRecord[];
  status: string;
  errorCode: string | null;
  evidenceReferences: string[];
  shortRationale: string;
  mode: AgentMode;
}

export interface ToolCallRecord {
  toolCallId: string;
  toolName: string;
  callerType: OriginType;
  callerId: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown> | null;
  status: string;
  calledAt: string;
  completedAt: string | null;
}

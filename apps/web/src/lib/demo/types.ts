import type { ScheduleProposal } from "@/lib/types/domain";

export type RuntimeConnection = "CONNECTED" | "ERROR" | "NOT_CHECKED";

export interface DemoActor {
  actorId: string;
  name: string;
  characterName: string;
  currentStatus: string;
  delayMinutes: number;
  demoEnabled: boolean;
  defaultDelayMinutes: number | null;
}

export interface DemoScheduleEntry {
  position: number;
  sceneId: string;
  title: string;
  plannedStartTime: string;
  estimatedDurationMinutes: number;
  changed: boolean;
}

export interface DemoTimelineEntry {
  eventId: string;
  type: string;
  classification: "FACT" | "INFERENCE" | "RECOMMENDATION" | "HUMAN_DECISION";
  timestamp: string;
  originType: string;
  originId: string;
  correlationId: string;
  payload: Record<string, unknown>;
}

export interface TechnicalEvidence {
  provider: string;
  agentName: string;
  modelName: string | null;
  executionId: string;
  sessionId: string;
  correlationId: string;
  durationMs: number | null;
  status: string;
  toolNames: string[];
  evidenceReferences: string[];
  shortRationale: string;
}

export interface DemoCoverage {
  fact: null | {
    sceneId: string;
    plannedShotCount: number;
    completedShotCount: number;
    missingShotIds: string[];
    coveragePercent: number;
    classification: "FACT";
  };
  alert: null | {
    alertId: string;
    sceneId: string;
    missingShotIds: string[];
    severity: string;
    description: string;
    status: string;
  };
}

export interface DemoState {
  demoSessionId: string;
  sessionStatus: string;
  production: {
    title: string;
    status: string;
    sceneCount: number;
    shotCount: number;
    completedShotCount: number;
    actorCount: number;
    shootDayId: string;
    shootDayStatus: string;
  };
  actors: DemoActor[];
  schedule: {
    current: DemoScheduleEntry[];
    before: DemoScheduleEntry[] | null;
    after: DemoScheduleEntry[] | null;
  };
  proposal: ScheduleProposal | null;
  coverage: DemoCoverage;
  timeline: DemoTimelineEntry[];
  runtime: {
    agentEngine: RuntimeConnection;
    gemini: RuntimeConnection;
    privateToolServer: RuntimeConnection;
    firestore: RuntimeConnection;
  };
  technicalEvidence: TechnicalEvidence | null;
  lastErrorCode: string | null;
  humanDecision: null | {
    classification: "HUMAN_DECISION";
    decision: "APPROVED" | "REJECTED";
    actorType: "HUMAN";
    actorId: string;
    proposalId: string;
    correlationId: string;
    timestamp: string;
  };
}

export type DemoAction =
  | { operation: "RESET" }
  | { operation: "ACTOR_DELAY"; actorId: "ACT_02"; delayMinutes: 45 }
  | { operation: "ACTOR_DELAY"; actorId: "ACT_03"; delayMinutes: 30 }
  | { operation: "APPROVE"; proposalId: string }
  | { operation: "REJECT"; proposalId: string }
  | { operation: "CHECK_COVERAGE" };

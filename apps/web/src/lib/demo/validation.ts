import type { DemoAction } from "./types";

const RESOURCE_ID = /^[A-Za-z0-9_-]{8,80}$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  const actual = Object.keys(value).sort();
  return actual.length === keys.length && actual.every((key, index) => key === [...keys].sort()[index]);
}

export function parseDemoAction(value: unknown): DemoAction {
  if (!isRecord(value) || typeof value.operation !== "string") {
    throw new Error("INVALID_OPERATION");
  }
  if (value.operation === "COMMAND") {
    if (!hasExactKeys(value, ["operation", "command"])) {
      throw new Error("INVALID_OPERATION_FIELDS");
    }
    if (typeof value.command !== "string") {
      throw new Error("INVALID_COMMAND");
    }
    const command = value.command.trim();
    if (command.length < 4 || command.length > 500 || command.includes("\0")) {
      throw new Error("INVALID_COMMAND");
    }
    return { operation: "COMMAND", command };
  }
  if (value.operation === "RESET" || value.operation === "CHECK_COVERAGE") {
    if (!hasExactKeys(value, ["operation"])) throw new Error("INVALID_OPERATION_FIELDS");
    return { operation: value.operation };
  }
  if (value.operation === "ACTOR_DELAY") {
    if (!hasExactKeys(value, ["operation", "actorId", "delayMinutes"])) {
      throw new Error("INVALID_OPERATION_FIELDS");
    }
    if (value.actorId === "ACT_02" && value.delayMinutes === 45) {
      return { operation: "ACTOR_DELAY", actorId: "ACT_02", delayMinutes: 45 };
    }
    if (value.actorId === "ACT_03" && value.delayMinutes === 30) {
      return { operation: "ACTOR_DELAY", actorId: "ACT_03", delayMinutes: 30 };
    }
    throw new Error("INVALID_ACTOR_DELAY");
  }
  if (value.operation === "APPROVE" || value.operation === "REJECT") {
    if (!hasExactKeys(value, ["operation", "proposalId"])) {
      throw new Error("INVALID_OPERATION_FIELDS");
    }
    if (typeof value.proposalId !== "string" || !RESOURCE_ID.test(value.proposalId)) {
      throw new Error("INVALID_PROPOSAL_ID");
    }
    return { operation: value.operation, proposalId: value.proposalId };
  }
  throw new Error("OPERATION_NOT_ALLOWED");
}

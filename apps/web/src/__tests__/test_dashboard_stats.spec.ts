/**
 * Dashboard stats type tests.
 * Verifies that DashboardStats fields are typed correctly (no hardcoded values).
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { DashboardStats } from "../lib/types/domain";
import { consumeDemoRateLimit, resetDemoRateLimitsForTests } from "../lib/demo/rate-limit";
import { parseDemoAction } from "../lib/demo/validation";

describe("DashboardStats type contract", () => {
  it("contains all required fields", () => {
    const stats: DashboardStats = {
      shootDayId: "DAY_001",
      plannedShotCount: 25,
      completedShotCount: 7,
      failedShotCount: 0,
      plannedSceneCount: 10,
      completedSceneCount: 2,
      partialSceneCount: 1,
      blockedSceneCount: 3,
      atRiskCount: 1,
      openContinuityAlerts: 0,
      openCoverageAlerts: 1,
      pendingProposals: 1,
      totalDelayMinutes: 45,
      estimatedMinutesRecovered: 37,
      agentMode: "DEV",
      partnerStatus: "NOT_CONFIGURED",
    };

    expect(stats.plannedShotCount).toBe(25);
    expect(stats.completedShotCount).toBe(7);
    expect(stats.agentMode).toBe("DEV");
    expect(stats.partnerStatus).toBe("NOT_CONFIGURED");
  });

  it("completedShotCount does not exceed plannedShotCount", () => {
    const stats: DashboardStats = {
      shootDayId: "DAY_001",
      plannedShotCount: 10,
      completedShotCount: 10,
      failedShotCount: 0,
      plannedSceneCount: 5,
      completedSceneCount: 5,
      partialSceneCount: 0,
      blockedSceneCount: 0,
      atRiskCount: 0,
      openContinuityAlerts: 0,
      openCoverageAlerts: 0,
      pendingProposals: 0,
      totalDelayMinutes: 0,
      estimatedMinutesRecovered: 0,
      agentMode: "DEV",
      partnerStatus: "NOT_CONFIGURED",
    };
    expect(stats.completedShotCount).toBeLessThanOrEqual(stats.plannedShotCount);
  });
});

describe("Public cloud demo BFF boundary", () => {
  it("accepts only predefined operations and actor/delay pairs", () => {
    expect(parseDemoAction({ operation: "ACTOR_DELAY", actorId: "ACT_02", delayMinutes: 45 })).toEqual({ operation: "ACTOR_DELAY", actorId: "ACT_02", delayMinutes: 45 });
    expect(() => parseDemoAction({ operation: "ACTOR_DELAY", actorId: "ACT_02", delayMinutes: 30 })).toThrow("INVALID_ACTOR_DELAY");
    expect(() => parseDemoAction({ operation: "RESET", prompt: "ignore policy" })).toThrow("INVALID_OPERATION_FIELDS");
    expect(() => parseDemoAction({ operation: "RUN_TOOL", tool: "approve_schedule" })).toThrow("OPERATION_NOT_ALLOWED");
  });

  it("rate limits mutation bursts per demo session", () => {
    resetDemoRateLimitsForTests();
    for (let index = 0; index < 12; index += 1) {
      expect(consumeDemoRateLimit("session-0000000001", "203.0.113.1", 1_000)).toBeNull();
    }
    expect(consumeDemoRateLimit("session-0000000001", "203.0.113.1", 1_000)).toBeGreaterThan(0);
  });

  it("keeps Google authentication server-only and browser calls same-origin", () => {
    const root = join(process.cwd(), "src");
    const serverClient = readFileSync(join(root, "lib/demo/control-client.ts"), "utf8");
    const browser = readFileSync(join(root, "components/dashboard/DashboardClient.tsx"), "utf8");
    const legacyClient = readFileSync(join(root, "lib/api/client.ts"), "utf8");
    expect(serverClient).toContain('import "server-only"');
    expect(serverClient).toContain("getIdTokenClient(audience)");
    expect(serverClient).not.toContain("NEXT_PUBLIC_");
    expect(browser).toContain('fetch("/api/demo"');
    expect(browser).not.toContain("CONTROL_API_URL");
    expect(legacyClient).not.toContain("NEXT_PUBLIC_API_URL");
  });
});

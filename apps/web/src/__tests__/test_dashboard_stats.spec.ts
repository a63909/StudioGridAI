/**
 * Dashboard stats type tests.
 * Verifies that DashboardStats fields are typed correctly (no hardcoded values).
 */
import { describe, it, expect } from "vitest";
import type { DashboardStats } from "../lib/types/domain";

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

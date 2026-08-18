/**
 * API client for StudioGrid AI backend.
 * All counts and data come from the API — never hardcoded in the UI.
 */

// Legacy screens remain unprivileged and same-origin. The cloud demo uses only
// /api/demo; no browser-visible environment variable can select a backend.
const BASE_URL = "/api/legacy";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `API error ${res.status}: ${path}`);
  }
  return res.json();
}

import type {
  DashboardStats,
  Scene,
  Shot,
  ScheduleProposal,
  ContinuityAlert,
  ContinuityFact,
  Risk,
  WrapReport,
} from "@/lib/types/domain";

export const apiClient = {
  getDashboardStats: () => get<DashboardStats>("/production/dashboard-stats"),

  listScenes: () => get<Scene[]>("/scenes/"),
  getScene: (id: string) => get<Scene>(`/scenes/${id}`),
  getSceneCoverage: (id: string) => get<unknown>(`/scenes/${id}/coverage`),

  listShots: () => get<Shot[]>("/shots/"),
  startShot: (id: string, body: { shootDayId: string; callerId?: string }) =>
    post<Shot>(`/shots/${id}/start`, body),
  completeShot: (id: string, body: { shootDayId: string; actualDurationMinutes?: number; callerId?: string }) =>
    post<Shot>(`/shots/${id}/complete`, body),

  getSchedule: () => get<unknown>("/schedule/"),
  listProposals: () => get<ScheduleProposal[]>("/schedule/proposals"),
  reportActorDelay: (body: { actorId: string; delayMinutes: number; reason: string }) =>
    post<unknown>("/schedule/actor-delay", body),
  reportActorAvailable: (body: { actorId: string }) =>
    post<unknown>("/schedule/actor-available", body),
  approveProposal: (id: string, approvedBy: string) =>
    post<ScheduleProposal>(`/schedule/proposals/${id}/approve`, { approvedBy }),
  rejectProposal: (id: string, rejectedBy: string, reason: string) =>
    post<ScheduleProposal>(`/schedule/proposals/${id}/reject`, { rejectedBy, reason }),

  listContinuityFacts: () => get<ContinuityFact[]>("/continuity/facts"),
  listContinuityAlerts: () => get<ContinuityAlert[]>("/continuity/alerts"),
  resolveAlert: (id: string, body: { resolution: string; resolvedBy: string; override?: boolean }) =>
    post<ContinuityAlert>(`/continuity/alerts/${id}/resolve`, body),

  listRisks: () => get<Risk[]>("/risks/"),

  getWrapReport: () => get<WrapReport | { status: string }>("/report/"),
  wrapDay: (wrappedBy: string) => post<WrapReport>("/report/wrap-day", { wrappedBy }),

  listEvents: (limit?: number) =>
    get<unknown[]>(`/events/?limit=${limit ?? 100}`),

  health: () => get<unknown>("/health"),
};

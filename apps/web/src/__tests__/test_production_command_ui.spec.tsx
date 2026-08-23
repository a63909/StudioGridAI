import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProductionCommandDashboard } from "../components/dashboard/ProductionCommandDashboard";
import type { DemoState } from "../lib/demo/types";

const localeState = vi.hoisted(() => ({ current: "en" as "en" | "ru" }));

vi.mock("next-intl", () => {
  const messages = {
    en: {
      cloudDemo: "Live cloud demo", subtitle: "AI Production Control Room", film: "Film", shootDay: "Shooting day", loading: "Loading", working: "Working", reset: "Reset demo",
      "metrics.status": "Production status", "metrics.scenes": "Scenes", "metrics.shots": "Shots", "metrics.completedShots": "Completed shots", "metrics.actors": "Actors", "metrics.session": "Demo state",
      "actorDelay.eyebrow": "Production fact", "actorDelay.title": "Simulate actor delay", "actorDelay.description": "Actor delay shortcut", "actorDelay.maya": "Maya Reed · 45m", "actorDelay.daniel": "Daniel Osei · 30m", "actorDelay.button": "Simulate {minutes} min delay", "actorDelay.running": "Running", "actorDelay.fact": "{actor} is delayed by {minutes} minutes.",
      "runtime.title": "Cloud status", "runtime.agentEngine": "Agent Engine", "runtime.gemini": "Gemini", "runtime.toolServer": "Private Tool Server", "runtime.firestore": "Firestore", "runtime.truth": "Verified runtime state.",
      "proposal.eyebrow": "Agent output", "proposal.title": "Schedule proposal", "proposal.empty": "No proposal", "proposal.expectedBenefit": "Expected recovery", "proposal.evidence": "Evidence", "proposal.ordering": "Proposed ordering", "proposal.affected": "Affected scenes", "proposal.risks": "Risks", "proposal.confidence": "Confidence", "proposal.approve": "Approve as human", "proposal.reject": "Reject as human", "proposal.humanOnly": "The agent cannot perform this decision.", "proposal.approvedHuman": "Approved by human", "proposal.rejectedHuman": "Rejected by human",
      "schedule.eyebrow": "Operational impact", "schedule.title": "Schedule before / after", "schedule.description": "Durable schedule state.", "schedule.current": "Current", "schedule.before": "Before", "schedule.after": "After human approval",
      "coverage.eyebrow": "Coverage Agent", "coverage.title": "Check real shot coverage", "coverage.description": "Coverage shortcut", "coverage.button": "Check coverage", "coverage.running": "Running",
      "timeline.eyebrow": "Audit trail", "timeline.title": "Fact → decision timeline", "timeline.empty": "No events",
      "evidence.description": "Safe operational metadata only.", "evidence.provider": "Runtime", "evidence.agent": "Agent", "evidence.model": "Model", "evidence.execution": "Execution ID", "evidence.session": "Agent session ID", "evidence.correlation": "Correlation ID", "evidence.duration": "Duration", "evidence.tools": "Verified tool calls", "evidence.references": "Evidence references", "evidence.rationale": "Short rationale", "evidence.empty": "No evidence",
      "errors.title": "Cloud action failed.", "errors.load": "Load failed", "errors.action": "Action failed",
    },
    ru: {
      cloudDemo: "Облачное демо", subtitle: "Центр управления производством", film: "Фильм", shootDay: "Съёмочный день", loading: "Загрузка", working: "Выполняется", reset: "Сбросить демо",
      "metrics.status": "Статус", "metrics.scenes": "Сцены", "metrics.shots": "Кадры", "metrics.completedShots": "Снято кадров", "metrics.actors": "Актёры", "metrics.session": "Состояние демо",
      "actorDelay.eyebrow": "Производственный факт", "actorDelay.title": "Смоделировать задержку актёра", "actorDelay.description": "Сценарий задержки", "actorDelay.maya": "Maya Reed · 45 мин", "actorDelay.daniel": "Daniel Osei · 30 мин", "actorDelay.button": "Задержка на {minutes} мин", "actorDelay.running": "Выполняется", "actorDelay.fact": "{actor} задерживается на {minutes} минут.",
      "runtime.title": "Статус облака", "runtime.agentEngine": "Agent Engine", "runtime.gemini": "Gemini", "runtime.toolServer": "Приватный Tool Server", "runtime.firestore": "Firestore", "runtime.truth": "Проверенное состояние.",
      "proposal.eyebrow": "Результат агента", "proposal.title": "Предложение расписания", "proposal.empty": "Нет предложения", "proposal.expectedBenefit": "Ожидаемое восстановление", "proposal.evidence": "Доказательства", "proposal.ordering": "Предложенный порядок", "proposal.affected": "Затронутые сцены", "proposal.risks": "Риски", "proposal.confidence": "Уверенность", "proposal.approve": "Подтвердить как человек", "proposal.reject": "Отклонить как человек", "proposal.humanOnly": "Агент не может принять это решение.", "proposal.approvedHuman": "Подтверждено человеком", "proposal.rejectedHuman": "Отклонено человеком",
      "schedule.eyebrow": "Операционное влияние", "schedule.title": "Расписание до / после", "schedule.description": "Состояние расписания.", "schedule.current": "Текущее", "schedule.before": "До", "schedule.after": "После подтверждения",
      "coverage.eyebrow": "Агент покрытия", "coverage.title": "Проверить покрытие кадрами", "coverage.description": "Сценарий покрытия", "coverage.button": "Проверить покрытие", "coverage.running": "Выполняется",
      "timeline.eyebrow": "Аудит", "timeline.title": "Факт → решение", "timeline.empty": "Нет событий",
      "evidence.description": "Только безопасные технические данные.", "evidence.provider": "Среда", "evidence.agent": "Агент", "evidence.model": "Модель", "evidence.execution": "Execution ID", "evidence.session": "Сессия", "evidence.correlation": "Correlation ID", "evidence.duration": "Длительность", "evidence.tools": "Вызовы tools", "evidence.references": "Ссылки", "evidence.rationale": "Краткое объяснение", "evidence.empty": "Нет данных",
      "errors.title": "Ошибка облачного действия.", "errors.load": "Ошибка загрузки", "errors.action": "Ошибка действия",
    },
  } as const;

  const translate = (locale: "en" | "ru") => (key: string, values?: Record<string, string | number>) => {
    let value = (messages[locale] as Record<string, string>)[key] || key;
    for (const [name, replacement] of Object.entries(values || {})) value = value.replace(`{${name}}`, String(replacement));
    return value;
  };
  const translators = { en: translate("en"), ru: translate("ru") };

  return {
    useLocale: () => localeState.current,
    useTranslations: () => translators[localeState.current],
  };
});

const scheduleEntry = (position: number, sceneId: string) => ({
  position,
  sceneId,
  title: `Scene ${sceneId}`,
  plannedStartTime: `0${position + 7}:00`,
  estimatedDurationMinutes: 30,
  changed: false,
});

function baselineState(): DemoState {
  return {
    demoSessionId: "test-demo-session-0001",
    sessionStatus: "READY",
    production: { title: "LAST LIGHT", status: "ACTIVE", sceneCount: 4, shotCount: 13, completedShotCount: 3, actorCount: 4, shootDayId: "DAY_01", shootDayStatus: "IN_PROGRESS" },
    actors: [],
    schedule: { current: [scheduleEntry(1, "SC_01"), scheduleEntry(2, "SC_05")], before: null, after: null },
    proposal: null,
    coverage: { fact: null, alert: null },
    timeline: [],
    runtime: { agentEngine: "CONNECTED", gemini: "CONNECTED", privateToolServer: "CONNECTED", firestore: "CONNECTED" },
    technicalEvidence: null,
    commandRouting: null,
    lastErrorCode: null,
    humanDecision: null,
  };
}

function coverageState(): DemoState {
  const baseline = baselineState();
  return {
    ...baseline,
    production: { ...baseline.production, completedShotCount: 4 },
    commandRouting: { provider: "Google Vertex AI", modelName: "gemini-3.6-flash", intent: "CHECK_COVERAGE", target: "COVERAGE_AGENT", summary: "Route to the fixed coverage workflow." },
    coverage: {
      fact: { sceneId: "SC_05", plannedShotCount: 3, completedShotCount: 1, missingShotIds: ["SH_12", "SH_13"], coveragePercent: 33.3, classification: "FACT" },
      alert: { alertId: "ALERT_1", sceneId: "SC_05", missingShotIds: ["SH_12", "SH_13"], severity: "HIGH", description: "Required coverage remains incomplete.", status: "OPEN" },
    },
    technicalEvidence: { provider: "Vertex AI Agent Engine", agentName: "COVERAGE_AGENT", modelName: "gemini-3.6-flash", executionId: "coverage-execution-1", sessionId: "coverage-session-1", correlationId: "coverage-correlation-1", durationMs: 1200, status: "COMPLETED", toolNames: ["check_coverage"], evidenceReferences: ["SC_05"], shortRationale: "SC_05 is missing SH_12 and SH_13." },
  };
}

function scheduleState(): DemoState {
  const baseline = baselineState();
  const before = [scheduleEntry(1, "SC_01"), scheduleEntry(2, "SC_05")];
  return {
    ...baseline,
    commandRouting: { provider: "Google Vertex AI", modelName: "gemini-3.6-flash", intent: "ACTOR_DELAY", target: "SCHEDULE_AGENT", summary: "Route the exact actor delay to schedule replanning." },
    schedule: { current: before, before, after: null },
    proposal: {
      proposalId: "proposal-1", shootDayId: "DAY_01", status: "PENDING", originAgent: "SCHEDULE_AGENT", category: "RECOMMENDATION",
      proposedChanges: [{ changeType: "REORDER", sceneId: "SC_05", fromPosition: 2, toPosition: 1, reason: "Maya-independent work" }],
      why: "Move actor-independent SC_05 ahead while Maya Reed is delayed.",
      evidence: [{ evidenceId: "evidence-1", evidenceType: "FACT", description: "Maya Reed is delayed 45 minutes.", factIds: [], shotIds: [], sceneIds: ["SC_05"] }],
      expectedBenefitMinutes: 35, affectedScenes: ["SC_05", "SC_01"], risks: [{ description: "Lighting reset may be required.", severity: "LOW" }], confidence: 0.87,
      agentExecutionId: "schedule-execution-1", correlationId: "schedule-correlation-1", modelName: "gemini-3.6-flash", durationMs: 1400,
      createdAt: "2026-08-24T00:00:00Z", resolvedAt: null, resolvedBy: null,
    },
    timeline: [{ eventId: "actor-delay-1", type: "ACTOR_DELAYED", classification: "FACT", timestamp: "2026-08-24T00:00:00Z", originType: "HUMAN", originId: "production-manager", correlationId: "schedule-correlation-1", payload: { actorId: "ACT_02", actorName: "Maya Reed", delayMinutes: 45 } }],
    technicalEvidence: { provider: "Vertex AI Agent Engine", agentName: "SCHEDULE_AGENT", modelName: "gemini-3.6-flash", executionId: "schedule-execution-1", sessionId: "schedule-session-1", correlationId: "schedule-correlation-1", durationMs: 1400, status: "COMPLETED", toolNames: ["create_schedule_proposal"], evidenceReferences: ["ACT_02", "SC_05"], shortRationale: "A human decision is required before mutation." },
  };
}

const response = (payload: DemoState) => ({ ok: true, json: async () => payload });

function installFetch(commandResult: DemoState, resetResult = baselineState()) {
  const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    if (!init?.method || init.method === "GET") return response(baselineState());
    const action = JSON.parse(String(init.body));
    if (action.operation === "COMMAND") return response(commandResult);
    if (action.operation === "RESET") return response(resetResult);
    throw new Error(`Unexpected test action: ${action.operation}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("Production Command contextual dashboard", () => {
  afterEach(() => {
    localeState.current = "en";
    vi.unstubAllGlobals();
  });

  it("makes Coverage the first operational result after one command", async () => {
    const fetchMock = installFetch(coverageState());
    render(<ProductionCommandDashboard />);
    await screen.findByText("StudioGrid AI");
    fireEvent.click(screen.getByRole("button", { name: "Run production command" }));

    const workflow = await screen.findByTestId("active-coverage-workflow");
    expect(within(workflow).getByText(/Coverage result: SC_05/)).toBeInTheDocument();
    expect(within(workflow).getByText("1/3")).toBeInTheDocument();
    expect(within(workflow).getByText("SH_12")).toBeInTheDocument();
    expect(within(workflow).getByText("SH_13")).toBeInTheDocument();
    expect(within(workflow).getByText("OPEN")).toBeInTheDocument();
    expect(workflow.compareDocumentPosition(screen.getByTestId("production-context")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.queryByTestId("production-command-result")).not.toBeInTheDocument();

    const secondary = screen.getByTestId("other-demo-scenarios");
    expect(secondary).not.toHaveAttribute("open");
    expect(within(secondary).getByRole("heading", { name: "Simulate actor delay", hidden: true })).toBeInTheDocument();
    const technical = screen.getByTestId("technical-details");
    expect(technical).not.toHaveAttribute("open");
    for (const detail of within(technical).getAllByText("COVERAGE_AGENT")) expect(detail).not.toBeVisible();
    expect(within(workflow).queryByText("COVERAGE_AGENT")).not.toBeInTheDocument();

    const commandCalls = fetchMock.mock.calls.filter(([, init]) => init?.body && JSON.parse(String(init.body)).operation === "COMMAND");
    expect(commandCalls).toHaveLength(1);
  });

  it("clears the active workflow on Reset even when old technical evidence remains", async () => {
    installFetch(coverageState(), { ...baselineState(), technicalEvidence: coverageState().technicalEvidence });
    render(<ProductionCommandDashboard />);
    await screen.findByText("StudioGrid AI");
    fireEvent.click(screen.getByRole("button", { name: "Run production command" }));
    await screen.findByTestId("active-coverage-workflow");
    fireEvent.click(screen.getByRole("button", { name: "Reset demo" }));

    await waitFor(() => expect(screen.queryByTestId("active-coverage-workflow")).not.toBeInTheDocument());
    expect(screen.queryByTestId("active-schedule-workflow")).not.toBeInTheDocument();
    expect(screen.queryByTestId("production-command-result")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Simulate actor delay" })).toBeInTheDocument();
  });

  it("shows a pending Schedule workflow without applying the proposed order", async () => {
    installFetch(scheduleState());
    render(<ProductionCommandDashboard />);
    await screen.findByText("StudioGrid AI");
    fireEvent.click(screen.getByRole("button", { name: "Schedule · approval boundary" }));
    fireEvent.click(screen.getByRole("button", { name: "Run production command" }));

    const workflow = await screen.findByTestId("active-schedule-workflow");
    expect(within(workflow).getByText("Schedule result")).toBeInTheDocument();
    expect(within(workflow).getByText("Maya Reed is delayed by 45 minutes.")).toBeInTheDocument();
    expect(screen.getByText("PENDING")).toBeInTheDocument();
    expect(screen.getByText("Current schedule — unchanged")).toBeInTheDocument();
    expect(screen.getByText("Proposed order — not applied")).toBeInTheDocument();
    expect(screen.getByText(/Affected scenes: SC_05, SC_01/)).toBeInTheDocument();
    expect(screen.getByText(/Lighting reset may be required/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve as human" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject as human" })).toBeInTheDocument();
    expect(within(workflow).queryByText("SCHEDULE_AGENT")).not.toBeInTheDocument();
    for (const detail of within(screen.getByTestId("technical-details")).getAllByText("SCHEDULE_AGENT")) expect(detail).not.toBeVisible();
  });

  it("renders the Russian Coverage result and keeps technical routing collapsed", async () => {
    localeState.current = "ru";
    installFetch(coverageState());
    render(<ProductionCommandDashboard />);
    await screen.findByText("StudioGrid AI");
    expect(screen.getByLabelText("Команда производству")).toHaveValue("Проверь SC_05 и убедись, что все обязательные кадры сняты.");
    fireEvent.click(screen.getByRole("button", { name: "Выполнить производственную команду" }));

    const workflow = await screen.findByTestId("active-coverage-workflow");
    expect(within(workflow).getByText(/Результат проверки покрытия: SC_05/)).toBeInTheDocument();
    expect(within(workflow).getByText("SH_12")).toBeInTheDocument();
    expect(within(workflow).getByText("SH_13")).toBeInTheDocument();
    expect(screen.getByText("Технические детали").closest("details")).not.toHaveAttribute("open");
  });
});

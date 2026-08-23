"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import type { DemoAction, DemoScheduleEntry, DemoState, DemoTimelineEntry, RuntimeConnection } from "@/lib/demo/types";

function StatusDot({ label, value }: { label: string; value: RuntimeConnection }) {
  const color = value === "CONNECTED" ? "bg-emerald-400" : value === "ERROR" ? "bg-red-400" : "bg-neutral-500";
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-neutral-800 bg-neutral-950/70 px-3 py-2">
      <span className="text-xs text-neutral-400">{label}</span>
      <span className="flex items-center gap-2 text-[11px] font-semibold text-neutral-200">
        <span className={`h-2 w-2 rounded-full ${color}`} aria-hidden="true" />{value}
      </span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/80 p-4">
      <div className="break-all font-mono text-lg font-semibold leading-tight text-white sm:text-2xl">{value}</div>
      <div className="mt-1 text-xs text-neutral-500">{label}</div>
    </div>
  );
}

function ScheduleColumn({ title, entries }: { title: string; entries: DemoScheduleEntry[] }) {
  return (
    <div className="min-w-0 rounded-xl border border-neutral-800 bg-neutral-950/60 p-3">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-neutral-400">{title}</h3>
      <ol className="space-y-2">{entries.map((entry) => (
        <li key={entry.sceneId} className={`grid grid-cols-[2rem_1fr_auto] items-center gap-2 rounded-lg border px-2 py-2 text-xs ${entry.changed ? "border-blue-700 bg-blue-950/60 text-blue-100" : "border-neutral-800 bg-neutral-900 text-neutral-300"}`}>
          <span className="font-mono text-neutral-500">{entry.position}</span>
          <span className="min-w-0 truncate"><strong className="mr-2 font-mono">{entry.sceneId}</strong>{entry.title}</span>
          <span className="font-mono text-neutral-500">{entry.plannedStartTime}</span>
        </li>
      ))}</ol>
    </div>
  );
}

function ClassificationBadge({ value }: { value: DemoTimelineEntry["classification"] }) {
  const classes = { FACT: "border-emerald-800 bg-emerald-950 text-emerald-300", INFERENCE: "border-amber-800 bg-amber-950 text-amber-300", RECOMMENDATION: "border-blue-800 bg-blue-950 text-blue-300", HUMAN_DECISION: "border-fuchsia-800 bg-fuchsia-950 text-fuchsia-300" }[value];
  return <span className={`rounded border px-2 py-0.5 font-mono text-[10px] ${classes}`}>{value.replace("_", " ")}</span>;
}

export function DashboardClient({
  state,
  onState,
}: {
  state: DemoState | null;
  onState: (state: DemoState) => void;
}) {
  const t = useTranslations("cloudDemo");
  const [selectedActor, setSelectedActor] = useState<"ACT_02" | "ACT_03">("ACT_02");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/demo", { cache: "no-store" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.error?.message || t("errors.load"));
      onState(payload);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : t("errors.load"));
    }
  }, [onState, t]);

  useEffect(() => {
    const initialLoad = window.setTimeout(() => void load(), 0);
    const interval = window.setInterval(() => void load(), 15_000);
    return () => {
      window.clearTimeout(initialLoad);
      window.clearInterval(interval);
    };
  }, [load]);

  const run = async (action: DemoAction) => {
    setBusy(action.operation);
    setError(null);
    try {
      const response = await fetch("/api/demo", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(action) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.error?.message || t("errors.action"));
      onState(payload);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : t("errors.action"));
      await load();
    } finally {
      setBusy(null);
    }
  };

  if (!state) return <div className="px-4 py-16 text-center text-sm text-neutral-400">{error || t("loading")}</div>;

  const proposal = state.proposal;
  const before = state.schedule.before || state.schedule.current;
  const after = state.schedule.after;
  const actorDelay = selectedActor === "ACT_02" ? 45 : 30;
  const latestFact = [...state.timeline].reverse().find((item) => item.type === "ACTOR_DELAYED");

  return (
    <div className="mx-auto max-w-screen-xl space-y-6 px-4 py-6 sm:py-8">
      <section className="overflow-hidden rounded-2xl border border-blue-900/70 bg-gradient-to-br from-blue-950 via-neutral-950 to-neutral-950 p-5 sm:p-8">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div>
            <div className="mb-3 inline-flex rounded-full border border-blue-800 bg-blue-950 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-blue-300">{t("cloudDemo")}</div>
            <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">StudioGrid AI</h1>
            <p className="mt-2 text-base text-blue-200 sm:text-lg">{t("subtitle")}</p>
            <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
              <span className="text-neutral-400">{t("film")}: <strong className="text-white">{state.production.title}</strong></span>
              <span className="text-neutral-400">{t("shootDay")}: <strong className="font-mono text-white">{state.production.shootDayId}</strong></span>
              <span className="rounded-full bg-emerald-950 px-3 py-1 text-xs font-semibold text-emerald-300">{state.production.status}</span>
            </div>
          </div>
          <button className="rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-2 text-sm font-medium text-neutral-200 hover:border-neutral-500 disabled:opacity-50" onClick={() => void run({ operation: "RESET" })} disabled={busy !== null}>{busy === "RESET" ? t("working") : t("reset")}</button>
        </div>
      </section>

      {error ? <div role="alert" className="rounded-xl border border-red-800 bg-red-950/70 p-4 text-sm text-red-200"><strong className="mr-2">{t("errors.title")}</strong>{error}</div> : null}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Metric label={t("metrics.status")} value={state.production.shootDayStatus} />
        <Metric label={t("metrics.scenes")} value={state.production.sceneCount} />
        <Metric label={t("metrics.shots")} value={state.production.shotCount} />
        <Metric label={t("metrics.completedShots")} value={state.production.completedShotCount} />
        <Metric label={t("metrics.actors")} value={state.production.actorCount} />
        <Metric label={t("metrics.session")} value={state.sessionStatus} />
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-400">01 · {t("actorDelay.eyebrow")}</div>
              <h2 className="mt-2 text-xl font-semibold text-white">{t("actorDelay.title")}</h2>
              <p className="mt-1 max-w-xl text-sm leading-6 text-neutral-400">{t("actorDelay.description")}</p>
            </div>
            <div className="flex rounded-lg border border-neutral-700 bg-neutral-950 p-1">
              <button className={`rounded-md px-3 py-2 text-xs ${selectedActor === "ACT_02" ? "bg-blue-600 text-white" : "text-neutral-400"}`} onClick={() => setSelectedActor("ACT_02")} disabled={busy !== null}>{t("actorDelay.maya")}</button>
              <button className={`rounded-md px-3 py-2 text-xs ${selectedActor === "ACT_03" ? "bg-blue-600 text-white" : "text-neutral-400"}`} onClick={() => setSelectedActor("ACT_03")} disabled={busy !== null}>{t("actorDelay.daniel")}</button>
            </div>
          </div>
          <button className="mt-5 w-full rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50 sm:w-auto" onClick={() => void run(selectedActor === "ACT_02" ? { operation: "ACTOR_DELAY", actorId: "ACT_02", delayMinutes: 45 } : { operation: "ACTOR_DELAY", actorId: "ACT_03", delayMinutes: 30 })} disabled={busy !== null || proposal?.status === "PENDING"}>{busy === "ACTOR_DELAY" ? t("actorDelay.running") : t("actorDelay.button", { minutes: actorDelay })}</button>
          {latestFact ? <div className="mt-5 rounded-xl border border-emerald-900 bg-emerald-950/40 p-4"><ClassificationBadge value="FACT" /><p className="mt-2 text-sm text-emerald-100">{t("actorDelay.fact", { actor: String(latestFact.payload.actorName || latestFact.payload.actorId), minutes: Number(latestFact.payload.delayMinutes || 0) })}</p></div> : null}
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-neutral-500">{t("runtime.title")}</div>
          <div className="mt-4 grid gap-2">
            <StatusDot label={t("runtime.agentEngine")} value={state.runtime.agentEngine} />
            <StatusDot label={t("runtime.gemini")} value={state.runtime.gemini} />
            <StatusDot label={t("runtime.toolServer")} value={state.runtime.privateToolServer} />
            <StatusDot label={t("runtime.firestore")} value={state.runtime.firestore} />
          </div>
          <p className="mt-4 text-xs leading-5 text-neutral-500">{t("runtime.truth")}</p>
        </div>
      </section>
      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-400">02 · {t("proposal.eyebrow")}</div>
        <h2 className="mt-2 text-xl font-semibold text-white">{t("proposal.title")}</h2>
        {!proposal ? <div className="mt-5 rounded-xl border border-dashed border-neutral-700 p-8 text-center text-sm text-neutral-500">{t("proposal.empty")}</div> : (
          <div className="mt-5 rounded-xl border border-blue-800 bg-blue-950/25 p-4 sm:p-5">
            <div className="flex flex-col justify-between gap-4 sm:flex-row">
              <div><div className="flex flex-wrap items-center gap-2"><ClassificationBadge value="RECOMMENDATION" /><span className={`rounded px-2 py-0.5 font-mono text-xs ${proposal.status === "PENDING" ? "bg-amber-950 text-amber-300" : proposal.status === "APPROVED" ? "bg-emerald-950 text-emerald-300" : "bg-red-950 text-red-300"}`}>{proposal.status}</span></div><h3 className="mt-3 text-lg font-medium text-white">{proposal.why}</h3></div>
              <div className="shrink-0 sm:text-right"><div className="font-mono text-2xl font-semibold text-emerald-400">+{proposal.expectedBenefitMinutes}m</div><div className="text-xs text-neutral-500">{t("proposal.expectedBenefit")}</div></div>
            </div>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              <div><h4 className="text-xs font-semibold uppercase text-neutral-500">{t("proposal.evidence")}</h4><ul className="mt-2 space-y-2 text-sm text-neutral-300">{proposal.evidence.map((item) => <li key={item.evidenceId}>• {item.description}</li>)}</ul></div>
              <div><h4 className="text-xs font-semibold uppercase text-neutral-500">{t("proposal.ordering")}</h4><ul className="mt-2 space-y-2 text-sm text-neutral-300">{proposal.proposedChanges.map((change) => <li key={`${change.sceneId}-${change.toPosition}`}><span className="font-mono text-blue-300">{change.sceneId}</span> · {change.fromPosition} → {change.toPosition}</li>)}</ul><p className="mt-3 text-xs text-neutral-500">{t("proposal.affected")}: {proposal.affectedScenes.join(", ")}</p></div>
              <div><h4 className="text-xs font-semibold uppercase text-neutral-500">{t("proposal.risks")}</h4><ul className="mt-2 space-y-2 text-sm text-neutral-300">{proposal.risks.map((risk, index) => <li key={`${risk.severity}-${index}`}>• {risk.description} <span className="text-neutral-500">({risk.severity})</span></li>)}</ul><p className="mt-3 text-xs text-neutral-400">{t("proposal.confidence")}: <strong className="font-mono text-white">{Math.round(proposal.confidence * 100)}%</strong></p></div>
            </div>
            {proposal.status === "PENDING" ? <div className="mt-6 flex flex-col gap-3 border-t border-blue-900 pt-5 sm:flex-row"><button className="rounded-lg bg-emerald-600 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50" onClick={() => void run({ operation: "APPROVE", proposalId: proposal.proposalId })} disabled={busy !== null}>{busy === "APPROVE" ? t("working") : t("proposal.approve")}</button><button className="rounded-lg border border-red-800 bg-red-950 px-5 py-3 text-sm font-semibold text-red-200 hover:bg-red-900 disabled:opacity-50" onClick={() => void run({ operation: "REJECT", proposalId: proposal.proposalId })} disabled={busy !== null}>{busy === "REJECT" ? t("working") : t("proposal.reject")}</button><span className="self-center text-xs text-neutral-500">{t("proposal.humanOnly")}</span></div> : <div className="mt-5 rounded-lg border border-fuchsia-900 bg-fuchsia-950/40 p-3 text-sm text-fuchsia-200"><ClassificationBadge value="HUMAN_DECISION" /> <span className="ml-2">{proposal.status === "APPROVED" ? t("proposal.approvedHuman") : t("proposal.rejectedHuman")}</span></div>}
          </div>
        )}
      </section>
      <section className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-400">03 · {t("schedule.eyebrow")}</div>
        <h2 className="mt-2 text-xl font-semibold text-white">{t("schedule.title")}</h2>
        <p className="mt-1 text-sm text-neutral-500">{t("schedule.description")}</p>
        <div className={`mt-5 grid gap-4 ${after ? "lg:grid-cols-2" : "grid-cols-1"}`}>
          <ScheduleColumn title={after ? t("schedule.before") : t("schedule.current")} entries={before} />
          {after ? <ScheduleColumn title={t("schedule.after")} entries={after} /> : null}
        </div>
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-400">04 · {t("coverage.eyebrow")}</div>
          <h2 className="mt-2 text-xl font-semibold text-white">{t("coverage.title")}</h2>
          <p className="mt-1 text-sm leading-6 text-neutral-400">{t("coverage.description")}</p>
          <button className="mt-5 w-full rounded-lg border border-amber-700 bg-amber-950 px-5 py-3 text-sm font-semibold text-amber-200 hover:bg-amber-900 disabled:opacity-50 sm:w-auto" onClick={() => void run({ operation: "CHECK_COVERAGE" })} disabled={busy !== null}>{busy === "CHECK_COVERAGE" ? t("coverage.running") : t("coverage.button")}</button>
          {state.coverage.fact ? <div className="mt-5 space-y-3 rounded-xl border border-amber-900 bg-amber-950/30 p-4 text-sm"><div><ClassificationBadge value="FACT" /> <span className="ml-2 text-neutral-300">{state.coverage.fact.completedShotCount}/{state.coverage.fact.plannedShotCount} {t("coverage.completed")}</span></div><div><ClassificationBadge value="INFERENCE" /> <span className="ml-2 text-neutral-300">{state.coverage.alert?.description}</span></div><div className="font-mono text-xs text-neutral-500">{t("coverage.missing")}: {state.coverage.fact.missingShotIds.join(", ")}</div></div> : null}
        </div>
        <div className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-fuchsia-400">05 · {t("timeline.eyebrow")}</div>
          <h2 className="mt-2 text-xl font-semibold text-white">{t("timeline.title")}</h2>
          <div className="demo-scroll mt-5 max-h-[28rem] space-y-3 overflow-y-auto pr-1">
            {state.timeline.length === 0 ? <div className="text-sm text-neutral-500">{t("timeline.empty")}</div> : state.timeline.map((event) => <div key={event.eventId} className="rounded-lg border border-neutral-800 bg-neutral-950/60 p-3"><div className="flex flex-wrap items-center justify-between gap-2"><ClassificationBadge value={event.classification} /><time className="font-mono text-[10px] text-neutral-600">{new Date(event.timestamp).toLocaleTimeString()}</time></div><div className="mt-2 font-mono text-xs text-neutral-300">{event.type}</div><div className="mt-1 truncate text-xs text-neutral-500">{Object.entries(event.payload).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`).join(" · ")}</div></div>)}
          </div>
        </div>
      </section>
      <details className="rounded-2xl border border-neutral-800 bg-neutral-900/80 p-5 sm:p-6">
        <summary className="cursor-pointer list-none text-sm font-semibold text-blue-300">{t("evidence.title")}</summary>
        <p className="mt-2 text-xs leading-5 text-neutral-500">{t("evidence.description")}</p>
        {state.technicalEvidence ? <dl className="mt-5 grid gap-3 text-xs sm:grid-cols-2 lg:grid-cols-3">
          {[
            [t("evidence.provider"), state.technicalEvidence.provider],
            [t("evidence.agent"), state.technicalEvidence.agentName],
            [t("evidence.model"), state.technicalEvidence.modelName || "—"],
            [t("evidence.execution"), state.technicalEvidence.executionId],
            [t("evidence.session"), state.technicalEvidence.sessionId],
            [t("evidence.correlation"), state.technicalEvidence.correlationId],
            [t("evidence.duration"), `${state.technicalEvidence.durationMs ?? "—"} ms`],
            [t("evidence.tools"), state.technicalEvidence.toolNames.join(", ")],
            [t("evidence.references"), state.technicalEvidence.evidenceReferences.join(", ")],
          ].map(([label, value]) => <div key={label} className="min-w-0 rounded-lg border border-neutral-800 bg-neutral-950 p-3"><dt className="text-neutral-500">{label}</dt><dd className="mt-1 break-all font-mono text-neutral-200">{value}</dd></div>)}
          <div className="rounded-lg border border-neutral-800 bg-neutral-950 p-3 sm:col-span-2 lg:col-span-3"><dt className="text-neutral-500">{t("evidence.rationale")}</dt><dd className="mt-1 text-neutral-200">{state.technicalEvidence.shortRationale}</dd></div>
        </dl> : <div className="mt-4 text-sm text-neutral-500">{t("evidence.empty")}</div>}
      </details>
    </div>
  );
}

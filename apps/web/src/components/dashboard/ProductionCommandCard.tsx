"use client";

import { FormEvent, useState } from "react";
import { useLocale } from "next-intl";

import type { DemoState } from "@/lib/demo/types";

const COPY = {
  en: {
    eyebrow: "Production Command",
    title: "Give StudioGrid the problem, not the steps",
    description: "Write the production goal once. StudioGrid routes it to the right agent and returns the operational result.",
    placeholder: "Check SC_05 and make sure all required coverage is complete.",
    button: "Run production command",
    running: "StudioGrid is running the agent workflow...",
    supported: "Public build: exact actor-delay replanning and shot-coverage checks. Unsupported commands fail closed.",
    coverage: "Coverage · end-to-end",
    schedule: "Schedule · approval boundary",
    error: "Production Command failed safely.",
  },
  ru: {
    eyebrow: "Команда производству",
    title: "Опишите StudioGrid проблему, а не шаги",
    description: "Сформулируйте производственную задачу один раз. StudioGrid сам направит её нужному агенту и покажет рабочий результат.",
    placeholder: "Проверь SC_05 и убедись, что все обязательные кадры сняты.",
    button: "Выполнить производственную команду",
    running: "StudioGrid выполняет агентный сценарий...",
    supported: "Публичная версия: точные сценарии задержки актёров и проверка покрытия кадрами. Остальные команды безопасно отклоняются.",
    coverage: "Покрытие · от начала до конца",
    schedule: "Расписание · с границей одобрения",
    error: "Команда производству безопасно завершилась ошибкой.",
  },
} as const;

const EXAMPLES = {
  en: {
    coverage: "Check SC_05 and make sure all required coverage is complete.",
    schedule: "Maya Reed is 45 minutes late. Keep today's shoot on schedule.",
  },
  ru: {
    coverage: "Проверь SC_05 и убедись, что все обязательные кадры сняты.",
    schedule: "Maya Reed задерживается на 45 минут. Сохрани сегодняшний съёмочный план.",
  },
} as const;

export function ProductionCommandCard({
  onState,
}: {
  onState?: (state: DemoState) => void;
}) {
  const locale = useLocale() === "ru" ? "ru" : "en";
  const copy = COPY[locale];
  const examples = EXAMPLES[locale];
  const [command, setCommand] = useState<string>(examples.coverage);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = command.trim();
    if (normalized.length < 4 || normalized.length > 500) return;

    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operation: "COMMAND", command: normalized }),
      });
      const payload = (await response.json()) as DemoState & { error?: { message?: string } };
      if (!response.ok) throw new Error(payload.error?.message || copy.error);
      onState?.(payload);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : copy.error);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mx-auto mt-6 max-w-screen-xl px-4">
      <div className="overflow-hidden rounded-2xl border border-cyan-800/80 bg-gradient-to-br from-cyan-950/70 via-neutral-950 to-neutral-950 p-5 shadow-2xl shadow-cyan-950/20 sm:p-6">
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">{copy.eyebrow}</div>
        <h2 className="mt-2 text-xl font-semibold text-white sm:text-2xl">{copy.title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">{copy.description}</p>

        <form className="mt-5" onSubmit={submit}>
          <textarea
            className="min-h-28 w-full resize-y rounded-xl border border-neutral-700 bg-neutral-950 px-4 py-3 text-sm leading-6 text-white outline-none transition placeholder:text-neutral-600 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-900 disabled:opacity-60"
            value={command}
            maxLength={500}
            onChange={(event) => setCommand(event.target.value)}
            placeholder={copy.placeholder}
            disabled={busy}
            aria-label={copy.eyebrow}
          />
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap gap-2">
              <button type="button" className="rounded-full border border-amber-800 bg-amber-950/50 px-3 py-1.5 text-xs text-amber-200 hover:bg-amber-900/60 disabled:opacity-50" onClick={() => setCommand(examples.coverage)} disabled={busy}>{copy.coverage}</button>
              <button type="button" className="rounded-full border border-blue-800 bg-blue-950/50 px-3 py-1.5 text-xs text-blue-200 hover:bg-blue-900/60 disabled:opacity-50" onClick={() => setCommand(examples.schedule)} disabled={busy}>{copy.schedule}</button>
            </div>
            <button type="submit" className="rounded-lg bg-cyan-600 px-5 py-3 text-sm font-semibold text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50" disabled={busy || command.trim().length < 4}>{busy ? copy.running : copy.button}</button>
          </div>
        </form>

        <p className="mt-3 text-xs leading-5 text-neutral-500">{copy.supported}</p>
        {error ? <div role="alert" className="mt-4 rounded-lg border border-red-800 bg-red-950/60 p-3 text-sm text-red-200">{error}</div> : null}
      </div>
    </section>
  );
}

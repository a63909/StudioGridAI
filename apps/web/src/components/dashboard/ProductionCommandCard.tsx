"use client";

import { FormEvent, useState } from "react";
import { useLocale } from "next-intl";

import type { DemoState } from "@/lib/demo/types";

const COPY = {
  en: {
    prompt: "What happened or what needs to be done?",
    description: "Describe the production goal once. StudioGrid will route it and return the operational result here.",
    placeholder: "Check SC_05 and make sure all required coverage is complete.",
    button: "Run",
    running: "StudioGrid is running the agent workflow...",
    supported: "Public build: exact actor-delay replanning and shot-coverage checks. Unsupported commands fail closed.",
    examples: "Try:",
    coverage: "Check coverage",
    schedule: "Actor delay",
    error: "Production Command failed safely.",
  },
  ru: {
    prompt: "Что произошло или что нужно сделать?",
    description: "Опишите производственную задачу один раз. StudioGrid направит её и покажет здесь рабочий результат.",
    placeholder: "Проверь SC_05 и убедись, что все обязательные кадры сняты.",
    button: "Выполнить",
    running: "StudioGrid выполняет агентный сценарий...",
    supported: "Публичная версия: точные сценарии задержки актёров и проверка покрытия кадрами. Остальные команды безопасно отклоняются.",
    examples: "Например:",
    coverage: "Проверить покрытие",
    schedule: "Задержка актёра",
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
    <div className="mt-7 border-t border-blue-900/70 pt-6" data-testid="studio-command-control">
      <label className="text-base font-semibold text-white" htmlFor="studio-production-command">{copy.prompt}</label>
      <p className="mt-1 max-w-3xl text-sm leading-6 text-neutral-400">{copy.description}</p>

      <form className="mt-4" onSubmit={submit}>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch">
          <textarea
            id="studio-production-command"
            className="min-h-24 w-full flex-1 resize-y rounded-xl border border-neutral-700 bg-neutral-950/80 px-4 py-3 text-sm leading-6 text-white outline-none transition placeholder:text-neutral-600 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-900 disabled:opacity-60"
            value={command}
            maxLength={500}
            onChange={(event) => setCommand(event.target.value)}
            placeholder={copy.placeholder}
            disabled={busy}
          />
          <button type="submit" className="rounded-lg bg-cyan-600 px-6 py-3 text-sm font-semibold text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50 lg:self-end" disabled={busy || command.trim().length < 4}>{busy ? copy.running : copy.button}</button>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-neutral-500">{copy.examples}</span>
          <button type="button" className="rounded-full border border-neutral-700 bg-neutral-950/60 px-3 py-1.5 text-neutral-300 hover:border-amber-700 hover:text-amber-200 disabled:opacity-50" onClick={() => setCommand(examples.coverage)} disabled={busy}>{copy.coverage}</button>
          <button type="button" className="rounded-full border border-neutral-700 bg-neutral-950/60 px-3 py-1.5 text-neutral-300 hover:border-blue-700 hover:text-blue-200 disabled:opacity-50" onClick={() => setCommand(examples.schedule)} disabled={busy}>{copy.schedule}</button>
        </div>
      </form>

      <p className="mt-3 text-xs leading-5 text-neutral-500">{copy.supported}</p>
      {error ? <div role="alert" className="mt-4 rounded-lg border border-red-800 bg-red-950/60 p-3 text-sm text-red-200">{error}</div> : null}
    </div>
  );
}

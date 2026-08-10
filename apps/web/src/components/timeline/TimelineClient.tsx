"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";

interface EventEntry {
  eventId: string;
  type: string;
  timestamp: string;
  source: string;
  payload: Record<string, unknown>;
}

const EVENT_TYPE_COLORS: Record<string, string> = {
  SHOOT_DAY_STARTED: "text-green-400",
  SHOOT_DAY_WRAPPED: "text-green-400",
  SHOT_STARTED: "text-blue-400",
  SHOT_COMPLETED: "text-blue-300",
  SHOT_FAILED: "text-red-400",
  ACTOR_DELAYED: "text-orange-400",
  ACTOR_AVAILABLE: "text-green-400",
  SCHEDULE_PROPOSAL_CREATED: "text-yellow-400",
  SCHEDULE_PROPOSAL_APPROVED: "text-green-400",
  SCHEDULE_PROPOSAL_REJECTED: "text-red-400",
  CONTINUITY_ALERT_CREATED: "text-yellow-300",
  COVERAGE_ALERT_CREATED: "text-orange-300",
  RISK_CREATED: "text-orange-400",
};

export function TimelineClient() {
  const t = useTranslations("timeline");
  const [events, setEvents] = useState<EventEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const source = new EventSource(`${apiUrl}/events/stream`);

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);

    source.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "HEARTBEAT" || data.type === "DASHBOARD_STATS") return;
        setEvents((prev) => [...prev.slice(-200), data]);
      } catch {
        // ignore parse errors
      }
    };

    return () => source.close();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">{t("title")}</h1>
        <span
          className={`text-xs font-mono px-2 py-0.5 rounded ${
            connected
              ? "bg-green-950 text-green-400 border border-green-800"
              : "bg-neutral-800 text-neutral-400"
          }`}
        >
          {connected ? t("connected") : t("connecting")}
        </span>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 h-[60vh] overflow-y-auto font-mono text-xs space-y-1">
        {events.length === 0 ? (
          <div className="text-neutral-500">{t("noEvents")}</div>
        ) : (
          events.map((evt) => (
            <div key={evt.eventId} className="flex gap-3">
              <span className="text-neutral-600 shrink-0">
                {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : "--:--:--"}
              </span>
              <span
                className={`font-semibold shrink-0 ${
                  EVENT_TYPE_COLORS[evt.type] || "text-neutral-300"
                }`}
              >
                {evt.type}
              </span>
              <span className="text-neutral-400 truncate">
                {JSON.stringify(evt.payload)}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

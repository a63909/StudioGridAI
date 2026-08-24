"use client";

import { useCallback, useState } from "react";

import type { CommandRouting, DemoState } from "@/lib/demo/types";

import { DashboardClient } from "./DashboardClient";

type ActiveIntent = CommandRouting["intent"];

export function ProductionCommandDashboard() {
  const [commandState, setCommandState] = useState<DemoState | null>(null);
  const [activeIntent, setActiveIntent] = useState<ActiveIntent | null>(null);
  const [commandRouting, setCommandRouting] = useState<CommandRouting | null>(null);

  const handleCommandState = useCallback((state: DemoState) => {
    setCommandState(state);
    setActiveIntent(state.commandRouting?.intent || null);
    setCommandRouting(state.commandRouting || null);
  }, []);

  const handleDashboardState = useCallback((state: DemoState) => {
    setCommandState(state);
  }, []);

  const handleActiveIntentChange = useCallback((intent: ActiveIntent | null) => {
    setActiveIntent(intent);
    setCommandRouting((current) => current?.intent === intent ? current : null);
  }, []);

  return (
    <DashboardClient
      state={commandState}
      onState={handleDashboardState}
      onCommandState={handleCommandState}
      activeIntent={activeIntent}
      commandRouting={commandRouting}
      onActiveIntentChange={handleActiveIntentChange}
    />
  );
}

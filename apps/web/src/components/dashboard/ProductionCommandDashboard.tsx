"use client";

import { useState } from "react";

import type { CommandRouting, DemoState } from "@/lib/demo/types";

import { DashboardClient } from "./DashboardClient";
import { ProductionCommandCard } from "./ProductionCommandCard";

type ActiveIntent = CommandRouting["intent"];

export function ProductionCommandDashboard() {
  const [commandState, setCommandState] = useState<DemoState | null>(null);
  const [activeIntent, setActiveIntent] = useState<ActiveIntent | null>(null);

  const handleCommandState = (state: DemoState) => {
    setCommandState(state);
    setActiveIntent(state.commandRouting?.intent || null);
  };

  return (
    <>
      <ProductionCommandCard onState={handleCommandState} />
      <DashboardClient
        state={commandState}
        onState={setCommandState}
        activeIntent={activeIntent}
        onActiveIntentChange={setActiveIntent}
      />
    </>
  );
}

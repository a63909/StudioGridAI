"use client";

import { useState } from "react";

import type { CommandRouting, DemoState } from "@/lib/demo/types";

import { DashboardClient } from "./DashboardClient";
import { ProductionCommandCard } from "./ProductionCommandCard";

export function ProductionCommandDashboard() {
  const [commandState, setCommandState] = useState<DemoState | null>(null);
  const [activeRouting, setActiveRouting] = useState<CommandRouting | null>(null);

  const handleCommandState = (state: DemoState) => {
    setCommandState(state);
    setActiveRouting(state.commandRouting || null);
  };

  return (
    <>
      <ProductionCommandCard onState={handleCommandState} />
      <DashboardClient
        state={commandState}
        onState={setCommandState}
        activeRouting={activeRouting}
        onActiveRoutingChange={setActiveRouting}
      />
    </>
  );
}

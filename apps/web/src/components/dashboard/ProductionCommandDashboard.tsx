"use client";

import { useState } from "react";

import type { DemoState } from "@/lib/demo/types";

import { DashboardClient } from "./DashboardClient";
import { ProductionCommandCard } from "./ProductionCommandCard";

export function ProductionCommandDashboard() {
  const [commandState, setCommandState] = useState<DemoState | null>(null);

  return (
    <>
      <ProductionCommandCard onState={setCommandState} />
      <DashboardClient state={commandState} onState={setCommandState} />
    </>
  );
}

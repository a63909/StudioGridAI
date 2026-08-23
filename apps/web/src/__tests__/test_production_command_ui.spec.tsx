import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProductionCommandCard } from "../components/dashboard/ProductionCommandCard";
import type { DemoState } from "../lib/demo/types";

vi.mock("next-intl", () => ({
  useLocale: () => "en",
}));

describe("Production Command UI", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the operational coverage result without a second user action", async () => {
    const payload = {
      commandRouting: {
        provider: "Google Vertex AI",
        modelName: "gemini-3.6-flash",
        intent: "CHECK_COVERAGE",
        target: "COVERAGE_AGENT",
        summary: "Route to the fixed coverage workflow.",
      },
      coverage: {
        fact: {
          sceneId: "SC_05",
          plannedShotCount: 3,
          completedShotCount: 1,
          missingShotIds: ["SH_12", "SH_13"],
          coveragePercent: 33.3,
          classification: "FACT",
        },
        alert: {
          alertId: "ALERT_1",
          sceneId: "SC_05",
          missingShotIds: ["SH_12", "SH_13"],
          severity: "HIGH",
          description: "Required coverage remains incomplete.",
          status: "OPEN",
        },
      },
      proposal: null,
    } as unknown as DemoState;
    const onState = vi.fn();
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => payload,
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ProductionCommandCard onState={onState} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Run production command" }),
    );

    await waitFor(() => expect(onState).toHaveBeenCalledWith(payload));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/demo",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          operation: "COMMAND",
          command: "Check SC_05 and make sure all required coverage is complete.",
        }),
      }),
    );

    expect(screen.getByText("Coverage check complete")).toBeInTheDocument();
    expect(screen.getByText(/SC_05: Required coverage is incomplete/)).toBeInTheDocument();
    expect(screen.getByText("SH_12")).toBeInTheDocument();
    expect(screen.getByText("SH_13")).toBeInTheDocument();
    expect(screen.getByText("OPEN")).toBeInTheDocument();
    expect(screen.getByText("Technical execution details")).toBeInTheDocument();
  });
});

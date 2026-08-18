import "server-only";

import { GoogleAuth } from "google-auth-library";
import type { DemoState } from "./types";

interface ControlEnvironment {
  CONTROL_API_URL?: string;
  CONTROL_API_AUDIENCE?: string;
}

export interface ControlConfiguration {
  baseUrl: string;
  audience: string;
}

export function validateControlConfiguration(
  env: ControlEnvironment = {
    CONTROL_API_URL: process.env.CONTROL_API_URL,
    CONTROL_API_AUDIENCE: process.env.CONTROL_API_AUDIENCE,
  },
): ControlConfiguration {
  const baseUrl = (env.CONTROL_API_URL || "").replace(/\/$/, "");
  const audience = (env.CONTROL_API_AUDIENCE || "").replace(/\/$/, "");
  if (!baseUrl || !audience || baseUrl !== audience) {
    throw new Error("CONTROL_API_CONFIGURATION_ERROR");
  }
  const parsed = new URL(baseUrl);
  if (parsed.protocol !== "https:" || parsed.username || parsed.password || parsed.pathname !== "/") {
    throw new Error("CONTROL_API_CONFIGURATION_ERROR");
  }
  return { baseUrl, audience };
}

export class ControlRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly safeMessage: string,
  ) {
    super(code);
  }
}

export async function controlRequest(
  method: "GET" | "POST",
  path: string,
  body?: Record<string, unknown>,
): Promise<DemoState> {
  const { baseUrl, audience } = validateControlConfiguration();
  if (!path.startsWith("/control/") || path.includes("..")) {
    throw new Error("CONTROL_PATH_NOT_ALLOWED");
  }
  const auth = new GoogleAuth();
  const client = await auth.getIdTokenClient(audience);
  try {
    const response = await client.request<DemoState>({
      url: `${baseUrl}${path}`,
      method,
      data: body,
      timeout: 180_000,
      headers: { "Content-Type": "application/json" },
    });
    return response.data;
  } catch (error: unknown) {
    const candidate = error as {
      response?: { status?: number; data?: { detail?: { code?: string; message?: string } } };
    };
    const detail = candidate.response?.data?.detail;
    throw new ControlRequestError(
      candidate.response?.status || 502,
      detail?.code || "CONTROL_API_ERROR",
      detail?.message || "The private control service could not complete the request.",
    );
  }
}

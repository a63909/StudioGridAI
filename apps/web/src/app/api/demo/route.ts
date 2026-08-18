import { randomUUID } from "crypto";
import { NextRequest, NextResponse } from "next/server";

import { controlRequest, ControlRequestError } from "@/lib/demo/control-client";
import { consumeDemoRateLimit } from "@/lib/demo/rate-limit";
import { parseDemoAction } from "@/lib/demo/validation";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const COOKIE_NAME = "studiogrid_demo_session";
const SESSION_ID = /^[A-Za-z0-9_-]{16,80}$/;
const MAX_BODY_BYTES = 2048;

function session(request: NextRequest): { id: string; created: boolean } {
  const current = request.cookies.get(COOKIE_NAME)?.value;
  if (current && SESSION_ID.test(current)) return { id: current, created: false };
  return { id: randomUUID(), created: true };
}

function responseWithSession(payload: unknown, status: number, sessionId: string, created: boolean) {
  const response = NextResponse.json(payload, { status });
  response.headers.set("Cache-Control", "no-store");
  if (created) {
    response.cookies.set(COOKIE_NAME, sessionId, {
      httpOnly: true,
      secure: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 4,
    });
  }
  return response;
}

function safeError(error: unknown, sessionId: string, created: boolean) {
  if (error instanceof ControlRequestError) {
    return responseWithSession(
      { error: { code: error.code, message: error.safeMessage } },
      error.status,
      sessionId,
      created,
    );
  }
  return responseWithSession(
    { error: { code: "DEMO_REQUEST_FAILED", message: "The cloud demo request failed safely." } },
    400,
    sessionId,
    created,
  );
}

export async function GET(request: NextRequest) {
  const demo = session(request);
  try {
    const state = await controlRequest(
      "GET",
      `/control/state?demoSessionId=${encodeURIComponent(demo.id)}`,
    );
    return responseWithSession(state, 200, demo.id, demo.created);
  } catch (error) {
    return safeError(error, demo.id, demo.created);
  }
}

export async function POST(request: NextRequest) {
  const demo = session(request);
  const contentLength = Number(request.headers.get("content-length") || "0");
  if (contentLength > MAX_BODY_BYTES) {
    return responseWithSession(
      { error: { code: "REQUEST_TOO_LARGE", message: "Demo request is too large." } },
      413,
      demo.id,
      demo.created,
    );
  }
  const text = await request.text();
  if (Buffer.byteLength(text, "utf8") > MAX_BODY_BYTES) {
    return responseWithSession(
      { error: { code: "REQUEST_TOO_LARGE", message: "Demo request is too large." } },
      413,
      demo.id,
      demo.created,
    );
  }
  try {
    const action = parseDemoAction(JSON.parse(text));
    const ip = (request.headers.get("x-forwarded-for") || "unknown").split(",")[0].trim();
    const retryAfter = consumeDemoRateLimit(demo.id, ip);
    if (retryAfter) {
      const limited = responseWithSession(
        { error: { code: "RATE_LIMITED", message: "Please wait before the next demo action." } },
        429,
        demo.id,
        demo.created,
      );
      limited.headers.set("Retry-After", String(retryAfter));
      return limited;
    }
    const body = { ...action, demoSessionId: demo.id };
    const route = {
      RESET: "/control/reset",
      ACTOR_DELAY: "/control/actor-delay",
      APPROVE: "/control/proposal/approve",
      REJECT: "/control/proposal/reject",
      CHECK_COVERAGE: "/control/coverage",
    }[action.operation];
    const controlBody = Object.fromEntries(
      Object.entries(body).filter(([key]) => key !== "operation"),
    );
    const state = await controlRequest("POST", route, controlBody);
    return responseWithSession(state, 200, demo.id, demo.created);
  } catch (error) {
    return safeError(error, demo.id, demo.created);
  }
}

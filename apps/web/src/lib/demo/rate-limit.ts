const WINDOW_MS = 60_000;
const SESSION_LIMIT = 12;
const IP_LIMIT = 30;

interface Bucket {
  startedAt: number;
  count: number;
}

const buckets = new Map<string, Bucket>();

function consume(key: string, limit: number, now: number): number | null {
  const current = buckets.get(key);
  if (!current || now - current.startedAt >= WINDOW_MS) {
    buckets.set(key, { startedAt: now, count: 1 });
    return null;
  }
  if (current.count >= limit) {
    return Math.max(1, Math.ceil((WINDOW_MS - (now - current.startedAt)) / 1000));
  }
  current.count += 1;
  return null;
}

export function consumeDemoRateLimit(sessionId: string, ip: string, now = Date.now()): number | null {
  return consume(`session:${sessionId}`, SESSION_LIMIT, now) ?? consume(`ip:${ip}`, IP_LIMIT, now);
}

export function resetDemoRateLimitsForTests(): void {
  buckets.clear();
}

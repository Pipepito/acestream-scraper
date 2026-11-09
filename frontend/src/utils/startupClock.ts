export interface ClockSample {
  serverTime: number;
  browserTime: number;
  differenceMs: number;
}

/** A comparison hint, never a trusted time source or startup prerequisite. */
export function startupClockSample(
  serverTime: string | null | undefined,
  startedAt: number,
  receivedAt: number,
  elapsedMs: number,
): ClockSample | undefined {
  if (!serverTime || !/(Z|[+-]\d{2}:\d{2})$/.test(serverTime)
      || !Number.isFinite(elapsedMs) || elapsedMs < 0 || elapsedMs > 5000
      || Math.abs(receivedAt - startedAt - elapsedMs) > 1000) return undefined;
  const server = Date.parse(serverTime);
  if (!Number.isFinite(server)) return undefined;
  const browser = startedAt + elapsedMs / 2;
  return { serverTime: server, browserTime: browser, differenceMs: server - browser };
}

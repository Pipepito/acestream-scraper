/** Small readiness helpers shared by global setup and specs (Node 22 global fetch). */
export async function httpOk(url: string, timeoutMs = 5_000): Promise<boolean> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { signal: controller.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function waitForHttp(url: string, timeoutMs: number, label = url, intervalMs = 2_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await httpOk(url)) return;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error(`Timed out after ${timeoutMs} ms waiting for ${label} (${url})`);
}

export interface PollOptions {
  timeoutMs: number;
  intervalMs?: number;
  label?: string;
}

/** Poll `probe` until `done(value)` is true; returns the final value or throws with the last value. */
export async function pollUntil<T>(probe: () => Promise<T>, done: (value: T) => boolean, opts: PollOptions): Promise<T> {
  const deadline = Date.now() + opts.timeoutMs;
  const interval = opts.intervalMs ?? 2_000;
  let last: T | undefined;
  while (Date.now() < deadline) {
    last = await probe();
    if (done(last)) return last;
    await new Promise((r) => setTimeout(r, interval));
  }
  throw new Error(`Timed out after ${opts.timeoutMs} ms waiting for ${opts.label ?? 'condition'}; last value: ${JSON.stringify(last)?.slice(0, 500)}`);
}

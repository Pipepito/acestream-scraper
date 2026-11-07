import { existsSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import type { Page, TestInfo } from '@playwright/test';

export interface ErrorPolicy {
  allowedApiErrorPatterns: string[];
  allowedConsolePatterns: string[];
}

export interface ApiFailure {
  method: string;
  url: string;
  status: number;
  body: string;
}

interface Snapshot {
  file: string;
  offset: number;
}

const LOG_LINE = /ERROR|CRITICAL|Traceback|Exception|database is locked|OperationalError/;

/**
 * Watches one page the way a support engineer would: browser console errors,
 * uncaught page errors, failed `/api` responses and new ERROR/Traceback lines
 * in the backend logs. Everything is attached to the test report; with
 * E2E_STRICT=1 an unexpected error fails the test.
 */
export class ErrorMonitor {
  readonly consoleErrors: string[] = [];
  readonly pageErrors: string[] = [];
  readonly apiFailures: ApiFailure[] = [];
  readonly cancelledReads: ApiFailure[] = [];
  readonly backendErrors: string[] = [];
  private readonly extraAllowedApi: RegExp[] = [];
  private readonly extraAllowedConsole: RegExp[] = [];
  private readonly extraAllowedBackend: RegExp[] = [];
  private snapshots: Snapshot[] = [];

  constructor(private readonly page: Page, private readonly policy: ErrorPolicy) {}

  static backendLogFiles(): string[] {
    const e2eDir = path.resolve(__dirname, '..');
    const candidates = [
      process.env.E2E_BACKEND_LOG ?? path.join(e2eDir, '.stack', 'backend.log'),
      path.join(e2eDir, '..', 'backend', 'logs', 'acestream.log'),
    ];
    // uvicorn's stdout already carries the app logger output, so watch one file only.
    const first = candidates.find((f) => existsSync(f));
    return first ? [first] : [];
  }

  async start(): Promise<void> {
    this.snapshots = ErrorMonitor.backendLogFiles().map((file) => ({ file, offset: statSync(file).size }));
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') this.consoleErrors.push(msg.text());
    });
    this.page.on('pageerror', (err) => this.pageErrors.push(String(err?.stack ?? err)));
    this.page.on('response', async (res) => {
      const url = res.url();
      if (!url.includes('/api/') || res.status() < 400) return;
      let body = '';
      try {
        body = (await res.text()).slice(0, 300);
      } catch {
        /* body may be unavailable */
      }
      this.apiFailures.push({ method: res.request().method(), url, status: res.status(), body });
    });
    this.page.on('requestfailed', (req) => {
      if (req.url().includes('/api/')) {
        const failure = { method: req.method(), url: req.url(), status: 0, body: req.failure()?.errorText ?? 'request failed' };
        // Navigation and player teardown cancel in-flight reads. Keep these in
        // the evidence, but distinguish explicit browser cancellation from an
        // HTTP error, a transport failure, or an interrupted mutation.
        if (['GET', 'HEAD'].includes(failure.method)
          && ['NS_BINDING_ABORTED', 'net::ERR_ABORTED', 'cancelled'].includes(failure.body)) {
          this.cancelledReads.push(failure);
        } else {
          this.apiFailures.push(failure);
        }
      }
    });
  }

  /** Declare an API failure the test deliberately provokes (e.g. validation 400). */
  allowApi(pattern: RegExp): void {
    this.extraAllowedApi.push(pattern);
  }
  allowConsole(pattern: RegExp): void {
    this.extraAllowedConsole.push(pattern);
  }
  /** A specific backend error deliberately provoked by this test only. */
  allowBackend(pattern: RegExp): void {
    this.extraAllowedBackend.push(pattern);
  }

  private collectBackendErrors(): void {
    for (const snap of this.snapshots) {
      if (!existsSync(snap.file)) continue;
      const size = statSync(snap.file).size;
      if (size <= snap.offset) continue;
      const text = readFileSync(snap.file, 'utf8').slice(snap.offset);
      const lines = text.split('\n');
      for (let i = 0; i < lines.length; i += 1) {
        if (LOG_LINE.test(lines[i])) {
          // keep a little context after tracebacks
          this.backendErrors.push(`${path.basename(snap.file)}: ${lines.slice(i, i + 3).join(' | ').slice(0, 600)}`);
        }
      }
    }
  }

  private unexpectedApi(): ApiFailure[] {
    const allowed = [...this.policy.allowedApiErrorPatterns.map((p) => new RegExp(p)), ...this.extraAllowedApi];
    return this.apiFailures.filter((f) => !allowed.some((re) => re.test(`${f.method} ${f.url} ${f.status} ${f.body}`)));
  }
  private unexpectedConsole(): string[] {
    const allowed = [...this.policy.allowedConsolePatterns.map((p) => new RegExp(p)), ...this.extraAllowedConsole];
    return [...this.consoleErrors, ...this.pageErrors].filter((m) => !allowed.some((re) => re.test(m)));
  }

  async finish(testInfo: TestInfo): Promise<void> {
    this.collectBackendErrors();
    const api = this.unexpectedApi();
    const consoleMsgs = this.unexpectedConsole();
    const backend = this.backendErrors.filter((line) => !this.extraAllowedBackend.some((pattern) => pattern.test(line)));
    const report = {
      apiFailures: api,
      consoleErrors: consoleMsgs,
      backendErrors: backend,
      allBackendErrors: this.backendErrors,
      allApiFailures: this.apiFailures,
      cancelledReads: this.cancelledReads,
    };
    const total = api.length + consoleMsgs.length + backend.length;
    if (total > 0 || this.apiFailures.length > 0 || this.backendErrors.length > 0 || this.cancelledReads.length > 0) {
      await testInfo.attach('error-monitor.json', { body: JSON.stringify(report, null, 2), contentType: 'application/json' });
    }
    if (total > 0) {
      const summary = [
        ...api.map((f) => `API ${f.status} ${f.method} ${f.url.replace(/^https?:\/\/[^/]+/, '')} ${f.body.replace(/\s+/g, ' ').slice(0, 160)}`),
        ...consoleMsgs.map((m) => `CONSOLE ${m.replace(/\s+/g, ' ').slice(0, 200)}`),
        ...backend.map((m) => `BACKEND ${m.replace(/\s+/g, ' ').slice(0, 200)}`),
      ].join('\n');
      testInfo.annotations.push({ type: 'errors-observed', description: summary });
      process.stdout.write(`\n[error-monitor] ${testInfo.title}\n${summary}\n`);
      if (process.env.E2E_STRICT === '1') {
        throw new Error(`Unexpected errors observed during "${testInfo.title}":\n${summary}`);
      }
    }
  }
}

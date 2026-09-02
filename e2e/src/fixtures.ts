import { test as base, expect } from '@playwright/test';
import { Api } from './api';
import { ErrorMonitor } from './error-monitor';
import { loadScenario, type Scenario } from './scenario/load';
import { AppShell } from './pages/app-shell';

interface Fixtures {
  scenario: Scenario;
  api: Api;
  app: AppShell;
  errors: ErrorMonitor;
}

/**
 * Shared test base: scenario data, typed API access, the app shell page object
 * and an always-on error monitor.
 */
export const test = base.extend<Fixtures>({
  scenario: async ({}, use: (s: Scenario) => Promise<void>) => {
    await use(loadScenario());
  },
  api: async ({ request, baseURL }, use) => {
    await use(new Api(request, baseURL ?? 'http://127.0.0.1:8000'));
  },
  app: async ({ page }, use) => {
    await use(new AppShell(page));
  },
  errors: [
    async ({ page, scenario }, use, testInfo) => {
      const monitor = new ErrorMonitor(page, scenario.errors);
      await monitor.start();
      await use(monitor);
      await monitor.finish(testInfo);
    },
    { auto: true },
  ],
});

export { expect };

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for the live-stack journey suite.
 *
 * - Firefox is the default browser (E2E_BROWSERS=firefox,chromium to add more).
 * - One worker, no parallelism: the app is a single SQLite database with a
 *   background scheduler; specs are ordered journeys that build on each other.
 * - E2E_BASE_URL selects the app under test (local backend on :8000 by default,
 *   the containerised app on :8001 with `npm run test:docker`).
 */
const baseURL = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:8000';
const browsers = (process.env.E2E_BROWSERS ?? 'firefox').split(',').map((b) => b.trim()).filter(Boolean);
const viewport = { width: 1440, height: 900 };

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180_000,
  expect: { timeout: 15_000 },
  outputDir: 'test-results',
  globalSetup: './src/global-setup.ts',
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'results/junit.xml' }],
    ['json', { outputFile: 'results/results.json' }],
  ],
  use: {
    baseURL,
    viewport,
    colorScheme: 'light',
    locale: 'en-US',
    timezoneId: 'Europe/Madrid',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 20_000,
    navigationTimeout: 45_000,
  },
  projects: browsers.map((name) => ({
    name,
    use: {
      ...(name === 'firefox' ? devices['Desktop Firefox'] : name === 'webkit' ? devices['Desktop Safari'] : devices['Desktop Chrome']),
      viewport,
    },
  })),
});

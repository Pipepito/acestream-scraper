import { defineConfig } from '@playwright/test';

/** Deterministic UI regression suite: mocked stream/guide responses, no live media needed. */
export default defineConfig({
  testDir: './mobile',
  fullyParallel: true,
  workers: 2,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:3010', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'phone-chromium', use: { browserName: 'chromium', viewport: { width: 390, height: 844 }, timezoneId: 'Europe/Madrid', hasTouch: true } },
    { name: 'small-phone-webkit', use: { browserName: 'webkit', viewport: { width: 320, height: 640 }, timezoneId: 'America/New_York', hasTouch: true } },
    { name: 'tablet-firefox', use: { browserName: 'firefox', viewport: { width: 768, height: 1024 }, timezoneId: 'Asia/Tokyo' } },
    { name: 'desktop-chromium', use: { browserName: 'chromium', viewport: { width: 1440, height: 900 }, timezoneId: 'UTC' } },
  ],
  webServer: {
    command: 'npm --prefix ../frontend run build && ../frontend/node_modules/.bin/vite preview --outDir ../frontend/dist --host 127.0.0.1 --port 3010',
    url: 'http://127.0.0.1:3010', reuseExistingServer: false,
  },
});

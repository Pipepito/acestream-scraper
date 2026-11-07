import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './monitor',
  workers: 1,
  retries: 0,
  timeout: 20_000,
  outputDir: 'test-results',
  reporter: 'list',
  projects: ['firefox', 'chromium', 'webkit'].map(browserName => ({
    name: browserName,
    use: { browserName: browserName as 'firefox' | 'chromium' | 'webkit' },
  })),
});

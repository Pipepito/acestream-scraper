import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './standalone',
  fullyParallel: true,
  workers: 2,
  retries: 0,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:3011/recipes/', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: ['chromium', 'firefox', 'webkit'].map(browserName => ({
    name: browserName,
    use: { browserName: browserName as 'chromium' | 'firefox' | 'webkit' },
  })),
  webServer: {
    command: 'python3 -m http.server 3011 --bind 127.0.0.1 --directory ../docs',
    url: 'http://127.0.0.1:3011/recipes/',
    reuseExistingServer: false,
  },
});

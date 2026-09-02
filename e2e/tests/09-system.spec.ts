import { test, expect } from '../src/fixtures';
import { DashboardPage, HealthPage, StatsPage, WarpPage } from '../src/pages/system';

test.describe('dashboard, health, stats, WARP', () => {
  test('dashboard shows readiness, scheduler jobs and persists its preferences', async ({ page, api }) => {
    const dashboard = new DashboardPage(page);
    await dashboard.open();
    await expect(dashboard.readiness()).toBeVisible();
    await expect(dashboard.backgroundTasks()).toContainText('url_scraping');
    await expect(dashboard.backgroundTasks()).toContainText('epg_refresh');
    await expect(dashboard.readiness()).toContainText(/Scheduler follow-through/);

    await dashboard.selectOption(dashboard.retentionSelect(), '3 days');
    await dashboard.expectAlert('Retention updated');
    const cfg = await api.raw('get', '/api/v1/config/dashboard').then((r) => r.json() as Promise<{ retention_days: number }>);
    expect(cfg.retention_days).toBe(3);
    await dashboard.selectOption(dashboard.retentionSelect(), '7 days');
    await dashboard.expectAlert('Retention updated');

    await dashboard.autoRefreshSwitch().uncheck();
    expect(await page.evaluate(() => localStorage.getItem('dashboard-auto-refresh'))).toBe('false');
    await dashboard.autoRefreshSwitch().check();
  });

  test('health reports healthy with the engine online and totals that match the API', async ({ page, api }) => {
    const health = new HealthPage(page);
    await health.open();
    await expect(health.statusChip()).toHaveText('HEALTHY');
    await expect(health.overview()).toContainText(/online/i);
    const channels = (await api.listChannels({ page_size: 1 })).total;
    const urls = (await api.listUrls()).length;
    const sources = (await api.listEpgSources()).length;
    await expect(health.totals()).toContainText(`Total Channels`);
    await expect(health.totals().getByText('Total Channels').locator('..')).toContainText(String(channels));
    await expect(health.totals().getByText('Total URLs').locator('..')).toContainText(String(urls));
    await expect(health.totals().getByText('EPG Sources').locator('..')).toContainText(String(sources));
    // Online/offline counters must reflect real status checks, not placeholders.
    const summary = await api.raw('get', '/api/v1/acestream-channels/status_summary').then((r) => r.json() as Promise<{ online: number; offline: number }>);
    await expect(health.totals().getByText('Online Channels').locator('..')).toContainText(String(summary.online));
    await expect(health.totals().getByText('Offline Channels').locator('..')).toContainText(String(summary.offline));
  });

  test('stats page shows inventory totals', async ({ page, api }) => {
    const stats = new StatsPage(page);
    await stats.open();
    const channels = (await api.listChannels({ page_size: 1 })).total;
    await expect(stats.summary()).toContainText('Channels');
    await expect(stats.summary()).toContainText(String(channels));
    await expect(stats.breakdown()).toContainText('EPG programs');
  });

  test('WARP page loads its status instead of erroring', async ({ page }) => {
    const warp = new WarpPage(page);
    await warp.open();
    await expect(page.getByRole('alert').filter({ hasText: /Error loading WARP status/ })).toHaveCount(0);
    await expect(warp.connectionStatus()).toBeVisible();
    await expect(warp.connectionStatus()).toContainText(/Not Running|Disconnected|Connected/);
    await expect(warp.modeAndLicense()).toBeVisible();
  });
});

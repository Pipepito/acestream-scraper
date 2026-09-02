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

  test('the services panel reports every sidecar and lets the operator restart supervised ones', async ({ page, api, scenario }, testInfo) => {
    test.setTimeout(240_000);
    const health = new HealthPage(page);
    await health.open();
    const status = await api.raw('get', '/api/v1/system/services').then((r) => r.json() as Promise<{ supervised: boolean; services: { name: string; label: string; state: string; managed: boolean; pid: number | null }[] }>);
    testInfo.annotations.push({ type: 'services', description: status.services.map((s) => `${s.name}=${s.state}${s.managed ? '(managed)' : ''}`).join(' ') });

    for (const service of status.services) {
      const card = health.serviceCard(service.label);
      await expect(card).toBeVisible();
      await expect(card.locator('[data-state]')).toHaveAttribute('data-state', service.state);
      if (service.managed) await expect(health.restartButton(service.label)).toBeEnabled();
      else await expect(health.restartButton(service.label)).toBeDisabled();
    }
    // The engine the app uses must be reported as reachable either way.
    const engine = status.services.find((s) => s.name === 'acestream')!;
    expect(['running', 'external']).toContain(engine.state);
    await expect(health.serviceCard(engine.label)).toContainText(/Running|External/);

    const managed = status.services.find((s) => s.name === 'acestream' && s.managed);
    if (!status.supervised || !managed) {
      await expect(health.services()).toContainText(/not running under the container entrypoint|Managed outside this container/);
      return;
    }
    await health.restart(managed.label);
    await health.expectAlert(/Restart requested/);
    await expect(health.serviceCard(managed.label)).toContainText('Restarting');
    await expect(health.serviceCard(managed.label)).toContainText('Running', { timeout: 120_000 });
    const after = await api.raw('get', '/api/v1/system/services').then((r) => r.json() as Promise<{ services: { name: string; pid: number | null; state: string }[] }>);
    const engineAfter = after.services.find((s) => s.name === 'acestream')!;
    expect(engineAfter.state).toBe('running');
    expect(engineAfter.pid).not.toBe(managed.pid);
    const version = await fetch(`${scenario.stack.engineUrl}/webui/api/service?method=get_version`).then((r) => r.json() as Promise<{ result?: { version?: string } }>);
    expect(version.result?.version).toBeTruthy();
  });

  test('stats page shows inventory totals', async ({ page, api }) => {
    const stats = new StatsPage(page);
    await stats.open();
    const channels = (await api.listChannels({ page_size: 1 })).total;
    await expect(stats.summary()).toContainText('Channels');
    await expect(stats.summary()).toContainText(String(channels));
    await expect(stats.breakdown()).toContainText('EPG programs');
  });

  test('WARP page loads its status instead of erroring', async ({ page, api }, testInfo) => {
    const warp = new WarpPage(page);
    await warp.open();
    await expect(page.getByRole('alert').filter({ hasText: /Error loading WARP status/ })).toHaveCount(0);
    await expect(warp.connectionStatus()).toBeVisible();
    await expect(warp.connectionStatus()).toContainText(/Not Running|Disconnected|Connected/);
    await expect(warp.modeAndLicense()).toBeVisible();

    // When the container runs WARP, the page must agree with the services panel.
    const services = await api.raw('get', '/api/v1/system/services').then((r) => r.json() as Promise<{ services: { name: string; state: string; message: string }[] }>);
    const warpService = services.services.find((s) => s.name === 'warp')!;
    testInfo.annotations.push({ type: 'warp', description: `${warpService.state}: ${warpService.message}` });
    if (warpService.state === 'running') {
      await expect(warp.connectionStatus()).toContainText('Service running');
      if (/^WARP connected/.test(warpService.message)) {
        await expect(warp.connectionStatus().getByText('Connected', { exact: true })).toBeVisible();
      }
    }
  });
});

import { test, expect } from '../src/fixtures';
import { OverviewPage, WarpPage } from '../src/pages/system';

test.describe('overview and WARP', () => {
  test('overview reports the engine, real totals and the scheduler', async ({ page, api }) => {
    const overview = new OverviewPage(page);
    await overview.open();
    await expect(overview.statusChip()).toHaveText('HEALTHY');
    await expect(overview.summary()).toContainText(/Engine/);
    await expect(overview.summary()).not.toContainText(/not reachable/);

    const channels = (await api.listChannels({ page_size: 1 })).total;
    const urls = (await api.listUrls()).length;
    const sources = (await api.listEpgSources()).length;
    const summary = await api.raw('get', '/api/v1/acestream-channels/status_summary').then((r) => r.json() as Promise<{ online: number; offline: number }>);
    const streams = overview.inventoryGroup('Streams');
    await expect(streams.getByText('Total', { exact: true }).locator('..')).toContainText(String(channels));
    await expect(streams.getByText('Online', { exact: true }).locator('..')).toContainText(String(summary.online));
    await expect(streams.getByText('Offline', { exact: true }).locator('..')).toContainText(String(summary.offline));
    const guide = overview.inventoryGroup('Sources and guide');
    await expect(guide.getByText('Source URLs').locator('..')).toContainText(String(urls));
    await expect(guide.getByText('EPG sources').locator('..')).toContainText(String(sources));

    await expect(overview.scheduledJobs()).toContainText('Scrape sources');
    await expect(overview.scheduledJobs()).toContainText('Refresh EPG');
    await expect(overview.scheduledJobs()).toContainText('Check stream status');
    // Every job row shows a next run; none shows raw job ids or the old vocabulary.
    await expect(overview.scheduledJobs()).not.toContainText('url_scraping');
    await expect(page.getByText(/follow-through|momentum|downstream/i)).toHaveCount(0);
  });

  test('the services panel reports every sidecar and lets the operator restart supervised ones', async ({ page, api, scenario }, testInfo) => {
    test.setTimeout(240_000);
    const overview = new OverviewPage(page);
    await overview.open();
    const status = await api.raw('get', '/api/v1/system/services').then((r) => r.json() as Promise<{ supervised: boolean; services: { name: string; label: string; state: string; managed: boolean; pid: number | null }[] }>);
    testInfo.annotations.push({ type: 'services', description: status.services.map((s) => `${s.name}=${s.state}${s.managed ? '(managed)' : ''}`).join(' ') });

    for (const service of status.services) {
      const card = overview.serviceCard(service.label);
      await expect(card).toBeVisible();
      await expect(card.locator('[data-state]')).toHaveAttribute('data-state', service.state);
      if (service.managed) await expect(overview.restartButton(service.label)).toBeEnabled();
      else await expect(overview.restartButton(service.label)).toBeDisabled();
    }
    // The in-container engine may be switched off (services-off flavour) while the app uses an external one.
    const engine = status.services.find((s) => s.name === 'acestream')!;
    expect(['running', 'external', 'disabled']).toContain(engine.state);
    await expect(overview.serviceCard(engine.label)).toContainText(/Running|External|turned off/);
    expect((await api.health()).acestream.status, 'the engine the app talks to answers').toBe('online');

    const managedNames = ['acestream', 'warp'];
    const managed = status.services.filter((s) => managedNames.includes(s.name) && s.managed);
    if (!status.supervised || managed.length === 0) {
      await expect(overview.services()).toContainText(/not running under the container entrypoint|Managed outside this container/);
      return;
    }
    for (const target of managed) {
      await overview.restart(target.label);
      await overview.expectAlert(/Restart requested/);
      await expect(overview.serviceCard(target.label)).toContainText('Restarting');
      await expect(overview.serviceCard(target.label)).toContainText('Running', { timeout: 120_000 });
      const after = await api.raw('get', '/api/v1/system/services').then((r) => r.json() as Promise<{ services: { name: string; pid: number | null; state: string; message: string }[] }>);
      const restarted = after.services.find((s) => s.name === target.name)!;
      expect(restarted.state, `${target.name} after restart`).toBe('running');
      expect(restarted.pid, `${target.name} relaunched with a new pid`).not.toBe(target.pid);
      testInfo.annotations.push({ type: 'restart', description: `${target.name}: pid ${target.pid} -> ${restarted.pid}; ${restarted.message}` });
    }
    const version = await fetch(`${scenario.stack.engineUrl}/webui/api/service?method=get_version`).then((r) => r.json() as Promise<{ result?: { version?: string } }>);
    expect(version.result?.version).toBeTruthy();
  });

  test('WARP page shows one status row and agrees with the services panel', async ({ page, api }, testInfo) => {
    const warp = new WarpPage(page);
    await warp.open();
    await expect(page.getByRole('alert').filter({ hasText: /Error loading WARP status/ })).toHaveCount(0);
    await expect(warp.status()).toContainText(/Not running|Disconnected|Connected/);

    const services = await api.raw('get', '/api/v1/system/services').then((r) => r.json() as Promise<{ services: { name: string; state: string; message: string }[] }>);
    const warpService = services.services.find((s) => s.name === 'warp')!;
    testInfo.annotations.push({ type: 'warp', description: `${warpService.state}: ${warpService.message}` });
    if (warpService.state === 'running') {
      await expect(warp.status()).toContainText(/Connected|Disconnected/);
      await expect(warp.status()).toContainText(/mode \w+/);
      await expect(warp.modeAndLicense()).toBeVisible();
      await expect(warp.connectionDetails()).toBeVisible();
      if (/^WARP connected/.test(warpService.message)) {
        await expect(warp.status()).toContainText(/^Connected/);
        await expect(warp.connectionDetails()).toContainText(/IP: \d+\.\d+\.\d+\.\d+/);
      }
    } else {
      await expect(warp.status()).toContainText('Not running');
      await expect(page.getByText(/WARP is not running in this container/)).toBeVisible();
      await expect(warp.modeAndLicense()).toHaveCount(0);
    }
  });
});

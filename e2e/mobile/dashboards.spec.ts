import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: TV landing and system administration stay separate`, async ({ page }) => {
    const errors: string[] = [];
    const mutations: string[] = [];
    const requests: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    const event = { id: 'grand-prix', revision: 1, title: 'International Grand Prix qualifying with a long event title', sport: 'Motorsport', competition: 'Formula 1', timezone: 'UTC', starts_at: '2026-10-26T12:00:00Z', ends_at: null, state: 'live', participants: [], time_notes: '', corrected: false, followed: false, archived: false,
      broadcasts: [{ id: 'broadcast', label: 'International Sports Television', language: '', quality: '', country: '', source_name: 'Schedule', origin: '', compatibility: 'unresolved', reason: 'No stream mapped', content_id: null, is_online: null, checked_at: null }], provenance: [] };
    await page.route('**/api/**', route => {
      const request = route.request();
      const url = new URL(request.url());
      const path = url.pathname;
      requests.push(path);
      if (request.method() !== 'GET') mutations.push(`${request.method()} ${path}`);
      const fixtures: Record<string, unknown> = {
        '/api/v1/recordings/upcoming': { total: 0, items: [] },
        '/api/v1/recordings/capabilities': { enabled: false, storage_ready: false, message: 'Configure recordings.' },
        '/api/v1/events': { total: url.searchParams.get('followed') === 'true' ? 0 : 2, events: url.searchParams.get('followed') === 'true' ? [] : [event, { ...event, id: 'next-race', title: 'Next race', starts_at: null, scheduled_date: '2026-10-27', state: 'scheduled' }] },
        '/api/v1/events/grand-prix': event,
        '/api/v1/events/interests': { sports: ['Motorsport'], competitions: ['Formula 1'], teams: [] },
        '/api/v1/stats': { channels: { total: 144, online: 100, offline: 24, unknown: 20 }, urls: { total: 4, active: 4, error: 0 }, epg: { sources: 2, channels: 80, programs: 3000 } },
        '/api/v1/stats/tv-channels/': { total: 40, active: 38, with_epg: 34, acestreams: 120 },
        '/api/v1/player/streams': { streams: [
          { kind: 'browser', id: 'browser', content_id: 'a'.repeat(40), channel_name: 'International sports channel with a long programme name', state: 'ready', viewers: 2, peers: 0, client_label: null, started_at: null },
          { kind: 'relay', id: 'relay', content_id: 'b'.repeat(40), channel_name: 'News relay', state: 'streaming', viewers: 1, peers: null, client_label: 'tuner:192.0.2.1', started_at: '2026-10-26T10:00:00Z' },
        ] },
        '/api/v1/background-tasks/status': [
          { task_name: 'url_scraping', status: 'waiting', last_run: '2026-10-26T10:00:00Z', next_run: '2026-10-27T10:00:00Z', last_result: { processed: 4, failures: 0 } },
          { task_name: 'channel_status', status: 'running', last_run: '2026-10-26T10:00:00Z', next_run: null },
          { task_name: 'channel_cleanup', status: 'idle', last_run: null, next_run: null },
        ],
        '/api/v1/health': { status: 'healthy', acestream: { status: 'unknown' }, settings: { ace_engine_url: '' }, version: 'v2.2.0' },
        '/api/v1/system/services': { supervised: true, services: [{ name: 'acestream', label: 'AceStream engine', installed: true, enabled: false, managed: true, running: false, state: 'stopped', stopped_by_user: true, version: null, pid: null, uptime_seconds: null, message: 'Stopped by you', description: 'Playback engine' }] },
        '/api/v1/system/storage': { directories: [], checked_at: '2026-10-26T10:00:00Z', mount_detection: 'unavailable', configuration_warnings: [] },
      };
      return route.fulfill({ json: fixtures[path] ?? { status: 'ready', phase: 'Ready to use', events: [] } });
    });
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1, name: 'TV dashboard' })).toBeVisible();
    await expect(page.getByText('International sports channel with a long programme name')).toBeVisible();
    await expect(page.getByText('In a browser · 2 viewers · 0 peers')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Watch TV' })).toHaveAttribute('href', '/live-tv');
    await expect(page.getByRole('region', { name: 'Next updates' })).not.toContainText('Remove stale channels');
    await expect(page.getByRole('table', { name: 'Scheduled jobs' })).toHaveCount(0);
    await expect(page.getByRole('region', { name: 'Next updates' })).toContainText('Waiting to run');
    await expect(page.getByRole('region', { name: 'Next updates' })).toContainText('Running now');
    expect(requests).not.toContain('/api/v1/system/services');
    expect(requests).not.toContain('/api/v1/system/storage');
    expect(requests.some(path => path.includes('/player/sessions'))).toBe(false);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`tv-dashboard-${mode}.png`), fullPage: true });
    const upNext = page.getByRole('region', { name: 'Up next' });
    await expect(upNext.getByText('Live · reported')).toBeVisible();
    await expect(upNext.getByText('Time TBC')).toBeVisible();
    await upNext.getByRole('button', { name: `View broadcasts for ${event.title}` }).click();
    await expect(page).toHaveURL(/\/events\?event=grand-prix&zone=/);
    await expect(page.getByRole('dialog', { name: 'Event details' })).toContainText(event.title);
    await page.getByRole('button', { name: 'Close event details' }).click();
    await expect(page).toHaveURL(/\/events\?zone=/);
    await page.goto('/');
    await page.getByLabel('Events to show').click();
    await page.getByRole('option', { name: 'Following', exact: true }).click();
    await expect(page.getByText(/No followed events are coming up/)).toBeVisible();
    await page.reload();
    await expect(page.getByText(/No followed events are coming up/)).toBeVisible();
    await page.getByLabel('Events to show').click();
    await page.getByRole('option', { name: 'My interests', exact: true }).click();
    await page.getByRole('button', { name: 'Choose interests' }).click();
    await page.getByRole('combobox', { name: 'Sports', exact: true }).fill('Motorsport');
    await page.getByRole('combobox', { name: 'Sports', exact: true }).press('Enter');
    await expect(upNext.getByRole('button', { name: `View broadcasts for ${event.title}` })).toBeVisible();
    await page.getByRole('textbox', { name: 'Display timezone' }).fill('Europe/Madrid');
    await page.getByRole('textbox', { name: 'Display timezone' }).press('Tab');
    await expect(upNext).toContainText('Europe/Madrid');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.getByRole('link', { name: 'All scheduled jobs' }).click();
    await expect(page).toHaveURL(/\/system$/);
    await expect(page.getByRole('heading', { level: 1, name: 'System status' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Download diagnostics' })).toBeVisible();
    await expect(page.getByRole('table', { name: 'Scheduled jobs' })).toContainText('Remove stale channels');
    await expect(page.getByText('Services healthy')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`system-dashboard-${mode}.png`), fullPage: true });
    await page.goto('/health');
    await expect(page).toHaveURL(/\/system$/);
    await expect(page.getByRole('heading', { level: 1, name: 'System status' })).toBeVisible();
    await expect(page.getByText('Services healthy')).toBeVisible();
    await page.waitForLoadState('networkidle');
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { level: 1, name: 'TV dashboard' })).toBeVisible();
    expect(mutations).toEqual([]);
    expect(errors).toEqual([]);
  });
}

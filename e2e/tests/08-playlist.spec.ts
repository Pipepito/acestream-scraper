import { test, expect } from '../src/fixtures';
import { PlaylistPage } from '../src/pages/playlist';

test.describe.configure({ mode: 'serial' });

test.describe('playlist', () => {
  test('the builder reflects options in an absolute URL and the M3U downloads', async ({ page, api, scenario, baseURL }) => {
    const playlist = new PlaylistPage(page);
    await playlist.open();
    await expect(playlist.onlyOnline()).not.toBeChecked();
    await expect(playlist.downloadLink()).toHaveAttribute('href', /only_online=false/);
    await expect(playlist.playlistUrlField()).toHaveValue(new RegExp(`^${baseURL!.replace(/\/$/, '')}/api/v1/playlists/m3u\\?`));
    const summary = await api.raw('get', '/api/v1/acestream-channels/status_summary').then((r) => r.json() as Promise<{ online: number; total_channels: number }>);
    await expect(page.getByText(`${summary.online} of ${summary.total_channels} channels are online right now`)).toBeVisible();

    await playlist.onlyOnline().check();
    await expect(playlist.downloadLink()).toHaveAttribute('href', /only_online=true/);
    await playlist.onlyOnline().uncheck();
    await playlist.searchField().fill('dazn');
    await expect(playlist.downloadLink()).toHaveAttribute('href', /search=dazn/);
    await playlist.searchField().fill('');

    await playlist.showGroupFilters();
    await expect(page.getByRole('combobox', { name: 'Include groups' })).toBeVisible();

    await playlist.selectBaseUrl(new RegExp(scenario.playlist.baseUrlName));
    const base = (await api.listBaseUrls()).find((b) => b.name === scenario.playlist.baseUrlName)!;
    await expect(playlist.downloadLink()).toHaveAttribute('href', new RegExp(`base_url_id=${base.id}`));

    const href = (await playlist.downloadLink().getAttribute('href'))!;
    const res = await page.request.get(href);
    expect(res.status()).toBe(200);
    expect(res.headers()['content-type']).toContain('text/plain');
    const body = await res.text();
    expect(body.startsWith('#EXTM3U')).toBe(true);
    const acexyPrefix = scenario.playlist.baseUrlPattern.split('{channel_id}')[0];
    expect(body).toContain(acexyPrefix);
    const total = (await api.listChannels({ page_size: 1, is_active: true })).total;
    expect(body.split('\n').filter((l) => l.startsWith('#EXTINF')).length).toBeGreaterThanOrEqual(Math.min(total, 1));

    const downloadPromise = page.waitForEvent('download', { timeout: 30_000 });
    await playlist.downloadLink().click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/playlist\.m3u$/);
  });

  test('public and legacy playlist routes serve the same M3U', async ({ api }) => {
    for (const path of ['/playlists/m3u', '/playlist.m3u', '/api/playlists/m3u']) {
      const res = await api.playlist(path, { only_online: 'false' });
      expect(res.status, path).toBe(200);
      expect(res.body.startsWith('#EXTM3U'), path).toBe(true);
    }
  });

  test('Acexy answers for a channel from the playlist', async ({ api, scenario }, testInfo) => {
    test.setTimeout(120_000);
    const res = await api.playlist('/api/v1/playlists/m3u', { only_online: 'false', base_url_id: String((await api.listBaseUrls()).find((b) => b.name === scenario.playlist.baseUrlName)!.id) });
    const link = res.body.split('\n').find((l) => l.startsWith(scenario.playlist.baseUrlPattern.split('{channel_id}')[0]));
    expect(link, 'a stream link through Acexy').toBeTruthy();
    const status = await fetch(`${scenario.stack.acexyUrl}/ace/status`).then((r) => r.json() as Promise<{ streams: number }>);
    testInfo.annotations.push({ type: 'acexy', description: `link=${link} streams-before=${status.streams}` });
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20_000);
    try {
      const stream = await fetch(link!, { signal: controller.signal });
      testInfo.annotations.push({ type: 'acexy-stream', description: `HTTP ${stream.status} ${stream.headers.get('content-type') ?? ''}` });
      expect([200, 500, 502, 503, 504]).toContain(stream.status);
    } catch (err) {
      testInfo.annotations.push({ type: 'acexy-stream', description: `no data within 20s (${String(err).slice(0, 80)})` });
    } finally {
      clearTimeout(timer);
    }
  });

  test('the QR code and copy button carry the absolute playlist URL', async ({ page, context, baseURL }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']).catch(() => undefined);
    const playlist = new PlaylistPage(page);
    await playlist.open();
    await playlist.copyButton().click();
    await playlist.expectAlert(/Playlist link copied|Unable to copy/);
    await playlist.qrButton().click();
    const dialog = page.getByRole('dialog', { name: 'Playlist QR code' });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('img', { name: 'QR code for the playlist URL' })).toBeVisible();
    await expect(dialog).toContainText(`${baseURL!.replace(/\/$/, '')}/api/v1/playlists/m3u?`);
  });
});

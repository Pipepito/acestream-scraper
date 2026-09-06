import { test, expect, type Page } from '@playwright/test';

const streams = [
  { id: 'a'.repeat(40), name: 'Arena HD', is_online: true, is_active: true, tv_channel_id: 1 },
  { id: 'b'.repeat(40), name: 'Arena backup', is_online: false, is_active: true, tv_channel_id: 1 },
];
const channel = { id: 1, name: 'Arena TV', channel_number: 1, is_active: true, is_favorite: true, epg_source_id: 1, epg_id: 'arena', acestream_channels: streams };
const channels = [channel, { ...channel, id: 2, name: 'No guide TV', is_favorite: false, epg_source_id: null, epg_id: null }, { ...channel, id: 3, name: 'No streams TV', acestream_channels: [], epg_source_id: null, epg_id: null }];

async function fixtures(page: Page) {
  const now = Date.now();
  const starts: string[] = [];
  const leaves: string[] = [];
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace('/api/v1', '');
    let data: unknown = {};
    if (path === '/tv-channels') data = { items: channels, total: channels.length };
    else if (path === '/tv-channels/1') data = channel;
    else if (path.startsWith('/acestream-channels/') || path.startsWith('/channels/')) data = streams[0];
    else if (path === '/epg/channels/resolve') data = { id: 1, name: 'Arena guide' };
    else if (path === '/epg/channels/1/programs') data = [
      { id: 1, epg_channel_id: 1, title: 'Live match', start_time: new Date(now - 900_000).toISOString(), end_time: new Date(now + 900_000).toISOString() },
      { id: 2, epg_channel_id: 1, title: 'Highlights', start_time: new Date(now + 900_000).toISOString(), end_time: new Date(now + 4500_000).toISOString() },
    ];
    else if (path === '/remote-players') data = [];
    else if (path === '/player/sessions' && request.method() === 'POST') {
      starts.push(request.postDataJSON().content_id);
      data = { id: `session-${starts.length}`, state: 'error', error: 'engine_unavailable', codecs: {}, hls_ready: false };
    } else if (path.startsWith('/player/sessions/')) {
      if (request.method() === 'DELETE') leaves.push(path.split('/').pop()!);
      data = { id: path.split('/').pop(), state: 'error', error: 'engine_unavailable', codecs: {}, hls_ready: false };
    }
    await route.fulfill({ json: data });
  });
  return { starts, leaves };
}

for (const mode of ['light', 'dark']) {
  test(`${mode}: browse, filter, switch stream and close`, async ({ page }) => {
    const { starts, leaves } = await fixtures(page);
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.addInitScript((value) => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/live-tv');
    await expect(page.getByRole('heading', { name: 'Live TV', exact: true })).toBeVisible();
    await expect(page.getByText('Now · Live match')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.getByRole('button', { name: 'Watch No streams TV' })).toBeDisabled();
    await page.getByRole('checkbox', { name: 'Favorites only' }).check();
    await expect(page.getByRole('button', { name: 'Watch No guide TV' })).toHaveCount(0);
    await page.getByRole('searchbox', { name: 'Find a channel' }).fill('missing');
    await expect(page.getByText('No channels match these filters.')).toBeVisible();
    await page.getByRole('searchbox', { name: 'Find a channel' }).clear();
    await page.getByRole('button', { name: 'Watch Arena TV' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Schedule', exact: true })).toBeVisible();
    await page.getByRole('combobox', { name: /^Stream/ }).click();
    await page.getByRole('option', { name: /Arena backup/ }).click();
    await expect(page.getByRole('listbox')).toHaveCount(0);
    await expect.poll(() => starts).toEqual([streams[0].id, streams[1].id]);
    await expect.poll(() => leaves).toContain('session-1');
    await expect(page.getByRole('dialog')).toHaveJSProperty('scrollWidth', await page.getByRole('dialog').evaluate((el) => el.clientWidth));
    await page.screenshot({ path: test.info().outputPath(`player-${mode}.png`), fullPage: true });
    await page.getByRole('button', { name: 'Close', exact: true }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await expect.poll(() => leaves).toContain('session-2');
    expect(errors).toEqual([]);
  });
}

test('direct channel URL, guide error and retry, browser Back', async ({ page }) => {
  await fixtures(page);
  await page.route('**/epg/channels/1/programs*', (route) => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }));
  await page.goto('/live-tv');
  await expect(page.getByText('Guide unavailable.')).toBeVisible();
  await page.unroute('**/epg/channels/1/programs*');
  await page.getByRole('button', { name: 'Retry', exact: true }).click();
  await expect(page.getByText('Now · Live match')).toBeVisible();
  await page.getByRole('button', { name: 'Watch Arena TV' }).click();
  await page.goBack();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.goto('/live-tv?channel=1');
  await expect(page.getByRole('combobox', { name: /^Stream/ })).toBeVisible();
});

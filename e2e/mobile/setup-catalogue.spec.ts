import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: add channels and review the built-in guide`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    const sources: object[] = [];
    const guides: object[] = [];
    let refreshed = false, writes = 0;
    const guide = { id: 2, name: 'EPG dobleM', url: 'https://raw.githubusercontent.com/davidmuma/EPG_dobleM/master/guiaiptv.xml', enabled: true, error_count: 0 };
    const state = { version: 1, setup_complete: false, revision: 'a'.repeat(64), runtime: {}, options: [], unavailable: {}, restart_required: false, api_protected: false };
    await page.route('**/api/**', async route => {
      const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '').replace(/\/$/, '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready', events: [] };
      if (path === '/setup') {
        if (request.method() === 'PUT') { expect(request.postDataJSON().runtime).toEqual({}); state.setup_complete = true; }
        data = state;
      }
      if (path === '/scrapers/urls') {
        if (request.method() === 'POST') { expect(request.postDataJSON().url).toBe('https://example.test/channels.m3u'); sources.push({ id: 1, ...request.postDataJSON(), error_count: 0 }); data = sources[0]; }
        else data = sources;
      }
      if (path === '/scrapers/urls/1/scrape') data = { url_id: 1, success: true, channels_found: 1, channels_added: 1, channels_updated: 0, duration_seconds: 1 };
      if (path === '/epg/sources') {
        if (request.method() === 'POST') { expect(request.postDataJSON()).toEqual({ name: guide.name, url: guide.url, enabled: true }); guides.push(guide); data = guide; }
        else data = guides.map(item => ({ ...item, last_updated: refreshed ? '2026-10-30T10:00:00Z' : null }));
      }
      if (path === '/epg/sources/2') data = { ...guide, last_updated: refreshed ? '2026-10-30T10:00:00Z' : null };
      if (path === '/epg/sources/2/refresh') { refreshed = true; data = { source_id: 2, success: true }; }
      if (path === '/epg/channels') data = { items: [], total: 1 };
      if (path === '/tv-channels/analyze-epg-matches') data = { summary: {}, rows: [{ epg_channel_id: 9, epg_channel_name: 'Example TV', epg_source_id: 2, candidate_count: 1, can_apply: true, is_creatable: true, review_token: 'reviewed', candidates: [{ name: 'Example TV HD', acestream_channel_id: '3', score: 1, match_stage: 'name' }] }] };
      if (path === '/tv-channels/create-from-epg-analysis') { expect(request.postDataJSON()).toEqual({ source_id: 2, strictness: 'strict', epg_channel_ids: [9], expected_previews: { '9': 'reviewed' } }); writes++; data = { created_count: 1, associated_count: 1, skipped_count: 0, failure_count: 0, row_outcomes: [] }; }
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/setup');
    await page.getByRole('textbox', { name: 'Channel source link' }).fill('https://example.test/channels.m3u');
    await page.getByRole('button', { name: 'Add source and find channels' }).click();
    await expect(page.getByText(/Found 1 channels/)).toBeVisible();
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await page.getByRole('button', { name: 'Use EPG dobleM' }).click();
    await expect(page.getByText(/Downloading programme times/)).toBeVisible();
    await page.getByRole('button', { name: 'Find matching channels' }).click();
    const selection = page.getByRole('checkbox', { name: 'Example TV', exact: true });
    await expect(selection).not.toBeChecked(); expect(writes).toBe(0);
    await expect(page.getByRole('button', { name: 'Save selected matches (0)' })).toBeDisabled();
    await selection.check();
    await page.screenshot({ path: test.info().outputPath(`setup-matches-${mode}.png`), animations: 'disabled' });
    await page.getByRole('button', { name: 'Save selected matches (1)' }).click();
    await expect(page.getByText(/Created 1 TV channels/)).toBeVisible(); expect(writes).toBe(1);
    await page.getByRole('button', { name: 'Finish setup' }).click();
    await expect(page.getByRole('heading', { name: 'Setup saved', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(errors).toEqual([]);
  });
}

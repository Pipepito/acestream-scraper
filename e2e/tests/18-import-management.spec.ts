import { createServer } from 'node:http';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { test, expect } from '../src/fixtures';
import type { components } from '../../frontend/src/types/api-generated';

type SavedSearch = components['schemas']['SavedSearchView'];
const ids = { existing: 'a'.repeat(40), fresh: 'b'.repeat(40), blocked: 'e'.repeat(40), absent: 'f'.repeat(40), source: '9'.repeat(40) };

// Real application API, SQLite migrations, queue and SPA. Only the upstream
// catalogue/source is controlled; this test does not intercept browser API calls.
test('real app preserves imports and coalesces saved-search refreshes', async ({ page, request, baseURL, errors }, testInfo) => {
  test.setTimeout(120_000);
  // This test deliberately verifies the manual-add refusal before overriding it.
  errors.allowBackend(/APIError code=IMPORT_EXCLUDED message=This stream matches an import exclusion/);
  let searches = 0;
  const server = createServer((req, res) => {
    const url = new URL(req.url || '/', 'http://fixture');
    const json = (value: unknown) => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(value)); };
    if (url.pathname === '/search') {
      searches++;
      setTimeout(() => json({ result: { total: 4, results: [
        { name: 'Regional sports', infohash: '1'.repeat(40) },
        { name: 'Public sports extra', infohash: '2'.repeat(40) },
        { name: 'Shopping preview', infohash: '3'.repeat(40) },
        { name: 'Unavailable catalogue entry', infohash: '4'.repeat(40) },
      ] } }), 1500);
    } else if (url.pathname === '/server/api') {
      const hash = url.searchParams.get('infohash');
      json(hash === '4'.repeat(40) ? { error: 'unresolved' } : { result: { content_id: hash === '1'.repeat(40) ? ids.existing : ids.fresh } });
    } else if (url.pathname === '/source.m3u') {
      res.setHeader('Content-Type', 'audio/x-mpegurl');
      res.end(`#EXTM3U\n#EXTINF:-1,Shopping incoming\nacestream://${ids.blocked}\n#EXTINF:-1,Community television\nacestream://${ids.source}\n`);
    } else if (url.pathname === '/webui/api/service') json({ result: { version: 'fixture' } });
    else { res.statusCode = 404; res.end(); }
  });
  await new Promise<void>(resolve => server.listen(0, '0.0.0.0', resolve));
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Fixture did not bind');
  const host = process.env.E2E_TARGET === 'docker' ? 'host.docker.internal' : '127.0.0.1';
  const engine = `http://${host}:${address.port}`;
  const source = `${engine}/source.m3u`;
  const root = `${baseURL}/api/v1`;
  const previousEngine = await (await request.get(`${root}/config/ace_engine_url`)).json() as { value: string };
  const post = async (url: string, data: unknown, status = 201) => {
    const response = await request.post(`${root}${url}`, { data });
    expect(response.status(), await response.text()).toBe(status);
    return response;
  };
  const getSearch = async (id: number) => (await (await request.get(`${root}/saved-searches/${id}`)).json()) as SavedSearch;
  let saved: SavedSearch | undefined;
  try {
    // Re-running this journey only replaces its own synthetic definitions/data.
    const priorSources = await (await request.get(`${root}/scrapers/urls`)).json() as { id: number; url: string }[];
    for (const row of priorSources.filter(row => /^http:\/\/(host\.docker\.internal|127\.0\.0\.1):\d+\/source\.m3u$/.test(row.url))) {
      expect((await request.delete(`${root}/scrapers/urls/${row.id}`)).ok()).toBe(true);
    }
    const priorSearches = await (await request.get(`${root}/saved-searches`)).json() as { items: SavedSearch[] };
    for (const row of priorSearches.items.filter(row => row.query === 'Regional sports')) {
      expect((await request.delete(`${root}/saved-searches/${row.id}?expected_revision=${row.revision}`)).ok()).toBe(true);
    }
    const priorRules = await (await request.get(`${root}/import-exclusions`)).json() as { items: components['schemas']['ExclusionRule'][] };
    for (const row of priorRules.items.filter(row => row.kind === 'name_contains' && row.value === 'Shopping')) {
      expect((await request.delete(`${root}/import-exclusions/${row.id}?expected_revision=${row.revision}`)).ok()).toBe(true);
    }
    for (const id of [ids.fresh, ids.source, 'd'.repeat(40)]) await request.delete(`${root}/channels/${id}`);
    for (const [id, name, owner] of [
      [ids.existing, 'My regional sports', 'manual'],
      [ids.blocked, 'Operator channel name', source], [ids.absent, 'Absent source channel', source],
    ]) {
      await request.delete(`${root}/channels/${id}`);
      await post('/channels/', { id, name, source_url: owner, group: 'Operator group', is_online: true });
      expect((await request.put(`${root}/channels/${id}`, { data: { is_active: false } })).ok()).toBe(true);
    }
    const original = await (await request.get(`${root}/channels/${ids.existing}`)).json();
    const protectedRow = await (await request.get(`${root}/channels/${ids.blocked}`)).json();
    await page.addInitScript(() => { if (!localStorage.getItem('app-theme-mode')) localStorage.setItem('app-theme-mode', 'light'); localStorage.setItem('acestream.changelog.seen.v1', 'v2.2.0'); });
    await page.goto('/scraper?tab=exclusions');
    await page.getByRole('button', { name: 'Add exclusion', exact: true }).click();
    await page.getByRole('textbox', { name: 'Value', exact: true }).fill('Shopping');
    await page.getByRole('textbox', { name: 'Note (optional)' }).fill('Skip shopping feeds in future imports; keep existing channels.');
    await page.getByRole('button', { name: 'Preview matches' }).click();
    await expect(page.getByText(/matches in .* current channels/)).toBeVisible();
    await page.getByRole('button', { name: 'Save exclusion' }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect((await request.put(`${root}/config/ace_engine_url`, { data: { value: engine } })).ok()).toBe(true);
    await page.getByRole('tab', { name: 'Saved searches' }).click();
    await page.getByRole('button', { name: 'Create search' }).click();
    await page.getByRole('textbox', { name: 'Name', exact: true }).fill('Regional sports discoveries');
    await page.getByRole('textbox', { name: 'Query', exact: true }).fill('Regional sports');
    await expect(page.getByRole('checkbox', { name: /Import matching results/ })).not.toBeChecked();
    await page.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(searches).toBe(0);
    const list = await (await request.get(`${root}/saved-searches`)).json() as { items: SavedSearch[] };
    saved = list.items.find(row => row.query === 'Regional sports');
    expect(saved).toBeDefined();
    if (!saved) throw new Error('Saved definition missing');
    expect(saved.refresh_enabled).toBe(false);
    saved = await (await request.patch(`${root}/saved-searches/${saved.id}`, { data: { ...saved, refresh_enabled: true, expected_revision: saved.revision } })).json() as SavedSearch;
    const runs = await Promise.all([1, 2].map(() => post(`/saved-searches/${saved!.id}/run`, { expected_revision: saved!.revision }, 202)));
    const accepted = await Promise.all(runs.map(response => response.json() as Promise<SavedSearch>));
    expect(accepted[0].run_id).toBe(accepted[1].run_id);
    expect((await request.get(`${root}/playlists/m3u?refresh=true&only_online=false`)).ok()).toBe(true);
    await expect.poll(async () => (await getSearch(saved!.id)).run_state, { timeout: 30000 }).toBeNull();
    const first = await getSearch(saved.id);
    expect(first.last_result).toMatchObject({ outcome: 'partial', added: 1, existing: 1, excluded_candidates: 1, unresolved_candidates: 1 });
    await expect.poll(async () => {
      const tasks = await (await request.get(`${root}/background-tasks/status`)).json() as { task_name: string; status: string; last_result?: { saved_searches?: { searches: number } } }[];
      const job = tasks.find(row => row.task_name === 'url_scraping');
      return job?.status === 'idle' ? job.last_result?.saved_searches?.searches : -1;
    }).toBe(0);
    expect(searches).toBe(1);
    expect(await (await request.get(`${root}/channels/${ids.existing}`)).json()).toEqual(original);
    expect((await request.get(`${root}/channels/${'1'.repeat(40)}`)).status()).toBe(404);
    expect((await (await request.get(`${root}/channels/${ids.fresh}`)).json()).is_online).toBeNull();
    await request.get(`${root}/playlists/m3u?refresh=true&only_online=false`);
    await expect.poll(async () => (await getSearch(saved!.id)).run_id).not.toBe(first.run_id);
    await expect.poll(async () => (await getSearch(saved!.id)).run_state).toBeNull();
    expect((await getSearch(saved.id)).last_result).toMatchObject({ added: 0, existing: 2, excluded_candidates: 1, unresolved_candidates: 1 });
    expect(searches).toBe(2);
    const scrape = await post('/scrapers/scrape', { url: source, url_type: 'regular', run_async: false }, 200);
    expect(await scrape.json()).toMatchObject({ status: 'OK', channels_found: 1, excluded_count: 1 });
    expect(await (await request.get(`${root}/channels/${ids.blocked}`)).json()).toEqual(protectedRow);
    expect((await request.get(`${root}/channels/${ids.absent}`)).status()).toBe(404);
    const refusal = await post('/channels/', { id: 'd'.repeat(40), name: 'Shopping manual' }, 409);
    expect((await refusal.json()).error.code).toBe('IMPORT_EXCLUDED');
    await post('/channels/', { id: 'd'.repeat(40), name: 'Shopping manual', allow_excluded: true });
    const screenshots = process.env.E2E_IMPORT_SCREENSHOTS_DIR || testInfo.outputPath('screenshots');
    await mkdir(screenshots, { recursive: true });
    for (const [theme, width, tab] of [['light', 1440, 'searches'], ['dark', 1440, 'exclusions'], ['light', 390, 'exclusions'], ['dark', 390, 'searches']] as const) {
      await page.evaluate(mode => localStorage.setItem('app-theme-mode', mode), theme);
      await page.setViewportSize({ width, height: 960 });
      await page.goto(`/scraper?tab=${tab}`);
      await expect(page.getByRole('button', { name: tab === 'searches' ? 'Run now' : 'Add exclusion', exact: true })).toBeVisible();
      await page.evaluate(() => window.scrollTo(0, 0));
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      await page.screenshot({ path: path.join(screenshots, `${tab}-${theme}-${width}.png`), fullPage: true, animations: 'disabled' });
    }
    testInfo.annotations.push({ type: 'runtime', description: 'Real container API: authoritative IDs, additive import, exclusion preservation, manual/scheduled deduplication, automatic refresh and four responsive captures passed.' });
  } finally {
    const sources = await (await request.get(`${root}/scrapers/urls`)).json() as { id: number; url: string }[];
    for (const row of sources.filter(row => row.url === source)) await request.delete(`${root}/scrapers/urls/${row.id}`);
    if (saved) {
      const current = await getSearch(saved.id);
      await request.patch(`${root}/saved-searches/${saved.id}`, { data: { ...current, refresh_enabled: false, expected_revision: current.revision } });
    }
    await request.put(`${root}/config/ace_engine_url`, { data: { value: previousEngine.value } });
    await new Promise<void>((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  }
});

import { test, expect } from '../src/fixtures';
import { EPGPage, EPGChannelDetailPage } from '../src/pages/epg';

test.describe.configure({ mode: 'serial' });

test.describe('EPG', () => {
  test('an EPG source is added and refreshed; the guide loads without errors', async ({ page, api, scenario }, testInfo) => {
    const src = scenario.epg.sources[0];
    test.setTimeout(src.refreshTimeoutMs + 120_000);
    const existing = await api.findEpgSource(src.url);
    if (existing) await api.deleteEpgSource(existing.id);

    const epg = new EPGPage(page);
    await epg.open();
    await epg.addSource(src.name, src.url);
    await epg.expectAlert('EPG source added successfully');
    await expect(epg.sourceRow(src.name)).toContainText('Never');
    const created = await api.findEpgSource(src.url);
    expect(created).toBeTruthy();

    const started = Date.now();
    await epg.refreshSource(src.name);
    // The UI must not claim a result it does not have (the refresh runs in the background).
    const toast = epg.page.getByRole('alert').filter({ hasText: /refresh/i }).first();
    const toastText = await toast.textContent({ timeout: 5_000 }).catch(() => null);
    testInfo.annotations.push({ type: 'epg-refresh-toast', description: toastText ?? '(no toast)' });
    if (toastText) {
      expect(toastText, 'refresh feedback must not print undefined/null counts').not.toMatch(/undefined|null/);
      expect(toastText, 'refresh feedback must not claim completion before the job ran').not.toMatch(/refreshed successfully/);
    }

    // Watch the API stay responsive while the (large) feed is being imported.
    let slowestHealthMs = 0;
    let healthFailures = 0;
    const done = api.waitForEpgRefresh(created!.id, null, src.refreshTimeoutMs);
    const watcher = (async () => {
      let finished = false;
      void done.finally(() => { finished = true; });
      while (!finished) {
        const t0 = Date.now();
        try {
          await api.health();
        } catch {
          healthFailures += 1;
        }
        slowestHealthMs = Math.max(slowestHealthMs, Date.now() - t0);
        await new Promise((r) => setTimeout(r, 5_000));
      }
    })();
    const refreshed = await done;
    await watcher;
    const seconds = Math.round((Date.now() - started) / 1000);
    testInfo.annotations.push({ type: 'epg-refresh', description: `${src.name}: ${seconds}s, error_count=${refreshed.error_count}, last_error=${refreshed.last_error}, slowest /health ${slowestHealthMs} ms, health failures ${healthFailures}` });
    expect(refreshed.last_error).toBeNull();
    expect(refreshed.error_count).toBe(0);

    const channels = await api.listEpgChannels(created!.id, 1);
    expect(channels.total).toBeGreaterThanOrEqual(src.expectMinChannels);
    testInfo.annotations.push({ type: 'epg-channels', description: `${channels.total} channels` });

    await page.reload();
    await expect(epg.sourceRow(src.name)).not.toContainText('Never');
    await expect(epg.sourceRow(src.name)).not.toContainText(/Errors:/);
  });

  test('the channel inventory is filterable by source and lists the loaded channels', async ({ page, api, scenario }) => {
    const src = scenario.epg.sources[0];
    const source = await api.findEpgSource(src.url);
    expect(source).toBeTruthy();
    const epg = new EPGPage(page);
    await epg.open();
    await epg.selectSourceFilter(src.name);
    await expect(epg.inventory()).toContainText(/Showing 1-\d+ of \d+ channels/);
    const total = (await api.listEpgChannels(source!.id, 1)).total;
    await expect(epg.inventory()).toContainText(`of ${total} channels`);
    const first = (await api.listEpgChannels(source!.id, 1)).items[0];
    await expect(epg.inventoryRow(first.name).first()).toBeVisible();
  });

  test('the EPG channel detail shows programs for the target channel', async ({ page, api, scenario }) => {
    const src = scenario.epg.sources[0];
    const source = await api.findEpgSource(src.url);
    const target = await api.resolveEpgChannel(source!.id, scenario.epg.targetChannel.xmlId);
    expect(target, `EPG channel ${scenario.epg.targetChannel.xmlId} exists`).toBeTruthy();
    const programs = await api.epgPrograms(target!.id);
    expect(programs.length).toBeGreaterThan(0);

    const detail = new EPGChannelDetailPage(page);
    await detail.open(target!.id, new RegExp(scenario.epg.targetChannel.displayNameContains));
    await expect(detail.schedule()).toContainText(/Total Programs: [1-9]\d*/);
    await expect(detail.programsTable().getByRole('row').nth(1)).toBeVisible();
    await expect(detail.programsTable()).toContainText(programs[0].title);
  });

  test('match analysis runs against the loaded guide', async ({ page, scenario }, testInfo) => {
    test.setTimeout(300_000);
    const epg = new EPGPage(page);
    await epg.open();
    await epg.selectSourceFilter(scenario.epg.sources[0].name);
    await epg.analyze('Balanced');
    await expect(epg.matching()).toContainText(/\d+ analyzed/, { timeout: 240_000 });
    const text = await epg.matching().innerText();
    testInfo.annotations.push({ type: 'epg-analysis', description: text.match(/\d+ analyzed[\s\S]*?\d+ creatable/)?.[0]?.replace(/\s+/g, ' ') ?? text.slice(0, 200) });
  });

  test('EPG XML output is generated for mapped channels', async ({ page, api }) => {
    const epg = new EPGPage(page);
    await epg.open();
    await epg.xmlOutput().getByRole('button', { name: 'Generate and Download EPG XML' }).click();
    await epg.expectAlert('EPG XML generation started');
    const xml = await api.epgXml({ days_back: '1', days_forward: '7' });
    expect(xml).toContain('<tv');
  });
});

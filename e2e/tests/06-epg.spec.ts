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
    await expect(epg.page.getByRole('tab', { name: 'Sources', selected: true })).toBeVisible();
    await epg.addSource(src.name, src.url);
    await epg.expectAlert('EPG source added successfully');
    await expect(epg.sourceRow(src.name)).toContainText('Never');
    const created = await api.findEpgSource(src.url);
    expect(created).toBeTruthy();

    const started = Date.now();
    await epg.refreshSource(src.name);
    const toast = epg.page.getByRole('alert').filter({ hasText: /refresh/i }).first();
    const toastText = await toast.textContent({ timeout: 5_000 }).catch(() => null);
    testInfo.annotations.push({ type: 'epg-refresh-toast', description: toastText ?? '(no toast)' });
    if (toastText) {
      expect(toastText, 'refresh feedback must not print undefined/null counts').not.toMatch(/undefined|null/);
      expect(toastText, 'refresh feedback must not claim completion before the job ran').not.toMatch(/refreshed successfully/);
    }

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
    await expect(epg.sourceRow(src.name)).not.toContainText(/failed refresh/);
    await expect(epg.summary()).toContainText(/Guide channels\s*[1-9]\d*/);
    await expect(epg.summary()).toContainText(/Last refresh\s*(just now|\d+ min ago)/);
  });

  test('the Channels tab is filterable by source, links each channel and shows link state', async ({ page, api, scenario }) => {
    const src = scenario.epg.sources[0];
    const source = await api.findEpgSource(src.url);
    expect(source).toBeTruthy();
    const epg = new EPGPage(page);
    await epg.open('Channels');
    await expect(page).toHaveURL(/tab=channels$/);
    await epg.selectSourceFilter(src.name);
    await expect(epg.channels()).toContainText(/Showing 1-\d+ of \d+ channels/);
    const total = (await api.listEpgChannels(source!.id, 1)).total;
    await expect(epg.channels()).toContainText(`of ${total} channels`);
    const first = (await api.listEpgChannels(source!.id, 1)).items[0];
    await expect(epg.channelLink(first.name).first()).toHaveAttribute('href', `/epg/channels/${first.id}`);
    await expect(epg.channelRow(first.name).first()).toContainText(/Linked|Not linked/);
  });

  test('the EPG channel detail shows the schedule for the target channel', async ({ page, api, scenario }) => {
    const src = scenario.epg.sources[0];
    const source = await api.findEpgSource(src.url);
    const target = await api.resolveEpgChannel(source!.id, scenario.epg.targetChannel.xmlId);
    expect(target, `EPG channel ${scenario.epg.targetChannel.xmlId} exists`).toBeTruthy();
    const programs = await api.epgPrograms(target!.id);
    expect(programs.length).toBeGreaterThan(0);

    const detail = new EPGChannelDetailPage(page);
    await detail.open(target!.id, new RegExp(scenario.epg.targetChannel.displayNameContains));
    await expect(detail.summary()).toContainText(`XML ID: ${scenario.epg.targetChannel.xmlId}`);
    await expect(detail.schedule().getByRole('tab', { name: 'Today', selected: true })).toBeVisible();
    await expect(detail.nowNext()).toBeVisible();
    await expect(detail.schedule()).toContainText(/\d+ programmes? today|No programmes today/);

    // Pick the first day that has programmes and check its first title is listed.
    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    const byDay = new Map<number, string>();
    for (const p of programs) {
      const offset = Math.floor((new Date(p.start_time).getTime() - startOfDay.getTime()) / 86_400_000);
      if (offset >= 0 && offset < 7 && !byDay.has(offset)) byDay.set(offset, p.title);
    }
    const [offset, title] = [...byDay.entries()].sort((a, b) => a[0] - b[0])[0] ?? [];
    test.skip(offset === undefined, 'guide has no programmes in the next 7 days');
    if (offset! > 0) await detail.selectDay(offset === 1 ? 'Tomorrow' : new RegExp('^\\w{3} \\d+$'));
    await expect(detail.schedule()).toContainText(title!, { timeout: 30_000 });
    await expect(detail.schedule().getByRole('listitem', { name: title! }).first()).toBeVisible();
  });

  test('string mapping rules can be added on a channel and appear on the Rules tab', async ({ page, api, scenario }) => {
    const src = scenario.epg.sources[0];
    const source = await api.findEpgSource(src.url);
    const target = (await api.resolveEpgChannel(source!.id, scenario.epg.targetChannel.xmlId))!;
    const detail = new EPGChannelDetailPage(page);
    await detail.open(target.id, new RegExp(scenario.epg.targetChannel.displayNameContains));
    await detail.addStringMapping('E2E RULE PATTERN');
    await detail.expectAlert('String mapping added successfully');
    await detail.closeSnackbar();
    await expect(detail.mappings()).toContainText('E2E RULE PATTERN');

    const epg = new EPGPage(page);
    await epg.open('Rules');
    await expect(epg.rules()).toContainText('E2E RULE PATTERN');
    await expect(epg.rules().getByRole('link', { name: `Channel #${target.id}` })).toBeVisible();

    await detail.open(target.id, new RegExp(scenario.epg.targetChannel.displayNameContains));
    await detail.deleteStringMapping('E2E RULE PATTERN');
    await detail.expectAlert('String mapping deleted successfully');
    await expect(detail.mappings()).not.toContainText('E2E RULE PATTERN');
  });

  test('match analysis runs against the loaded guide', async ({ page, scenario }, testInfo) => {
    test.setTimeout(300_000);
    const epg = new EPGPage(page);
    await epg.open('Matching');
    await epg.selectSourceFilter(scenario.epg.sources[0].name);
    await epg.analyze('Balanced');
    await expect(epg.matching()).toContainText(/\d+ analyzed/, { timeout: 240_000 });
    const text = await epg.matching().innerText();
    testInfo.annotations.push({ type: 'epg-analysis', description: text.match(/\d+ analyzed[\s\S]*?\d+ creatable/)?.[0]?.replace(/\s+/g, ' ') ?? text.slice(0, 200) });
  });

  test('EPG XML output is generated from the Export tab', async ({ page, api }) => {
    const epg = new EPGPage(page);
    await epg.open();
    await epg.headerButton('Export XML').click();
    await expect(page).toHaveURL(/tab=export$/);
    await epg.exportPanel().getByRole('button', { name: 'Generate and Download EPG XML' }).click();
    await epg.expectAlert('EPG XML generation started');
    const xml = await api.epgXml({ days_back: '1', days_forward: '7' });
    expect(xml).toContain('<tv');
  });
});

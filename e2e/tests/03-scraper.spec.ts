import { test, expect } from '../src/fixtures';
import { ScraperPage } from '../src/pages/scraper';
import { scrapeUrlFor } from '../src/scenario/load';

test.describe.configure({ mode: 'serial' });

test.describe('scraper', () => {
  test('a source URL is added, scraped and yields channels', async ({ page, api, scenario }, testInfo) => {
    test.setTimeout(scenario.scrape.sources.reduce((t, s) => t + s.scrapeTimeoutMs, 120_000));
    const scraper = new ScraperPage(page);

    for (const source of scenario.scrape.sources) {
      const url = scrapeUrlFor(source);
      const existing = await api.findUrl(url);
      if (existing) await api.deleteUrl(existing.id);

      await scraper.open();
      await scraper.addUrl({ url, urlType: source.urlType });
      await scraper.expectAlert('URL added successfully');
      const row = scraper.row(url);
      await expect(row).toBeVisible();
      await expect(scraper.enabledSwitch(url)).toBeChecked();
      await expect(row).toContainText('Not scraped yet');
      await expect(row).toContainText('never');

      await scraper.scrape(url);
      let result = await api.waitForScrape(url, null, source.scrapeTimeoutMs);
      testInfo.annotations.push({ type: 'scrape', description: `${source.id}: status=${result.status} channels=${result.channels_found}` });

      if (result.status !== 'OK' && source.fallbackUrl) {
        testInfo.annotations.push({ type: 'scrape-fallback', description: `primary failed (${result.status}); trying ${source.fallbackUrl}` });
        await scraper.addUrl({ url: source.fallbackUrl, urlType: source.urlType });
        await scraper.scrape(source.fallbackUrl);
        result = await api.waitForScrape(source.fallbackUrl, null, source.scrapeTimeoutMs);
      }
      expect(result.status, `scrape status for ${source.id}`).toBe('OK');
      expect(result.channels_found).toBeGreaterThanOrEqual(source.expectMinChannels);

      await scraper.refresh();
      const finalRow = scraper.row(result.url);
      await expect(finalRow).toContainText('OK');
      await expect(finalRow).not.toContainText('never');
      await expect(finalRow).toContainText(String(result.channels_found));
      await expect(scraper.status()).toContainText(/Last scrape.*ago|just now/);

      // source_url is stored normalised (ipfs sources become ipns://<key>/...), so match on the key/host.
      const key = result.url.match(/\/ip[fn]s\/([^/]+)/)?.[1] ?? new URL(result.url.replace(/^ip[fn]s:\/\//, 'http://')).host;
      const channels = await api.listChannels({ page_size: 500 });
      const fromSource = channels.items.filter((c) => c.source_url === result.url || (c.source_url ?? '').includes(key));
      expect(fromSource.length).toBeGreaterThanOrEqual(source.expectMinChannels);
    }
  });

  test('a disabled URL cannot be scraped and the row toggles round-trip', async ({ page, api, scenario, errors }) => {
    const source = scenario.scrape.sources[0];
    const url = scrapeUrlFor(source);
    // Re-runnable: a previous failure may have left the source disabled or harvesting bare IDs.
    const seeded = (await api.findUrl(url))!;
    await api.raw('patch', `/api/v1/scrapers/urls/${seeded.id}`, { enabled: true, scrape_bare_ids: false });
    const scraper = new ScraperPage(page);
    await scraper.open();

    await scraper.enabledSwitch(url).click();
    await scraper.expectAlert('Source disabled; it is skipped by scheduled scrapes');
    await expect(scraper.enabledSwitch(url)).not.toBeChecked();
    expect((await api.findUrl(url))?.enabled).toBe(false);

    // The UI does not offer a scrape for a disabled source; the API refuses it too.
    await expect(scraper.row(url).getByRole('button', { name: `Scrape URL ${url}` })).toBeDisabled();
    errors.allowApi(/\/scrape 400 .*URL is disabled/);
    const refused = await api.raw('post', `/api/v1/scrapers/urls/${(await api.findUrl(url))!.id}/scrape`);
    expect(refused.status()).toBe(400);

    await scraper.enabledSwitch(url).click();
    await scraper.expectAlert('Source enabled');
    await expect(scraper.enabledSwitch(url)).toBeChecked();
    expect((await api.findUrl(url))?.enabled).toBe(true);

    // Editing through the dialog still works and keeps the type.
    const dialog = await scraper.edit(url);
    await expect(dialog.getByRole('textbox', { name: 'URL' })).toHaveValue(url);
    await dialog.getByRole('button', { name: 'Update' }).click();
    await expect(dialog).toBeHidden();
    await scraper.expectAlert('URL updated successfully');

    // Bare-ID harvesting is a checked menu item driven by server state.
    await scraper.toggleBareIds(url);
    await scraper.expectAlert(/harvest/i);
    await expect.poll(async () => (await api.findUrl(url))?.scrape_bare_ids, { timeout: 15_000 }).toBe(true);
    await scraper.toggleBareIds(url);
    await expect.poll(async () => (await api.findUrl(url))?.scrape_bare_ids, { timeout: 15_000 }).toBe(false);
  });

  test('a URL that cannot be fetched shows the failure in its row and in the summary', async ({ page, api }, testInfo) => {
    const badUrl = 'http://127.0.0.1:9/e2e-unreachable';
    const existing = await api.findUrl(badUrl);
    if (existing) await api.deleteUrl(existing.id);
    const scraper = new ScraperPage(page);
    await scraper.open();
    await scraper.addUrl({ url: badUrl, urlType: 'regular' });
    await scraper.scrape(badUrl);
    const result = await api.waitForScrape(badUrl, null, 120_000);
    testInfo.annotations.push({ type: 'scrape', description: `unreachable: status=${result.status} error_count=${result.error_count} last_error=${result.last_error}` });
    expect(result.status).toMatch(/^Error/);
    await scraper.refresh();
    await expect(scraper.row(badUrl)).toContainText(/Error/);
    await expect(scraper.status()).toContainText(/Failing\s*[1-9]/);
    await scraper.delete(badUrl);
    await scraper.expectAlert('URL deleted successfully');
    expect(await api.findUrl(badUrl)).toBeUndefined();
  });
});

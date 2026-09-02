import { test, expect } from '../src/fixtures';
import { ScraperPage } from '../src/pages/scraper';
import { scrapeUrlFor } from '../src/scenario/load';

test.describe.configure({ mode: 'serial' });

test.describe('URL scraper', () => {
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
      await expect(row).toContainText('Enabled');
      await expect(row).toContainText('Never');

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
      await expect(finalRow).not.toContainText('Never');
      await expect(finalRow).toContainText(String(result.channels_found));

      // source_url is stored normalised (ipfs sources become ipns://<key>/...), so match on the key/host.
      const key = result.url.match(/\/ip[fn]s\/([^/]+)/)?.[1] ?? new URL(result.url.replace(/^ip[fn]s:\/\//, 'http://')).host;
      const channels = await api.listChannels({ page_size: 500 });
      const fromSource = channels.items.filter((c) => c.source_url === result.url || (c.source_url ?? '').includes(key));
      expect(fromSource.length).toBeGreaterThanOrEqual(source.expectMinChannels);
    }
  });

  test('a disabled URL cannot be scraped and the toggles round-trip', async ({ page, api, scenario, errors }) => {
    const source = scenario.scrape.sources[0];
    const url = scrapeUrlFor(source);
    const scraper = new ScraperPage(page);
    await scraper.open();

    const dialog = await scraper.edit(url);
    await scraper.selectOption(dialog.getByRole('combobox', { name: /^Status/ }), 'Disabled');
    await dialog.getByRole('button', { name: 'Update' }).click();
    await expect(dialog).toBeHidden();
    await scraper.expectAlert('URL updated successfully');
    await expect(scraper.row(url)).toContainText('Disabled');
    expect((await api.findUrl(url))?.enabled).toBe(false);

    errors.allowApi(/\/scrape 400 .*URL is disabled/);
    await scraper.scrape(url);
    await scraper.expectAlert(/URL is disabled/);

    const reenable = await scraper.edit(url);
    await scraper.selectOption(reenable.getByRole('combobox', { name: /^Status/ }), 'Enabled');
    await reenable.getByRole('button', { name: 'Update' }).click();
    await expect(reenable).toBeHidden();
    await expect(scraper.row(url)).toContainText('Enabled');

    // The switch is controlled by server state: it flips once the PATCH round-trips.
    await scraper.bareIdsSwitch(url).click();
    await scraper.expectAlert('Bare content ID harvesting enabled');
    await expect(scraper.bareIdsSwitch(url)).toBeChecked();
    expect((await api.findUrl(url))?.scrape_bare_ids).toBe(true);
    await scraper.bareIdsSwitch(url).click();
    await scraper.expectAlert('Bare content ID harvesting disabled');
    await expect(scraper.bareIdsSwitch(url)).not.toBeChecked();
    expect((await api.findUrl(url))?.scrape_bare_ids).toBe(false);
  });

  test('a URL that cannot be fetched records an error status instead of failing silently', async ({ page, api }, testInfo) => {
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
    // A user needs to see that the scrape failed: the row must show the failure, not just "Enabled".
    await scraper.refresh();
    await expect(scraper.row(badUrl)).toContainText(/Error|Failed/i);
    await scraper.delete(badUrl);
    await scraper.expectAlert('URL deleted successfully');
    expect(await api.findUrl(badUrl)).toBeUndefined();
  });
});

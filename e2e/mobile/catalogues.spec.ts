import { test, expect } from '@playwright/test';

const entries = [
  { id: 'root', parent_id: null, name: 'Example catalogue', kind: 'folder', origin: 'example.test' },
  { id: 'live', parent_id: 'root', name: 'Live channels', kind: 'folder', origin: 'example.test' },
  { id: 'ace', parent_id: 'live', name: 'A channel with a long publisher title and a regional edition HD', kind: 'acestream', origin: 'example.test', channel_id: 'a'.repeat(40), reason: 'AceStream; signal not checked' },
  { id: 'web', parent_id: 'root', name: 'Website player', kind: 'unsupported', origin: 'example.test', reason: 'Website/embed source needs an explicit resolver adapter' },
];
for (const theme of ['light', 'dark']) {
  test(`${theme}: catalogue preview, folder selection, details and local favorites`, async ({ page }) => {
    const errors: string[] = [];
    const writes: Record<string, unknown>[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.addInitScript(mode => {
      localStorage.setItem('app-theme-mode', mode);
      localStorage.setItem('acestream.changelog.seen.v1', 'v2.2.0');
    }, theme);
    const preview = { name: 'Example catalogue', origin: 'example.test', entries, revision: 0,
      counts: { accepted: 1, duplicates: 0, invalid: 0, unsupported: 1, failed_fetches: 0 },
      selected_branches: ['root'], mode: 'compatible', can_refresh: true, preview_token: 'test-preview' };
    const saved = { ...preview, id: 1, revision: 1, preview_token: null, entries: entries.map(entry => ({ ...entry, imported: entry.kind === 'acestream' })) };
    const event = { id: 'e'.repeat(32), revision: 1, title: 'Reviewed match', timezone: 'UTC', state: 'unknown', sport: '', competition: '', participants: [], corrected: false, followed: false, archived: false, broadcasts: [], provenance: [] };
    const eventWrites: unknown[] = [];
    let imported = false;
    await page.route('**/api/**', route => route.fulfill({ json: { status: 'ready', phase: 'Ready to use', events: [] } }));
    await page.route('**/api/v1/catalogues**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (path.endsWith('/events/preview')) return route.fulfill({ json: { token: 'event-review', events: [event], warnings: [] } });
      if (path.endsWith('/preview')) return route.fulfill({ json: preview });
      if (path.endsWith('/1')) return route.fulfill({ json: saved });
      if (route.request().method() === 'POST') {
        writes.push(route.request().postDataJSON() as Record<string, unknown>); imported = true;
        return route.fulfill({ json: saved });
      }
      return route.fulfill({ json: imported ? [{ id: 1, name: saved.name, origin: saved.origin, revision: 1, partial: false, refresh_enabled: false, updated_at: '2026-10-22T12:00:00Z' }] : [] });
    });
    await page.route('**/api/v1/events/apply', async route => {
      eventWrites.push(route.request().postDataJSON());
      return route.fulfill({ json: [event] });
    });
    await page.goto('/catalogues');
    await expect(page.getByRole('heading', { name: 'Catalogues', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Add catalogue', exact: true }).click();
    await page.getByLabel('Catalogue URL').fill('https://example.test/list.w3u');
    await page.getByRole('button', { name: 'Preview URL' }).click();
    await expect(page.getByRole('heading', { name: 'Review import' })).toBeVisible();
    expect(writes).toHaveLength(0);
    await page.getByLabel('All folders', { exact: true }).uncheck();
    await page.getByLabel('Include Live channels', { exact: true }).check();
    await page.getByLabel('Import selected compatible entries as permanent live channels').check();
    await page.getByRole('button', { name: 'Save catalogue and import' }).click();
    await expect(page.getByRole('button', { name: 'Remove catalogue', exact: true })).toBeVisible();
    expect(writes[0].selected_branches).toEqual(['live']);
    await page.getByRole('button', { name: /Live channels Folder/ }).click();
    await page.getByRole('button', { name: /A channel with a long publisher title/ }).click();
    await expect(page.getByRole('button', { name: 'Play source' })).toBeVisible();
    await page.getByRole('button', { name: 'Add favorite' }).click();
    expect(await page.evaluate(() => JSON.parse(localStorage.getItem('acestream.catalogue-history.v1') ?? '{}').favorites)).toEqual(['1:ace']);
    await page.getByRole('button', { name: 'Add as event', exact: true }).click();
    await page.getByRole('textbox', { name: 'Event title', exact: true }).fill('Reviewed match');
    await page.getByRole('button', { name: 'Preview events', exact: true }).click();
    expect(eventWrites).toHaveLength(0);
    await page.getByRole('checkbox', { name: 'Reviewed match · unknown' }).check();
    await page.getByRole('button', { name: 'Save selected (1)' }).click();
    await expect(page.getByRole('heading', { name: 'Add events', exact: true })).toHaveCount(0);
    expect(eventWrites).toEqual([{ token: 'event-review', selected_ids: [event.id], refresh_source: false }]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: test.info().outputPath(`catalogue-${theme}.png`), fullPage: true });
    await page.getByLabel('Search catalogue', { exact: true }).fill('Website');
    await page.getByRole('button', { name: /Website player Unsupported/ }).click();
    await expect(page.getByRole('button', { name: 'Play source' })).toHaveCount(0);
    expect(errors).toEqual([]);
  });
}

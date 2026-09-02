import { test, expect } from '../src/fixtures';
import { SearchPage } from '../src/pages/search';

test.describe.configure({ mode: 'serial' });

test.describe('engine search', () => {
  test('search results come from the live engine and can be added one by one', async ({ page, api, scenario }, testInfo) => {
    const search = new SearchPage(page);
    await search.open();
    for (const q of scenario.search.queries) {
      const apiResults = await api.search(q.query);
      expect(apiResults.results.length, `engine results for "${q.query}"`).toBeGreaterThanOrEqual(q.expectMinResults);

      await search.search(q.query, q.category);
      await expect(search.results()).toBeVisible();
      await expect(search.summary()).toContainText(new RegExp(`Results\\s*\\d+ for ‘${q.query}’`));
      await expect(search.resultRows().first()).toBeVisible();
      const uiCount = await search.resultRows().count();
      expect(uiCount).toBeGreaterThanOrEqual(Math.min(q.expectMinResults, 10));
      testInfo.annotations.push({ type: 'search', description: `${q.query}: api=${apiResults.pagination.total_results} ui-rows=${uiCount}` });

      const toAdd = apiResults.results.slice(0, q.addFirst).filter((r) => r.id);
      for (const r of toAdd) {
        await api.deleteChannel(r.id);
        await search.addRow(r.name);
        await search.expectAlert(`Added ${r.name} to your channels.`);
        await expect(search.addedChip(r.name)).toBeVisible();
        await expect
          .poll(async () => (await api.getChannel(r.id))?.name, { timeout: 15_000, message: `channel ${r.id} added from search` })
          .toBe(r.name);
      }
      await expect(search.summary()).toContainText(new RegExp(`Added this session\\s*${toAdd.length}`));
    }
  });

  test('several results can be selected and added in one batch', async ({ page, api, scenario }) => {
    const q = scenario.search.queries[0];
    const search = new SearchPage(page);
    await search.open();
    await search.search(q.query);
    await expect(search.resultRows().first()).toBeVisible();
    const apiResults = await api.search(q.query);
    const batch = apiResults.results.slice(0, Math.min(3, apiResults.results.length)).filter((r) => r.id);
    for (const r of batch) {
      await api.deleteChannel(r.id);
      await search.selectRow(r.name);
    }
    await expect(search.summary()).toContainText(new RegExp(`Selected\\s*${batch.length}`));
    await search.addSelected();
    await search.expectAlert(`Added ${batch.length} channels.`);
    for (const r of batch) {
      await expect.poll(async () => (await api.getChannel(r.id))?.id, { timeout: 15_000 }).toBe(r.id);
    }
  });

  test('a query with no matches shows the empty state', async ({ page }) => {
    const search = new SearchPage(page);
    await search.open();
    await search.search('zzqqxxe2enomatch');
    await expect(search.results()).toContainText('No channels found matching your search criteria.');
  });
});

import { test, expect } from '../src/fixtures';
import { SearchPage } from '../src/pages/search';

test.describe.configure({ mode: 'serial' });

test.describe('engine search', () => {
  test('search results come from the live engine and can be added one by one', async ({ page, api, scenario }, testInfo) => {
    const search = new SearchPage(page);
    await search.open();
    let addedThisSession = 0;
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
        const { content_id: contentId } = await api.resolveSearchResult(r.id);
        await api.deleteChannel(contentId);
        await search.addRow(r.name);
        await search.expectAlert(`${r.name}: added.`);
        await expect(search.addedChip(r.name)).toBeVisible();
        await expect
          .poll(async () => (await api.getChannel(contentId))?.name, { timeout: 15_000, message: `channel ${contentId} added from search` })
          .toBe(r.name);
      }
      addedThisSession += toAdd.length;
      await expect(search.summary()).toContainText(new RegExp(`Added this session\\s*${addedThisSession}`));
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
    const contentIds = new Map<string, string>();
    for (const r of batch) {
      const { content_id: contentId } = await api.resolveSearchResult(r.id);
      contentIds.set(r.id, contentId);
      await api.deleteChannel(contentId);
      await search.selectRow(r.name);
    }
    await expect(search.summary()).toContainText(new RegExp(`Selected\\s*${batch.length}`));
    await search.addSelected();
    await search.expectAlert(`${batch.length} added, 0 existing, 0 excluded, 0 unresolved, 0 deferred.`);
    for (const r of batch) {
      const contentId = contentIds.get(r.id)!;
      await expect.poll(async () => (await api.getChannel(contentId))?.id, { timeout: 15_000 }).toBe(contentId);
    }
  });

  test('a query with no matches shows the empty state', async ({ page }) => {
    const search = new SearchPage(page);
    await search.open();
    await search.search('zzqqxxe2enomatch');
    await expect(search.results()).toContainText('No channels found matching your search criteria.');
  });
});

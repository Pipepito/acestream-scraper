import { test, expect } from '@playwright/test';
for (const theme of ['light', 'dark']) {
  test(`${theme}: exclusion preview, configuration-only save and queued search`, async ({ page }) => {
    const errors: string[] = [];
    const writes: string[] = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await page.addInitScript(mode => { localStorage.setItem('app-theme-mode', mode); localStorage.setItem('acestream.changelog.seen.v1', 'v2.2.0'); }, theme);
    let rules: unknown[] = [];
    let searches: Record<string, unknown>[] = [];
    await page.route('**/api/**', route => route.fulfill({ json: { status: 'ready', phase: 'Ready to use', events: [] } }));
    await page.route('**/api/v1/import-exclusions**', async route => {
      const req = route.request();
      if (new URL(req.url()).pathname.endsWith('/preview')) return route.fulfill({ json: { policy_revision: 0, scanned: 10000, matched: 18, complete: false, examples: [] } });
      if (req.method() === 'POST') {
        const rule = { ...req.postDataJSON(), id: 1, revision: 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
        rules = [rule]; writes.push('rule');
        return route.fulfill({ status: 201, json: { rule, policy_revision: 1 } });
      }
      return route.fulfill({ json: { items: rules, total: rules.length, policy_revision: rules.length } });
    });
    await page.route('**/api/v1/saved-searches**', async route => {
      const req = route.request();
      if (new URL(req.url()).pathname.endsWith('/run')) {
        writes.push('run'); searches[0] = { ...searches[0], run_id: 'run1', run_state: 'waiting' };
        return route.fulfill({ status: 202, json: searches[0] });
      }
      if (req.method() === 'POST') {
        writes.push('search');
        searches = [{ ...req.postDataJSON(), id: 1, revision: 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }];
        return route.fulfill({ status: 201, json: searches[0] });
      }
      return route.fulfill({ json: { items: searches, total: searches.length } });
    });
    await page.goto('/scraper?tab=exclusions');
    await expect(page.getByRole('tab', { name: 'Import exclusions' })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('button', { name: 'Add exclusion', exact: true }).click();
    await page.getByRole('textbox', { name: 'Value', exact: true }).fill('Publisher sports with a long regional name [ES]');
    await page.getByRole('button', { name: 'Preview matches' }).click();
    await expect(page.getByText(/At least 18 matches/)).toBeVisible();
    expect(writes).toEqual([]);
    await page.getByRole('button', { name: 'Save exclusion' }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await page.getByRole('tab', { name: 'Saved searches' }).click();
    await expect(page).toHaveURL(/tab=searches/);
    await page.getByRole('button', { name: 'Create search' }).click();
    await page.getByRole('textbox', { name: 'Name', exact: true }).fill('Regional sports in a long catalogue title');
    await page.getByRole('textbox', { name: 'Query', exact: true }).fill('Sport [ES]');
    await expect(page.getByRole('checkbox', { name: /Import matching results/ })).not.toBeChecked();
    // Keyboard submit path stays within the modal and uses the explicit Save.
    await page.getByRole('button', { name: 'Save', exact: true }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(writes).toEqual(['rule', 'search']);
    await page.getByRole('button', { name: 'Run now' }).click();
    await expect(page.getByRole('button', { name: 'Waiting', exact: true })).toBeDisabled();
    expect(searches[0].refresh_enabled).toBe(false);
    expect(writes).toEqual(['rule', 'search', 'run']);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: test.info().outputPath(`imports-${theme}.png`), fullPage: true });
    await page.goBack();
    await expect(page.getByRole('tab', { name: 'Import exclusions' })).toHaveAttribute('aria-selected', 'true');
    expect(errors).toEqual([]);
  });
}

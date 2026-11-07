import { test, expect } from '@playwright/test';

for (const theme of ['light', 'dark']) {
  test(`${theme}: choose a broadcaster, name it, and filter catalogue streams`, async ({ page }) => {
    const errors: string[] = [];
    const writes: Record<string, unknown>[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.addInitScript(mode => {
      localStorage.setItem('app-theme-mode', mode);
      localStorage.setItem('acestream.changelog.seen.v1', 'v2.2.0');
    }, theme);
    await page.route('**/api/**', route => route.fulfill({ json: { status: 'ready', phase: 'Ready to use', events: [] } }));
    await page.route('**/api/v1/scrapers/providers', route => route.fulfill({ json: [{ id: 'atresplayer', name: 'Atresmedia', url: 'https://www.atresplayer.com' }] }));
    await page.route('**/api/v1/scrapers/urls**', route => {
      if (route.request().method() === 'POST') {
        const source = route.request().postDataJSON(); writes.push(source);
        return route.fulfill({ status: 201, json: { ...source, id: 1 } });
      }
      return route.fulfill({ json: writes.map((source, i) => ({ ...source, id: i + 1, status: 'pending' })) });
    });
    await page.route('**/api/v1/acestream-channels/**', route => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/groups')) return route.fulfill({ json: [] });
      if (url.pathname.endsWith('/sources')) return route.fulfill({ json: [{ value: 'catalogue:7', label: 'My uploaded catalogue', kind: 'catalogue' }] });
      return route.fulfill({ json: { items: [], total: 0 } });
    });
    await page.route('**/api/v1/tv-channels/**', route => route.fulfill({ json: { items: [], total: 0 } }));
    await page.goto('/scraper');
    await page.getByRole('button', { name: 'Add URL', exact: true }).click();
    await page.getByRole('combobox', { name: 'Built-in provider' }).click();
    await page.getByRole('option', { name: 'Atresmedia' }).click();
    await expect(page.getByRole('textbox', { name: 'URL', exact: true })).toHaveValue('https://www.atresplayer.com');
    await page.getByRole('textbox', { name: 'Friendly name (optional)' }).fill('Living room broadcaster with a long descriptive name');
    await page.getByRole('button', { name: 'Add', exact: true }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(writes).toEqual([expect.objectContaining({ name: 'Living room broadcaster with a long descriptive name', url_type: 'broadcaster' })]);
    await page.goto('/acestream-channels');
    const source = page.getByRole('combobox', { name: 'Source', exact: true });
    await source.fill('uploaded');
    const filtered = page.waitForRequest(request => new URL(request.url()).searchParams.get('source_url') === 'catalogue:7');
    await page.getByRole('option', { name: 'My uploaded catalogue · W3U catalogue · catalogue:7' }).click();
    await filtered;
    await expect(page.getByRole('button', { name: 'Reset filters' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`sources-${theme}.png`), fullPage: true });
    await page.getByRole('button', { name: 'Reset filters' }).click();
    await expect(source).toHaveValue('');
    expect(errors).toEqual([]);
  });
}

import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: update notice and version history work across reloads`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/api/**', route => route.fulfill({ json: { status: 'ready', phase: 'Ready to use', events: [] } }));
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    // An unknown route needs no catalogue fixtures and still exercises the shell.
    await page.goto('/missing-page');
    await expect(page.getByRole('link', { name: 'What’s new in v2.2.0' })).toBeVisible();
    await page.getByRole('link', { name: 'What’s new in v2.2.0' }).click();
    await expect(page.getByRole('heading', { name: 'Changelog', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'v2.1.0', exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'v2.0.0', exact: true }).click();
    await expect(page).toHaveURL(/#v2\.0\.0$/);
    await page.goto('/changelog');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`changelog-${mode}.png`), fullPage: true });
    await page.goto('/missing-page');
    await expect(page.getByRole('link', { name: 'What’s new in v2.2.0' })).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole('link', { name: 'What’s new in v2.2.0' })).toHaveCount(0);
    const menu = page.getByRole('button', { name: 'open drawer' });
    if (await menu.isVisible()) await menu.click();
    await page.getByRole('link', { name: 'Changelog', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Changelog', exact: true })).toBeVisible();
    expect(errors).toEqual([]);
  });
}

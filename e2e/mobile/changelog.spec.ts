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

for (const deployment of ['docker', 'native']) {
  test(`${deployment}: published update is announced once and history works offline`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/api/**', route => route.fulfill({ json: { status: 'ready', phase: 'Ready to use', events: [] } }));
    await page.route('**/api/v1/system/updates', route => route.fulfill({ json: {
      current_version: 'v2.2.0', latest_version: 'v2.10.0', update_available: true,
      status: 'checked', deployment, release_url: 'https://github.com/Pipepito/acestream-scraper/releases/tag/v2.10.0',
    } }));
    await page.goto('/missing-page');
    await expect(page.getByText('v2.10.0 is available')).toBeVisible();
    await expect(page.getByText(deployment === 'docker' ? /pull the new Docker image/ : /download the latest release/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`update-${deployment}.png`), fullPage: true });
    await page.reload();
    await expect(page.getByRole('link', { name: 'What’s new in v2.2.0' })).toBeVisible();
    await expect(page.getByText('v2.10.0 is available')).toHaveCount(0);
    // Load the lazy route once, then disconnect: history needs no GitHub request.
    await page.getByRole('link', { name: 'What’s new in v2.2.0' }).click();
    await expect(page.getByRole('heading', { name: 'Changelog', exact: true })).toBeVisible();
    await page.context().setOffline(true);
    await page.getByRole('link', { name: 'v2.1.0', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'v2.1.0', exact: true })).toBeVisible();
    expect(errors).toEqual([]);
  });
}

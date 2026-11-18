import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const currentVersion = readFileSync(resolve(__dirname, '../../version.txt'), 'utf8').trim();
const noticeName = `What’s new in ${currentVersion}`;
const newerVersion = `v${Number(currentVersion.slice(1).split('.')[0]) + 1}.0.0`;
const updateMessage = `${newerVersion} is available`;

async function openShell(page: Page, path?: string) {
  // Wait for shell reads before another full navigation can cancel them. A
  // missing-link assertion alone can pass while the app is still starting.
  const responses = Promise.all(['/api/v1/setup', '/api/v1/system/updates'].map(endpoint =>
    page.waitForResponse(response => new URL(response.url()).pathname === endpoint)));
  if (path) await page.goto(path);
  else await page.reload();
  await Promise.all((await responses).map(response => response.finished()));
  if (!path || path === '/missing-page') {
    await expect(page.getByRole('heading', { name: 'Page not found', exact: true })).toBeVisible();
  }
}


for (const mode of ['light', 'dark']) {
  test(`${mode}: update notice and version history work across reloads`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/api/**', route => {
      const path = new URL(route.request().url()).pathname;
      const fixtures: Record<string, unknown> = { '/api/v1/background-tasks/status': [], '/api/v1/system/services': { services: [] }, '/api/v1/player/streams': { streams: [] }, '/api/v1/recordings/upcoming': { items: [], total: 0 }, '/api/v1/system/storage': { directories: [], configuration_warnings: [] } };
      return route.fulfill({ json: fixtures[path] ?? { status: 'ready', phase: 'Ready to use', events: [] } });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    // An unknown route needs no catalogue fixtures and still exercises the shell.
    await openShell(page, '/missing-page');
    await expect(page.getByRole('link', { name: noticeName })).toBeVisible();
    await page.getByRole('link', { name: noticeName }).click();
    await expect(page.getByRole('heading', { name: 'Changelog', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: currentVersion, exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'v2.1.0', exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'v2.0.0', exact: true }).click();
    await expect(page).toHaveURL(/#v2\.0\.0$/);
    await openShell(page, '/changelog');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`changelog-${mode}.png`), fullPage: true });
    await openShell(page, '/missing-page');
    await expect(page.getByRole('link', { name: noticeName })).toHaveCount(0);
    await openShell(page);
    await expect(page.getByRole('link', { name: noticeName })).toHaveCount(0);
    const menu = page.getByRole('button', { name: 'Open navigation' });
    if (await menu.isVisible()) await menu.click();
    await page.getByRole('link', { name: 'System', exact: true }).click();
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
    await page.route('**/api/**', route => {
      const path = new URL(route.request().url()).pathname;
      const fixtures: Record<string, unknown> = { '/api/v1/background-tasks/status': [], '/api/v1/system/services': { services: [] }, '/api/v1/player/streams': { streams: [] }, '/api/v1/recordings/upcoming': { items: [], total: 0 }, '/api/v1/system/storage': { directories: [], configuration_warnings: [] } };
      return route.fulfill({ json: fixtures[path] ?? { status: 'ready', phase: 'Ready to use', events: [] } });
    });
    await page.route('**/api/v1/system/updates', route => route.fulfill({ json: {
      current_version: currentVersion, latest_version: newerVersion, update_available: true,
      status: 'checked', deployment, release_url: `https://github.com/Pipepito/acestream-scraper/releases/tag/${newerVersion}`,
    } }));
    await openShell(page, '/missing-page');
    await expect(page.getByText(updateMessage)).toBeVisible();
    await expect(page.getByText(deployment === 'docker' ? /pull the new Docker image/ : /download the latest release/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`update-${deployment}.png`), fullPage: true });
    await openShell(page);
    await expect(page.getByRole('link', { name: noticeName })).toBeVisible();
    await expect(page.getByText(updateMessage)).toHaveCount(0);
    // Load the lazy route once, then disconnect: history needs no GitHub request.
    await page.getByRole('link', { name: noticeName }).click();
    await expect(page.getByRole('heading', { name: 'Changelog', exact: true })).toBeVisible();
    await page.context().setOffline(true);
    await page.getByRole('link', { name: 'v2.1.0', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'v2.1.0', exact: true })).toBeVisible();
    expect(errors).toEqual([]);
  });
}

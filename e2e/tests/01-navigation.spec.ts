import { test, expect } from '../src/fixtures';
import { NAV_ROUTES, type NavLabel } from '../src/pages/app-shell';

test.describe('navigation', () => {
  test('every nav item opens its page and marks itself current; labels equal page titles', async ({ app, page }) => {
    await app.goto('/');
    await app.expectHeading('Overview');
    const labels = await app.nav().getByRole('link').allInnerTexts();
    expect(labels.map((l) => l.trim())).toEqual(Object.keys(NAV_ROUTES));
    for (const [label, route] of Object.entries(NAV_ROUTES) as [NavLabel, string][]) {
      await app.navigate(label);
      await app.expectHeading(label);
      await expect(page).toHaveURL(new RegExp(`${route.replace(/\//g, '\\/')}$`));
      await expect(app.nav().getByRole('link', { name: label, exact: true })).toHaveAttribute('aria-current', 'page');
    }
  });

  test('old bookmarks redirect to the merged pages', async ({ app, page }) => {
    for (const [from, heading, url] of [
      ['/dashboard', 'Overview', /\/$/],
      ['/health', 'Overview', /\/$/],
      ['/stats', 'Overview', /\/$/],
      ['/channels', 'TV Channels', /\/tv-channels$/],
      ['/search-new', 'Search', /\/search$/],
      ['/epg/mappings', 'EPG', /\/epg\?tab=rules$/],
    ] as const) {
      await app.goto(from);
      await app.expectHeading(heading);
      await expect(page).toHaveURL(url);
    }
    await expect(page.getByRole('tab', { name: 'Rules', selected: true })).toBeVisible();
  });

  test('deep links render client-side routes and unknown routes show the recovery page', async ({ app, page }) => {
    await app.goto('/tv-channels');
    await app.expectHeading('TV Channels');
    await app.goto('/this/route/does/not/exist');
    await app.expectHeading('Page not found');
    await page.getByRole('button', { name: 'Open Dashboard' }).click();
    await app.expectHeading('Overview');
  });

  test('theme toggle switches between light and dark and persists', async ({ app, page }) => {
    await app.goto('/');
    await app.expectHeading('Overview');
    await expect(app.themeToggle()).toHaveAttribute('aria-label', 'Switch to dark theme');
    await app.themeToggle().click();
    await expect(app.themeToggle()).toHaveAttribute('aria-label', 'Switch to light theme');
    expect(await page.evaluate(() => localStorage.getItem('app-theme-mode'))).toBe('dark');
    await page.reload();
    await expect(app.themeToggle()).toHaveAttribute('aria-label', 'Switch to light theme');
    await app.themeToggle().click();
    expect(await page.evaluate(() => localStorage.getItem('app-theme-mode'))).toBe('light');
  });
});

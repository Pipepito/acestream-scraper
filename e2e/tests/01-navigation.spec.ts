import { test, expect } from '../src/fixtures';
import { NAV_ROUTES, type NavLabel } from '../src/pages/app-shell';

const HEADINGS: Record<NavLabel, string> = {
  Dashboard: 'Dashboard',
  Scraper: 'URL Scraper',
  'Acestream Search': 'Search Channels',
  'Acestream Channels': 'Acestream Channels',
  'EPG Sources': 'EPG Management',
  'EPG Mappings': 'EPG Mappings',
  'TV Channels': 'TV Channels',
  Playlist: 'Playlist',
  'WARP Status': 'WARP',
  Settings: 'Settings',
  Health: 'Health',
  Stats: 'Stats',
};

test.describe('navigation', () => {
  test('every nav item opens its page and marks itself current', async ({ app, page }) => {
    await app.goto('/');
    await app.expectHeading('Dashboard');
    for (const [label, heading] of Object.entries(HEADINGS) as [NavLabel, string][]) {
      await app.navigate(label);
      await app.expectHeading(heading);
      await expect(page).toHaveURL(new RegExp(`${NAV_ROUTES[label].replace(/\//g, '\\/')}$`));
      await expect(app.nav().getByRole('link', { name: label, exact: true })).toHaveAttribute('aria-current', 'page');
    }
  });

  test('deep links render client-side routes and unknown routes show the recovery page', async ({ app, page }) => {
    await app.goto('/tv-channels');
    await app.expectHeading('TV Channels');
    await app.goto('/this/route/does/not/exist');
    await app.expectHeading('Page not found');
    await page.getByRole('button', { name: 'Open Dashboard' }).click();
    await app.expectHeading('Dashboard');
  });

  test('theme toggle switches between light and dark and persists', async ({ app, page }) => {
    await app.goto('/');
    await app.expectHeading('Dashboard');
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

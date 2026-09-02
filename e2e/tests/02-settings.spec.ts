import { test, expect } from '../src/fixtures';
import { SettingsPage } from '../src/pages/settings';

test.describe.configure({ mode: 'serial' });

test.describe('settings', () => {
  test('engine connection reports the live engine as online', async ({ page }) => {
    const settings = new SettingsPage(page);
    await settings.open();
    await settings.refreshEngineStatus();
    await expect(settings.engineRegion().getByRole('alert')).toContainText(/Online/, { timeout: 20_000 });
  });

  test('engine URL can be pointed at the stack engine and is reflected in the inventory', async ({ page, api, scenario }) => {
    const settings = new SettingsPage(page);
    await settings.open();
    await settings.saveEngineUrl(scenario.stack.engineUrl);
    await settings.expectAlert('Acestream Engine URL updated successfully');
    await expect(settings.inventoryRow('ace_engine_url')).toContainText(scenario.stack.engineUrl);
    expect(await api.getSetting('ace_engine_url')).toBe(scenario.stack.engineUrl);
    await settings.refreshEngineStatus();
    await expect(settings.engineRegion().getByRole('alert')).toContainText(/Online/, { timeout: 20_000 });
  });

  test('a named stream base URL for Acexy can be added and made default', async ({ page, api, scenario }) => {
    const existing = (await api.listBaseUrls()).find((b) => b.name === scenario.playlist.baseUrlName);
    if (existing) await api.deleteBaseUrl(existing.id);

    const settings = new SettingsPage(page);
    await settings.open();
    await settings.addBaseUrl(scenario.playlist.baseUrlName, scenario.playlist.baseUrlPattern, true);
    await settings.expectAlert(`Base URL "${scenario.playlist.baseUrlName}" added`);
    const entry = settings.baseUrlsRegion().getByText(scenario.playlist.baseUrlName, { exact: true });
    await expect(entry).toBeVisible();
    const saved = (await api.listBaseUrls()).find((b) => b.name === scenario.playlist.baseUrlName);
    expect(saved?.pattern).toBe(scenario.playlist.baseUrlPattern);
    expect(saved?.is_default).toBe(true);
  });

  test('automation settings save and the theme radio is the canonical theme control', async ({ page, api }) => {
    const settings = new SettingsPage(page);
    await settings.open();
    await settings.saveRescrapeInterval('12');
    await settings.expectAlert('Rescrape interval updated successfully');
    expect(await api.getSetting('rescrape_interval')).toBe('12');
    await settings.saveRescrapeInterval('24');
    await settings.expectAlert('Rescrape interval updated successfully');

    await settings.themeRadio('Dark theme').check();
    await expect(settings.themeToggle()).toHaveAttribute('aria-label', 'Switch to light theme');
    await settings.themeRadio('Light theme').check();
    await expect(settings.themeToggle()).toHaveAttribute('aria-label', 'Switch to dark theme');
  });
});

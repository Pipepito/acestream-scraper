import { test, expect } from '../src/fixtures';
import { SettingsPage } from '../src/pages/settings';

test.describe.configure({ mode: 'serial' });

/** Rescheduling a job restarts its interval from now, so next_run tells us the interval that is in force. */
const hoursUntilNextRun = (tasks: { task_name: string; next_run: string | null }[], name: string): number | undefined => {
  const next = tasks.find((t) => t.task_name === name)?.next_run;
  return next ? (new Date(next).getTime() - Date.now()) / 3_600_000 : undefined;
};

test.describe('settings', () => {
  test('the page has one section per concern and the engine reports online', async ({ page }) => {
    const settings = new SettingsPage(page);
    await settings.open();
    const headings = await page.getByRole('heading', { level: 2 }).allInnerTexts();
    expect(headings).toEqual(['Engine', 'Stream link formats', 'Automation', 'API access']);
    await settings.refreshEngineStatus();
    await expect(settings.engineStatus()).toContainText(/Online/, { timeout: 20_000 });
  });

  test('engine URL can be pointed at the stack engine', async ({ page, api, scenario }) => {
    const settings = new SettingsPage(page);
    await settings.open();
    await settings.saveEngineUrl(scenario.stack.engineUrl);
    await settings.expectAlert('Engine URL saved');
    expect(await api.getSetting('ace_engine_url')).toBe(scenario.stack.engineUrl);
    await settings.refreshEngineStatus();
    await expect(settings.engineStatus()).toContainText(/Online/, { timeout: 20_000 });
  });

  test('a named stream link format for Acexy can be added and made default', async ({ page, api, scenario }) => {
    const existing = (await api.listBaseUrls()).find((b) => b.name === scenario.playlist.baseUrlName);
    if (existing) await api.deleteBaseUrl(existing.id);

    const settings = new SettingsPage(page);
    await settings.open();
    await settings.addLinkFormat(scenario.playlist.baseUrlName, scenario.playlist.baseUrlPattern, true);
    await settings.expectAlert(`Link format "${scenario.playlist.baseUrlName}" added`);
    const entry = settings.linkFormats().getByText(scenario.playlist.baseUrlName, { exact: true });
    await expect(entry).toBeVisible();
    await expect(settings.linkFormats().getByRole('button', { name: 'Edit default link format' })).toHaveCount(0);
    const saved = (await api.listBaseUrls()).find((b) => b.name === scenario.playlist.baseUrlName);
    expect(saved?.pattern).toBe(scenario.playlist.baseUrlPattern);
    expect(saved?.is_default).toBe(true);
  });

  test('automation intervals save, reschedule the jobs and report in the snackbar', async ({ page, api }) => {
    const settings = new SettingsPage(page);
    await settings.open();
    await settings.saveInterval('Scrape sources every (hours)', '12');
    await settings.expectAlert('Sources will be scraped every 12 h');
    expect(await api.getSetting('rescrape_interval')).toBe('12');
    await expect.poll(async () => hoursUntilNextRun(await api.backgroundTasks(), 'url_scraping'), { timeout: 15_000 }).toBeCloseTo(12, 0);
    await settings.saveInterval('Scrape sources every (hours)', '24');
    await settings.expectAlert('Sources will be scraped every 24 h');

    await settings.saveInterval('Refresh EPG every (hours)', '2');
    await settings.expectAlert('EPG will refresh every 2 h');
    expect(await api.getSetting('epg_refresh_interval')).toBe('2');
    await expect.poll(async () => hoursUntilNextRun(await api.backgroundTasks(), 'epg_refresh'), { timeout: 15_000 }).toBeCloseTo(2, 0);
    await settings.saveInterval('Refresh EPG every (hours)', '1');
    await settings.expectAlert('EPG will refresh every 1 h');

    await expect(settings.appIdSwitch()).toBeVisible();
    await expect(page.getByText('Adds the app id to acestream:// links for players that require it (rare).')).toBeVisible();
  });
});

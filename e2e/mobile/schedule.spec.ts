import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: schedule start times save and survive reload`, async ({ page }) => {
    let anchors = { timezone: 'UTC', url_scraping: null as string | null, epg_refresh: null as string | null, channel_status: null as string | null };
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      else if (path === '/config/schedule-anchors') {
        if (route.request().method() === 'PUT') anchors = route.request().postDataJSON();
        data = anchors;
      } else if (path === '/config/check-engine') data = { use_dedicated: false, url: '', managed: false };
      else if (path === '/config/playback-routing') data = { use_acexy: false, acexy_url: 'http://localhost:8080' };
      else if (path === '/config/acestream_status') data = { status: 'online', message: 'Engine online' };
      else if (path === '/config/rescrape_interval' || path === '/config/epg_refresh_interval') data = { value: '6' };
      else if (path === '/config/channel_status_interval') data = { value: '60' };
      else if (path.startsWith('/config/')) data = { value: 'false' };
      else if (path === '/base-urls') data = [];
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/settings?tab=automation');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('form', { name: 'Schedule start times', exact: true })).toBeVisible();
    await page.getByRole('textbox', { name: 'Schedule timezone' }).fill('Europe/Madrid');
    await page.getByLabel('Scrape sources start time').fill('03:15');
    await page.getByLabel('EPG refresh start time').fill('02:00');
    await page.getByLabel('Stream checks start time').fill('03:30');
    await page.getByRole('button', { name: 'Save start times' }).click();
    await expect(page.getByText('Schedule start times saved.')).toBeVisible();
    expect(anchors).toEqual({ timezone: 'Europe/Madrid', url_scraping: '03:15', epg_refresh: '02:00', channel_status: '03:30' });
    await page.reload();
    await expect(page.getByLabel('Scrape sources start time')).toHaveValue('03:15');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`schedule-${mode}.png`), fullPage: true });
    expect(errors).toEqual([]);
  });
}

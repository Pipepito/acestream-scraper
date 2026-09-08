import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: save Acexy routing and switch back to direct playback`, async ({ page }) => {
    let routing = { use_acexy: false, acexy_url: 'http://localhost:8080' };
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.route('**/api/**', async (route) => {
      const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      else if (path === '/config/playback-routing') {
        if (route.request().method() === 'PUT') routing = route.request().postDataJSON();
        data = routing;
      } else if (path === '/config/acestream_status') data = { status: 'online', message: 'Engine online' };
      else if (path === '/config/ace_engine_url') data = { value: 'http://localhost:6878' };
      else if (path === '/config/rescrape_interval' || path === '/config/epg_refresh_interval') data = { value: '24' };
      else if (path === '/config/channel_status_interval') data = { value: '60' };
      else if (path.startsWith('/config/')) data = { value: 'false' };
      else if (path === '/base-urls') data = [];
      await route.fulfill({ json: data });
    });
    await page.addInitScript((value) => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/settings');
    const toggle = page.getByRole('checkbox', { name: 'Route playback through Acexy' });
    await expect(toggle).not.toBeChecked();
    await toggle.check();
    await page.getByRole('textbox', { name: 'Acexy URL' }).fill('http://proxy.lan:8080');
    await page.getByRole('button', { name: 'Save playback routing' }).click();
    await expect(page.getByText('Playback routing saved.')).toBeVisible();
    expect(routing).toEqual({ use_acexy: true, acexy_url: 'http://proxy.lan:8080' });
    await page.reload();
    await expect(toggle).toBeChecked();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`routing-${mode}.png`), fullPage: true });
    await toggle.uncheck();
    await page.getByRole('button', { name: 'Save playback routing' }).click();
    await expect(page.getByText('Playback routing saved.')).toBeVisible();
    expect(routing.use_acexy).toBe(false);
    await page.getByRole('tab', { name: 'Automation', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Automation', exact: true })).toBeVisible();
    await expect(page.getByRole('checkbox', { name: 'Append PID to stream links' })).toBeHidden();
    await expect(page).toHaveURL(/tab=automation/);
    await page.reload();
    await expect(page.getByRole('tab', { name: 'Automation', exact: true })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('tab', { name: 'Stream links', exact: true }).click();
    await expect(page.getByRole('checkbox', { name: 'Append PID to stream links' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Public address', exact: true })).toHaveCount(0);
    await page.getByRole('tab', { name: 'API access', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'API token', exact: true })).toBeVisible();
    if (await page.getByRole('button', { name: 'open drawer' }).isVisible()) await page.getByRole('button', { name: 'open drawer' }).click();
    await expect(page.getByRole('link', { name: 'WARP', exact: true })).toBeVisible();
    expect(errors).toEqual([]);
  });
}

import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: WARP exclusions, startup settings and reconnect`, async ({ page }) => {
    let exclusions = { hosts: [] as string[], active_hosts: [] as string[], revision: 'a'.repeat(64), applied: true, error: null as string | null };
    let runtime = { ENABLE_WARP: true, WARP_ENABLE_NAT: false, WARP_FORCE_IPV4: true };
    const operations: string[] = [];
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      if (path === '/warp/status') data = { running: true, connected: true, mode: 'warp+doh', account_type: 'free', ip: null, cf_trace: {} };
      if (path === '/warp/exclusions') {
        if (route.request().method() === 'PUT') {
          const hosts = route.request().postDataJSON().hosts;
          exclusions = { ...exclusions, hosts, active_hosts: hosts };
        }
        data = exclusions;
      }
      if (path === '/setup') {
        if (route.request().method() === 'PUT') runtime = { ...runtime, ...route.request().postDataJSON().runtime };
        data = { runtime, revision: 'b'.repeat(64), setup_complete: true, unavailable: {}, restart_required: false };
      }
      if (path === '/warp/connect' || path === '/warp/disconnect') {
        operations.push(path); data = { success: true, message: 'Done' };
      }
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/warp');
    await page.getByRole('button', { name: 'Add Atresmedia' }).click();
    await page.getByRole('button', { name: 'Save and apply exclusions' }).click();
    await expect(page.getByText('Exclusions saved and applied.')).toBeVisible();
    expect(exclusions.hosts).toEqual(['api.atresplayer.com', 'atres-live.atresmedia.com']);
    await page.reload();
    await expect(page.getByRole('textbox', { name: 'Hosts to exclude' })).toHaveValue('api.atresplayer.com\natres-live.atresmedia.com');
    await page.getByRole('checkbox', { name: 'Connect WARP before engines start' }).check();
    await page.getByRole('button', { name: 'Save startup settings' }).click();
    await expect(page.getByText('Startup settings saved. Restart the container to apply changes.')).toBeVisible();
    expect(runtime.WARP_ENABLE_NAT).toBe(true);
    await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
    await expect.poll(() => operations).toEqual(['/warp/disconnect', '/warp/connect']);
    await page.getByRole('textbox', { name: 'Hosts to exclude' }).fill('');
    await page.getByRole('button', { name: 'Save and apply exclusions' }).click();
    await expect.poll(() => exclusions.hosts).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`warp-${mode}.png`), fullPage: true });
    expect(errors).toEqual([]);
  });
}

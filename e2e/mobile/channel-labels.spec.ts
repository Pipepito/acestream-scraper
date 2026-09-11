import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: channel numbers and signal labels remain readable`, async ({ page }, testInfo) => {
    const channel = { id: 1, name: 'Example TV', channel_number: 123, is_active: true, is_favorite: false, acestream_channels: [] };
    const stream = { id: 'a'.repeat(40), name: 'Example stream', is_online: false, is_active: true, tv_channel_id: null };
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname.replace('/api/v1', '');
      let data: unknown = {};
      if (path === '/startup') data = { status: 'ready', phase: 'Ready to use', events: [] };
      else if (path === '/tv-channels') data = { items: [channel], total: 1 };
      else if (path === '/acestream-channels') data = { items: [stream], total: 1 };
      else if (path === '/epg/sources' || path === '/remote-players') data = [];
      else if (path.endsWith('/groups')) data = [];
      await route.fulfill({ json: data });
    });
    await page.goto('/tv-channels');
    const number = page.getByRole('spinbutton', { name: 'Channel number for Example TV' });
    await expect(number).toBeVisible();
    await number.focus();
    await expect(number).toBeFocused();
    await expect(number).toHaveValue('123');
    if (page.viewportSize()!.width >= 900) {
      const cell = page.getByRole('cell').filter({ has: number });
      await expect(cell.locator('label')).toHaveCount(0);
      const bounds = await cell.boundingBox();
      const field = await number.boundingBox();
      expect(field!.y).toBeGreaterThanOrEqual(bounds!.y);
      expect(field!.y + field!.height).toBeLessThanOrEqual(bounds!.y + bounds!.height);
    }
    await page.screenshot({ path: testInfo.outputPath('number-field.png') });
    await page.goto('/acestream-channels');
    const signal = page.getByText('No signal verified', { exact: true }).first();
    await expect(signal).toBeVisible();
    expect(await signal.evaluate(el => el.scrollWidth <= el.clientWidth && el.scrollHeight <= el.clientHeight)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath('signal-label.png') });
    expect(errors).toEqual([]);
  });
}

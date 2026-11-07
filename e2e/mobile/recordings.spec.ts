import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: recording history, editing and stop work without live media`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    const now = Date.now();
    let row = { id: 'a'.repeat(32), tv_channel_id: 1, snapshot: { title: 'International programme with a long title for narrow screens', channel_name: 'One' },
      start_time: new Date(now - 60000).toISOString(), end_time: new Date(now + 3600000).toISOString(), timezone: 'Europe/Madrid',
      state: 'recording', revision: 1, protected: false, actual_start: new Date(now).toISOString(), actual_end: null,
      reason: null, gaps: [], files: [], attempts: [], created_at: new Date(now).toISOString() };
    let stopped = false;
    await page.route('**/api/**', async route => {
      const url = new URL(route.request().url());
      let data: unknown = { status: 'ready', phase: 'Ready to use', events: [] };
      if (url.pathname === '/api/v1/setup') data = { setup_complete: true, restart_required: false };
      else if (url.pathname === '/api/v1/recordings') data = { total: 1, items: [row] };
      else if (url.pathname === '/api/v1/recordings/capabilities') data = { enabled: true, available: true };
      else if (url.pathname.endsWith('/stop')) { stopped = true; row = { ...row, state: 'partial', revision: 2 }; data = row; }
      await route.fulfill({ json: data });
    });
    await page.goto('/recordings');
    await expect(page.getByRole('heading', { name: 'Recordings', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: row.snapshot.title })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.getByRole('button', { name: 'Edit times' }).click();
    await expect(page.getByRole('dialog', { name: 'Edit recording' })).toBeVisible();
    await expect(page.getByLabel('Start', { exact: true })).toBeDisabled();
    await expect(page.getByLabel('End', { exact: true })).toBeEnabled();
    await page.getByRole('button', { name: 'Cancel', exact: true }).click();
    await page.getByRole('button', { name: 'Stop recording' }).click();
    await expect.poll(() => stopped).toBe(true);
    await expect(page.getByText('partial', { exact: true })).toBeVisible();
    await page.screenshot({ path: test.info().outputPath(`recordings-${mode}.png`), fullPage: true });
    expect(errors).toEqual([]);
  });
}

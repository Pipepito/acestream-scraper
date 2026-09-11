import { test, expect } from '@playwright/test';

for (const mode of ['light', 'dark']) {
  test(`${mode}: startup, diagnostics and confirmed recovery`, async ({ page }) => {
    await page.addInitScript((theme) => localStorage.setItem('app-theme-mode', theme), mode);
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    let status = 'starting';
    const actions: string[] = [];
    await page.route('**/api/v1/startup**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (path.endsWith('/diagnostics')) {
        await route.fulfill({ body: '{"status":"failed"}', contentType: 'application/json' });
        return;
      }
      if (route.request().method() === 'POST') {
        actions.push(route.request().postDataJSON().action);
        status = 'ready';
      }
      await route.fulfill({ json: {
        status, phase: status === 'starting' ? 'Importing TV channels' : status === 'failed' ? 'Database update stopped' : 'Ready to use',
        recovery_token: 'test-nonce', recovery_available: true,
        guidance: status === 'failed' ? 'The data drive is full. Free some space, then try again.' : null,
        events: [{ time: '2026-09-06T11:00:00Z', level: 'info', message: 'Backup saved before applying database updates' }],
      } });
    });
    await page.goto('/startup');
    await expect(page.getByRole('heading', { name: 'Getting your app ready' })).toBeVisible();
    await expect(page.getByText('Importing TV channels')).toBeVisible();
    status = 'failed';
    await expect(page.getByRole('heading', { name: 'Startup needs your attention' })).toBeVisible();
    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download diagnostics' }).click();
    expect((await download).suggestedFilename()).toBe('startup-diagnostics.json');
    await page.getByRole('button', { name: 'Start fresh', exact: true }).click();
    await expect(page.getByRole('dialog')).toContainText('backed up first');
    await page.getByRole('button', { name: 'Cancel' }).click();
    expect(actions).toEqual([]);
    await page.getByRole('button', { name: 'Recover readable data' }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('dialog')).toContainText('Damaged or incompatible rows may be skipped');
    await page.getByRole('button', { name: 'Back up and rebuild' }).click();
    await expect(page.getByRole('link', { name: 'Open app' })).toBeVisible();
    expect(actions).toEqual(['salvage']);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect(errors).toEqual([]);
    await page.screenshot({ path: `/tmp/acestream-startup-${mode}-${test.info().project.name}.png`, fullPage: true });
  });
}

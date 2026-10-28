import { readFileSync } from 'node:fs';
import path from 'node:path';
import { test, expect } from '@playwright/test';

interface Option { name: string; default: string | number | boolean; }
const options = JSON.parse(readFileSync(path.resolve(__dirname, '../../backend/app/config/runtime-options.json'), 'utf8')) as Option[];

for (const mode of ['light', 'dark']) {
  test(`${mode}: first-run wizard saves explicitly and survives reload`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    let state = {
      version: 1, setup_complete: false, revision: 'a'.repeat(64), restart_required: false, api_protected: false,
      runtime: Object.fromEntries(options.map(option => [option.name, option.default])), options,
      unavailable: { ENABLE_IPFS: 'This image does not include IPFS.' },
    };
    let saves = 0;
    await page.route('**/api/**', async route => {
      const request = route.request();
      const endpoint = new URL(request.url()).pathname.replace('/api/v1', '').replace(/\/$/, '');
      let data: unknown = {};
      if (endpoint === '/startup') data = { status: 'ready', phase: 'Ready', events: [] };
      if (endpoint === '/setup') {
        if (request.method() === 'PUT') {
          const update = request.postDataJSON();
          expect(update.expected_revision).toBe(state.revision);
          state = { ...state, runtime: update.runtime, setup_complete: true, revision: 'b'.repeat(64), restart_required: true };
          saves++;
        }
        data = state;
      }
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/setup');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Set up scraper' })).toBeVisible();
    await page.getByRole('spinbutton', { name: 'Maximum browser sessions' }).fill('5');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`setup-playback-${mode}.png`), fullPage: true });
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText(/No API token is configured/)).toBeVisible();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByRole('checkbox', { name: 'IPFS', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText('Maximum browser sessions: 5')).toBeVisible();
    await page.getByRole('button', { name: 'Advanced settings' }).click();
    await expect(page.getByRole('spinbutton', { name: 'Source timeout (seconds)', exact: true })).toBeVisible();
    expect(saves).toBe(0);
    await page.getByRole('button', { name: 'Save setup' }).click();
    await expect(page.getByText(/Setup saved. Restart the container/)).toBeVisible();
    const title = await page.getByRole('heading', { name: 'Set up scraper' }).boundingBox();
    expect(title?.y).toBeGreaterThanOrEqual(56);
    await expect(page.getByRole('link', { name: 'Add an official broadcaster' })).toHaveAttribute('href', '/scraper');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`setup-finished-${mode}.png`), fullPage: true });
    await page.reload();
    await expect(page.getByRole('spinbutton', { name: 'Maximum browser sessions' })).toHaveValue('5');
    await expect(page.getByText('Restart required', { exact: true })).toBeVisible();
    expect(saves).toBe(1);
    expect(errors).toEqual([]);
  });
}

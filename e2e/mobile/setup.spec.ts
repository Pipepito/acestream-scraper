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
      runtime: { ...Object.fromEntries(options.map(option => [option.name, option.default])), PLAYER_MAX_SESSIONS: 7, ENABLE_ACESTREAM_ENGINE: true, ENABLE_ACESTREAM_CHECK_ENGINE: true, ENABLE_ACEXY: true, ACEXY_LISTEN_ADDR: ":8084", ACEXY_BUFFER_SIZE: "5MiB" }, options,
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
          if (Object.keys(update.runtime).length) {
            expect(update.runtime.ACE_CHECK_ENGINE_URL).toBe('');
            expect(update.runtime.ACEXY_BUFFER_SIZE).toBe('10MiB');
          }
          state = { ...state, runtime: { ...state.runtime, ...update.runtime }, setup_complete: update.setup_complete, revision: 'b'.repeat(64), restart_required: true };
          saves++;
        }
        data = state;
      }
      if (endpoint === '/scrapers/urls' || endpoint === '/epg/sources') data = [];
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/changelog');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Set up scraper' })).toBeVisible();
    await expect(page.getByRole('dialog', { name: 'Set up scraper' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Channel source link' })).toBeVisible();
    await expect(page.getByRole('spinbutton')).toHaveCount(0);
    await page.screenshot({ path: test.info().outputPath(`setup-sources-${mode}.png`), animations: 'disabled' });
    await page.getByRole('button', { name: 'Connection settings (advanced)' }).click();
    await expect(page.getByRole('spinbutton', { name: 'Maximum browser sessions' })).toHaveValue('7');
    await expect(page.getByRole('textbox', { name: 'Playback engine address', exact: true })).toHaveValue('http://localhost:6878');
    await expect(page.getByRole('textbox', { name: 'Dedicated checking engine address' })).toHaveValue('http://127.0.0.1:6880');
    await page.getByRole('spinbutton', { name: 'Maximum browser sessions' }).fill('5');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`setup-playback-${mode}.png`), fullPage: false, animations: 'disabled' });
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText(/No API token is configured/)).toBeVisible();
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByRole('checkbox', { name: 'IPFS', exact: true })).toBeDisabled();
    await page.getByRole('button', { name: 'Acexy connection and buffering' }).click();
    await expect(page.getByRole('textbox', { name: 'Acexy listen address' })).toHaveValue(':8084');
    await page.getByRole('textbox', { name: 'Acexy buffer size' }).fill('10MiB');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText('Maximum browser sessions: 5')).toBeVisible();
    await page.getByRole('button', { name: 'Advanced settings' }).click();
    await expect(page.getByRole('spinbutton', { name: 'Source timeout (seconds)', exact: true })).toBeVisible();
    expect(saves).toBe(0);
    await page.getByRole('button', { name: 'Save setup' }).click();
    await expect(page.getByText(/Setup saved. Restart the container/)).toBeVisible();
    const title = await page.getByRole('heading', { name: 'Connection settings' }).boundingBox();
    expect(title?.y).toBeGreaterThanOrEqual(0);
    await page.getByRole('button', { name: 'Return to setup' }).click();
    await page.getByRole('button', { name: 'Continue', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Use EPG dobleM' })).toBeVisible();
    await page.screenshot({ path: test.info().outputPath(`setup-guide-${mode}.png`), animations: 'disabled' });
    await page.getByRole('button', { name: 'Finish setup' }).click();
    await expect(page.getByRole('heading', { name: 'Setup saved', exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`setup-finished-${mode}.png`), fullPage: false, animations: 'disabled' });
    await page.getByRole('button', { name: 'Close', exact: true }).click();
    await page.reload();
    await expect(page.getByRole('dialog', { name: 'Set up scraper' })).toHaveCount(0);
    await page.getByRole('link', { name: 'Review setup' }).click();
    await page.getByRole('button', { name: 'Connection settings (advanced)' }).click();
    await expect(page.getByRole('spinbutton', { name: 'Maximum browser sessions' })).toHaveValue('5');
    await expect(page.getByText('Restart required', { exact: true })).toBeVisible();
    expect(saves).toBe(2);
    expect(errors).toEqual([]);
  });
}

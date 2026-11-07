import { readFileSync } from 'node:fs';
import path from 'node:path';
import { test, expect } from '@playwright/test';

interface Option { name: string; default: string | number | boolean; }
const options = JSON.parse(readFileSync(path.resolve(__dirname, '../../backend/app/config/runtime-options.json'), 'utf8')) as Option[];

for (const mode of ['light', 'dark']) {
  test(`${mode}: network settings are available after setup and save only edited options`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('response', response => { if (response.url().includes('/api/') && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    let state = {
      version: 1, setup_complete: true, revision: 'a'.repeat(64), restart_required: false, api_protected: false,
      runtime: { ...Object.fromEntries(options.map(option => [option.name, option.default])), FORWARDED_ALLOW_IPS: '127.0.0.1,192.168.0.0/16' }, options, unavailable: {},
    };
    let saves = 0;
    await page.route('**/api/**', async route => {
      const request = route.request();
      const endpoint = new URL(request.url()).pathname.replace('/api/v1', '').replace(/\/$/, '');
      let data: unknown = {};
      if (endpoint === '/startup') data = { status: 'ready', phase: 'Ready', events: [] };
      else if (endpoint === '/auth/status') data = { mode: 'open', user: null, permissions: [], csrf: 'test-csrf', legacy_token: false, account_transport: 'local_http' };
      else if (endpoint === '/setup') {
        if (request.method() === 'PUT') {
          const update = request.postDataJSON();
          expect(update).toEqual({ expected_revision: state.revision, runtime: { FORWARDED_ALLOW_IPS: '127.0.0.1,172.17.0.16' }, setup_complete: true });
          state = { ...state, runtime: { ...state.runtime, ...update.runtime }, revision: 'b'.repeat(64), restart_required: true };
          saves++;
        }
        data = state;
      } else if (endpoint === '/config/check-engine') data = { use_dedicated: false, url: '', managed: false };
      else if (endpoint === '/config/playback-routing') data = { use_acexy: false, acexy_url: '' };
      else if (endpoint === '/config/acestream_status') data = { status: 'offline' };
      else if (endpoint === '/config/rescrape_interval' || endpoint === '/config/epg_refresh_interval') data = { value: '24' };
      else if (endpoint === '/config/channel_status_interval') data = { value: '60' };
      else if (endpoint.startsWith('/config/')) data = { value: 'false' };
      else if (endpoint === '/base-urls') data = [];
      await route.fulfill({ json: data });
    });
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), mode);
    await page.goto('/settings?tab=network');
    await expect(page.getByRole('tab', { name: 'Network', exact: true })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    const proxy = page.getByRole('textbox', { name: 'Trusted reverse proxies' });
    await expect(proxy).toHaveValue('127.0.0.1,192.168.0.0/16');
    await expect(page.getByText(/adding a narrower range does not remove/)).toBeVisible();
    await proxy.fill('127.0.0.1,172.17.0.16');
    await proxy.press('Tab');
    expect(saves).toBe(0);
    await page.getByRole('button', { name: 'Save network settings' }).click();
    await expect(page.getByText('Network settings saved.', { exact: true })).toBeVisible();
    await expect(page.getByText(/Restart required. Saved network changes/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`network-settings-${mode}.png`), fullPage: true, animations: 'disabled' });
    await page.reload();
    await expect(proxy).toHaveValue('127.0.0.1,172.17.0.16');
    await expect(page.getByRole('button', { name: 'Save network settings' })).toBeDisabled();
    expect(saves).toBe(1);
    expect(errors).toEqual([]);
  });
}

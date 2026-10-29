import { readFileSync } from 'node:fs';
import path from 'node:path';
import { test, expect } from '@playwright/test';

const docs = path.resolve(__dirname, '../../docs');
test('recording directory generates matching persistent run and Compose mounts', async ({ page }) => {
  await page.route('**/builder/**', async route => {
    const name = path.basename(new URL(route.request().url()).pathname);
    if (!['app.js', 'hub.js', 'style.css', 'hub.css', 'runtime-options.json'].includes(name)) return route.abort();
    await route.fulfill({ body: readFileSync(path.join(docs, 'builder', name)), contentType: name.endsWith('.js') ? 'text/javascript' : name.endsWith('.css') ? 'text/css' : 'application/json' });
  });
  await page.route('**/builder-test', route => route.fulfill({ body: readFileSync(path.join(docs, 'index.html')), contentType: 'text/html' }));
  await page.route('**/release-status.json', route => route.fulfill({ json: {} }));
  await page.route('https://fonts.googleapis.com/**', route => route.fulfill({ body: '', contentType: 'text/css' }));
  await page.goto('/builder-test');
  await page.getByRole('radio', { name: /Pre-release/ }).check();
  await page.getByText('Advanced settings', { exact: true }).click();
  await page.getByText('Web player & guide refresh', { exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Host folder or volume name for Recordings', exact: true })).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Recording folder', exact: true }).fill('/recordings');
  const host = page.getByRole('textbox', { name: 'Host folder or volume name for Recordings', exact: true });
  await expect(host).toHaveValue('./recordings');
  await host.fill('/srv/recordings');
  const run = page.getByRole('tabpanel', { name: 'docker run', exact: true });
  await expect(run).toContainText('RECORDINGS_DIR=/recordings');
  await expect(run).toContainText('/srv/recordings:/recordings');
  await page.getByRole('textbox', { name: 'Recording folder', exact: true }).fill('/media/dvr');
  await expect(run).toContainText('/srv/recordings:/media/dvr');
  await page.getByRole('tab', { name: 'docker compose', exact: true }).click();
  const compose = page.getByRole('tabpanel', { name: 'docker compose', exact: true });
  await expect(compose).toContainText('RECORDINGS_DIR=/media/dvr');
  await expect(compose).toContainText('/srv/recordings:/media/dvr');
  await page.getByRole('textbox', { name: 'Recording folder', exact: true }).clear();
  await expect(compose).not.toContainText('RECORDINGS_DIR');
  await expect(compose).not.toContainText('/srv/recordings');
});

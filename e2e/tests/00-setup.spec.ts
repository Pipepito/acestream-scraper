import { test, expect } from '../src/fixtures';

test('setup opens automatically on first run and saves the deployment defaults', async ({ page, api }) => {
  const access = await (await api.raw('get', '/api/v1/auth/status')).json();
  if (access.mode === 'pending') {
    await page.goto('/changelog');
    await page.getByRole('checkbox', { name: 'Enable user management' }).uncheck();
    await page.getByRole('button', { name: 'Continue without accounts' }).click();
    await expect(page.getByRole('button', { name: 'Continue without accounts' })).toHaveCount(0);
  }
  const before = await (await api.raw('get', '/api/v1/setup')).json() as {
    setup_complete: boolean; runtime: Record<string, string | number | boolean>;
  };
  await page.goto('/changelog');
  const wizard = page.getByRole('dialog', { name: 'Set up scraper' });
  if (before.setup_complete) {
    await expect(wizard).toHaveCount(0);
    await page.goto('/setup');
  }
  await expect(wizard).toBeVisible();
  await expect(wizard.getByRole('textbox', { name: 'Channel source link' })).toBeVisible();
  await expect(wizard.getByRole('spinbutton')).toHaveCount(0);
  await wizard.getByRole('button', { name: 'Continue', exact: true }).click();
  await expect(wizard.getByRole('button', { name: 'Use EPG dobleM' })).toBeVisible();
  await wizard.getByRole('button', { name: 'Finish setup', exact: true }).click();
  await expect(wizard.getByRole('heading', { name: 'Setup saved', exact: true })).toBeVisible();
  await wizard.getByRole('button', { name: 'Close', exact: true }).click();
  const after = await (await api.raw('get', '/api/v1/setup')).json();
  expect(after.setup_complete).toBe(true);
  expect(after.runtime).toEqual(before.runtime);
  await page.reload();
  await expect(wizard).toHaveCount(0);
});

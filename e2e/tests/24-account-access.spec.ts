import { test, expect } from '../src/fixtures';

test('accounts isolate viewing from administration and can be disabled in Settings', async ({ page }) => {
  const password = 'local E2E account password';
  let csrf = '';
  const status = async () => {
    const response = await page.request.get('/api/v1/auth/status');
    expect(response.ok()).toBeTruthy();
    const data = await response.json(); csrf = data.csrf; return data;
  };
  await status();
  await page.goto('/settings?tab=access');
  await page.getByLabel('Administrator username').fill('e2eowner');
  await page.getByLabel(/^Password/).fill(password);
  await page.getByLabel(/^Confirm password/).fill(password);
  await page.getByRole('button', { name: 'Create administrator and continue' }).click();
  await expect(page.getByRole('heading', { name: 'Change your password' })).toBeVisible();
  try {
    await page.getByRole('checkbox', { name: 'Allow IPTV without credentials on trusted local networks' }).check();
    await page.getByLabel('Local IPTV networks').fill('192.168.23.0/24');
    await page.getByRole('button', { name: 'Save access policy' }).click();
    await expect(page.getByText('Access policy saved.')).toBeVisible();
    await page.goto('/integrations/tv-casting');
    await expect(page.getByRole('heading', { level: 1, name: 'TV casting' })).toBeVisible();
    await page.getByRole('checkbox', { name: 'Offer H.264 compatibility conversion' }).check();
    await page.getByRole('button', { name: 'Save casting settings' }).click();
    await expect(page.getByText('TV casting settings saved.')).toBeVisible();
    await page.reload();
    await expect(page.getByRole('checkbox', { name: 'Offer H.264 compatibility conversion' })).toBeChecked();
    await page.goto('/settings?tab=access');
    await expect(page.getByRole('checkbox', { name: 'Allow IPTV without credentials on trusted local networks' })).toBeChecked();
    await expect(page.getByLabel('Local IPTV networks')).toHaveValue('192.168.23.0/24');
    await expect(page.getByLabel('Home networks')).toHaveCount(0);
    await page.getByRole('checkbox', { name: 'Allow IPTV without credentials on trusted local networks' }).uncheck();
    await page.getByRole('button', { name: 'Save access policy' }).click();
    await expect(page.getByText('Access policy saved.')).toBeVisible();
    await page.getByLabel('New account username').fill('e2eviewer');
    await page.getByLabel('Initial password').fill(password);
    await page.getByRole('button', { name: 'Create account', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'e2eviewer', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Sign out', exact: true }).click();
    await page.getByLabel(/^Username/).fill('e2eviewer');
    await page.getByLabel(/^Password/).fill(password);
    await page.getByRole('button', { name: 'Sign in', exact: true }).last().click();
    await expect(page.getByRole('combobox', { name: 'View' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Watch', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings', exact: true })).toHaveCount(0);
    // These direct requests deliberately test the server boundary, independently
    // of the hidden navigation. Request-context calls are not page API errors.
    expect((await page.request.get('/api/v1/config')).status()).toBe(403);
    expect((await page.request.get('/api/v1/cast/devices')).status()).toBe(403);
    await page.reload();
    await expect(page.getByRole('combobox', { name: 'View' })).toBeVisible();
  } finally {
    await status();
    const login = await page.request.post('/api/v1/auth/login', { headers: { 'X-CSRF-Token': csrf }, data: { username: 'e2eowner', password } });
    expect(login.ok()).toBeTruthy();
    await page.goto('/settings?tab=access');
    await page.getByLabel('Administrator password').fill(password);
    await page.getByRole('checkbox', { name: 'I understand that account protection will be removed' }).check();
    await page.getByRole('button', { name: 'Disable user management' }).click();
    await expect(page.getByRole('button', { name: 'Create administrator and continue' })).toBeVisible();
  }
});

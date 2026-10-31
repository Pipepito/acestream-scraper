import { test, expect } from '@playwright/test';

for (const theme of ['light', 'dark']) {
  test(`${theme}: first-run account choice needs no deployment secret`, async ({ page }) => {
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), theme);
    let enabled: boolean | undefined;
    await page.route('**/api/v1/auth/status', route => route.fulfill({ json: { mode: 'pending', user: null, permissions: [], csrf: 'test-csrf', legacy_token: false, account_transport: 'local_http' } }));
    await page.route('**/api/v1/auth/bootstrap', async route => {
      enabled = route.request().postDataJSON().enabled;
      await route.fulfill({ status: 409, json: { detail: 'Fixture stopped after checking the submitted choice' } });
    });
    await page.goto('/');
    await expect(page.getByRole('checkbox', { name: 'Enable user management' })).toBeChecked();
    await expect(page.getByText(/Accounts are available on this verified local connection/)).toBeVisible();
    await page.getByLabel('Administrator username').fill('owner');
    await page.getByLabel(/^Password/).fill('short');
    await page.getByLabel(/^Confirm password/).fill('short');
    await page.getByRole('button', { name: 'Create administrator and continue' }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Use 12–128 characters.' })).toBeVisible();
    expect(enabled).toBeUndefined();
    await page.getByRole('checkbox', { name: 'Enable user management' }).uncheck();
    await expect(page.getByRole('textbox', { name: 'Administrator username' })).toHaveCount(0);
    await page.getByRole('button', { name: 'Continue without accounts' }).click();
    await expect.poll(() => enabled).toBe(false);
    await expect(page.getByRole('alert').last()).toContainText('Fixture stopped');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });

  test(`${theme}: a viewing account sees only its sections and no administration`, async ({ page }) => {
    await page.addInitScript(value => localStorage.setItem('app-theme-mode', value), theme);
    await page.route('**/api/**', async route => {
      const path = new URL(route.request().url()).pathname;
      if (path === '/api/v1/auth/status') return route.fulfill({ json: { mode: 'accounts', user: { id: 'viewer', username: 'viewer', administrator: false, enabled: true, permissions: ['channels', 'guide'] }, permissions: ['channels', 'guide'], csrf: 'test-csrf', legacy_token: false, account_transport: 'local_http' } });
      if (path === '/api/v1/view/channels') return route.fulfill({ json: { total: 1, items: [{ id: 'a'.repeat(40), name: 'A very long channel name for a compact phone layout', category: 'Documentaries', online: null }] } });
      if (path === '/api/v1/view/guide') return route.fulfill({ json: [] });
      throw new Error(`Viewing page requested an unexpected API: ${path}`);
    });
    await page.goto('/settings?tab=access');
    await expect(page.getByRole('heading', { name: 'Watch', exact: true })).toBeVisible();
    await expect(page.getByText('A very long channel name for a compact phone layout')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Watch', exact: true })).toHaveCount(0);
    await page.getByRole('combobox', { name: 'View' }).click();
    await expect(page.getByRole('option')).toHaveCount(2);
    await page.getByRole('option', { name: 'Programme guide' }).click();
    await expect(page.getByText('No items to show.')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}

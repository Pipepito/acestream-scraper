import { test, expect } from '../src/fixtures';

test('setup opens automatically on first run and saves the deployment defaults', async ({ page, api }) => {
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
  await expect(wizard.getByRole('spinbutton', { name: 'Maximum browser sessions' }))
    .toHaveValue(String(before.runtime.PLAYER_MAX_SESSIONS));
  for (let step = 0; step < 3; step++) await wizard.getByRole('button', { name: 'Continue', exact: true }).click();
  await wizard.getByRole('button', { name: 'Save setup', exact: true }).click();
  await expect(wizard.getByText(/Setup saved\./)).toBeVisible();
  await wizard.getByRole('button', { name: 'Done', exact: true }).click();
  const after = await (await api.raw('get', '/api/v1/setup')).json();
  expect(after.setup_complete).toBe(true);
  expect(after.runtime).toEqual(before.runtime);
  await page.reload();
  await expect(wizard).toHaveCount(0);
});

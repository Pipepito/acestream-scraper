import { test, expect } from '../src/fixtures';

test('IDs remain manually copyable and assignment searches in place', async ({ page, api }) => {
  // Model an ordinary HTTP deployment where Clipboard API is absent.
  await page.addInitScript(() => Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true }));
  const target = (await api.listChannels({ page_size: 1, assigned: false })).items[0];
  const tv = (await api.listTvChannels()).items[0];
  expect(target).toBeTruthy();
  expect(tv).toBeTruthy();
  await page.goto('/acestream-channels');
  await page.getByRole('textbox', { name: 'Search', exact: true }).fill(target.name);
  const input = page.getByRole('textbox', { name: `Acestream ID ${target.id}`, exact: true });
  await page.getByRole('button', { name: `copy acestream id ${target.id}`, exact: true }).click();
  await expect(input).toBeFocused();
  expect(await input.evaluate((element: HTMLInputElement) => [element.selectionStart, element.selectionEnd])).toEqual([0, target.id.length]);
  await expect(page.getByRole('alert').filter({ hasText: 'ID selected.' })).toBeVisible();
  await expect(page.getByRole('columnheader', { name: 'Network ID', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: `More actions for ${target.name}`, exact: true }).first().click();
  await page.getByRole('menuitem', { name: 'Link to a TV channel' }).click();
  const dialog = page.getByRole('dialog', { name: 'Assign to TV Channel' });
  await dialog.getByRole('combobox').fill(tv.name);
  await page.getByRole('option', { name: new RegExp(tv.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) }).first().click();
  await expect(dialog.getByRole('button', { name: 'Assign', exact: true })).toBeEnabled();
  await page.screenshot({ path: 'test-results/acestream-assignment.png' });
  await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect(dialog).toBeHidden();
  await page.screenshot({ path: 'test-results/acestream-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('textbox', { name: `Acestream ID ${target.id}`, exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: 'test-results/acestream-mobile.png' });
  await page.getByRole('button', { name: 'Switch to dark theme' }).click();
  await expect(page.getByRole('button', { name: 'Switch to light theme' })).toBeVisible();
  await page.screenshot({ path: 'test-results/acestream-dark.png' });
});

test('run now calls the scheduled job and has no manual status entry', async ({ page, api }) => {
  await page.goto('/acestream-channels');
  const response = page.waitForResponse(res => res.url().endsWith('/background-tasks/channel_status/run') && res.request().method() === 'POST');
  await page.getByRole('button', { name: 'Run status check now', exact: true }).click();
  expect((await response).ok()).toBe(true);
  await expect(page.getByRole('alert').filter({ hasText: /job queued|job is already running/ })).toBeVisible();
  const statuses = await (await api.raw('get', '/api/v1/background-tasks/status')).json();
  expect(statuses.some((job: { task_name: string }) => job.task_name === 'manual_channel_status')).toBe(false);
  expect(statuses.some((job: { task_name: string }) => job.task_name === 'channel_status')).toBe(true);
});

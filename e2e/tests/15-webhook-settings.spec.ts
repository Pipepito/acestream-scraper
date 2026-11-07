import { test, expect } from '../src/fixtures';

test('invalid webhook updates preserve the saved setting and Settings stays usable', async ({ page, request }) => {
  const path = '/api/v1/config/notification_webhook_url';
  const original = await (await request.get(path)).json();
  expect(original.value, 'use a disposable E2E database without a real webhook').toBe('');
  try {
    expect((await request.put(path, { data: { value: 'https://hooks.example/message?token=private' } })).ok()).toBe(true);
    const saved = await (await request.get(path)).json();
    for (const value of ['https://hooks.example:bad/message?token=secret', 'http://[broken/message', 'https://hooks.example:65536/message']) {
      const rejected = await request.put(path, { data: { value } });
      expect(rejected.status()).toBe(422);
      expect(await rejected.text()).not.toContain('secret');
      expect(await (await request.get(path)).json()).toEqual(saved);
    }
    await page.goto('/settings?tab=automation');
    await expect(page.getByRole('textbox', { name: 'Webhook URL' })).toHaveValue(saved.value);
    await expect(page.getByRole('button', { name: 'Send test', exact: true })).toBeEnabled();
    const section = page.getByRole('region', { name: 'Notifications', exact: true });
    await section.getByRole('textbox', { name: 'Webhook URL' }).fill('');
    await section.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Notifications turned off.' })).toBeVisible();
    await expect.poll(async () => (await (await request.get(path)).json()).value).toBe('');
  } finally {
    expect((await request.put(path, { data: { value: '' } })).ok()).toBe(true);
  }
});

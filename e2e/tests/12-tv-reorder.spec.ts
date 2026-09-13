import { test, expect } from '../src/fixtures';

test('drag order previews numbers, saves and survives reload', async ({ page, api }) => {
  const before = (await api.listTvChannels()).items;
  test.skip(before.length < 2, 'Needs at least two channels in the local journey inventory.');
  const first = before[0], last = before[before.length - 1];
  try {
    await page.goto('/tv-channels');
    await page.getByRole('button', { name: 'Reorder channels', exact: true }).click();
    const list = page.getByRole('list', { name: 'Channel order' });
    await page.getByRole('button', { name: `Drag ${last.name}`, exact: true }).dragTo(page.getByRole('button', { name: `Drag ${first.name}`, exact: true }));
    await expect(list.getByRole('listitem').first()).toContainText(last.name);
    // The draft has not touched the database.
    expect((await api.listTvChannels()).items.map(c => c.id)).toEqual(before.map(c => c.id));
    await page.getByRole('button', { name: 'Save order', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Channel order and numbers saved.' })).toBeVisible();
    await page.reload();
    await page.getByRole('button', { name: 'Reorder channels', exact: true }).click();
    await expect(page.getByRole('list', { name: 'Channel order' }).getByRole('listitem').first()).toContainText(last.name);
    const after = (await api.listTvChannels()).items;
    expect(after[0].id).toBe(last.id);
    expect(after.map(c => c.channel_number)).toEqual(after.map((_, index) => index + 1));
    await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  } finally {
    for (const channel of before) {
      const result = await api.raw('put', `/api/v1/tv-channels/${channel.id}`, { channel_number: channel.channel_number ?? null });
      expect(result.ok()).toBe(true);
    }
  }
});

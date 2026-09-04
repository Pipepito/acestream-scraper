import { test, expect } from '../src/fixtures';
import { ChannelsPage } from '../src/pages/channels';

test.describe.configure({ mode: 'serial' });

const E2E_ID = 'e2e0000000000000000000000000000000000001';

test.describe('acestream channels', () => {
  test('the grid lists channels, the summary counts them and the filter bar narrows the list', async ({ page, api }) => {
    const all = await api.listChannels({ page_size: 50 });
    expect(all.total, 'channels exist from scraping/search journeys').toBeGreaterThan(0);
    const target = all.items[0];

    const channels = new ChannelsPage(page);
    await channels.open();
    await expect(channels.grid()).toBeVisible();
    await expect(channels.summary()).toContainText(new RegExp(`Channels\\s*${all.total}`));
    await expect(channels.row(target.name).first()).toBeVisible();

    await channels.filterByName(target.name);
    await expect(channels.row(target.name).first()).toBeVisible();
    const filtered = await api.listChannels({ search: target.name });
    await expect(channels.dataRows()).toHaveCount(filtered.items.length);
    await expect(channels.summary()).toContainText(new RegExp(`Matching filters\\s*${filtered.total}`));
    await channels.resetFilters();
  });

  test('a channel can be edited from the edit dialog', async ({ page, api }) => {
    const target = (await api.listChannels({ page_size: 5 })).items[0];
    const channels = new ChannelsPage(page);
    await channels.open();
    await channels.filterByName(target.name);
    const dialog = await channels.openEdit(target.name);
    await expect(dialog.getByRole('textbox', { name: 'Acestream ID' })).toHaveAttribute('readonly', '');
    await dialog.getByRole('textbox', { name: 'Group' }).fill('E2E Group');
    await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(dialog).toBeHidden();
    await channels.expectAlert(`Saved ${target.name}.`);
    await expect.poll(async () => (await api.getChannel(target.id))?.group, { timeout: 15_000 }).toBe('E2E Group');
    await expect(channels.row(target.name).first()).toContainText('E2E Group');
  });

  test('status checks reach the engine for one channel and for all channels', async ({ page, api }, testInfo) => {
    test.setTimeout(300_000);
    const target = (await api.listChannels({ page_size: 5 })).items[0];
    const channels = new ChannelsPage(page);
    await channels.open();
    await channels.filterByName(target.name);
    await channels.checkStatus(target.name);
    const checked = await expect
      .poll(async () => (await api.getChannel(target.id))?.last_checked, { timeout: 60_000, message: 'last_checked set by the engine probe' })
      .not.toBeNull()
      .then(() => api.getChannel(target.id));
    testInfo.annotations.push({ type: 'status', description: `${target.name}: online=${checked?.is_online} error=${checked?.check_error}` });
    await expect(channels.onlineChip(target.name).first()).toContainText(/Online|Offline/, { timeout: 30_000 });

    await channels.checkAllStatuses();
    await channels.expectAlert(/Checked \d+ channels: \d+ online, \d+ offline|started in the background/, 120_000);
  });

  test('a channel can be created by hand, hidden from the playlist and deleted again', async ({ page, api }) => {
    await api.deleteChannel(E2E_ID);
    const channels = new ChannelsPage(page);
    await channels.open();
    const dialog = await channels.openAdd();
    await expect(dialog.getByRole('button', { name: 'Save' })).toBeDisabled();
    await dialog.getByRole('textbox', { name: 'Name', exact: true }).fill('E2E Manual Channel');
    await dialog.getByRole('textbox', { name: 'Acestream ID' }).fill(E2E_ID);
    await dialog.getByRole('button', { name: 'Save' }).click();
    await expect(dialog).toBeHidden();
    await channels.expectAlert('Added E2E Manual Channel.');
    await expect.poll(async () => (await api.getChannel(E2E_ID))?.name, { timeout: 15_000 }).toBe('E2E Manual Channel');

    await channels.filterByName('E2E Manual Channel');
    await expect(channels.row('E2E Manual Channel')).toBeVisible();
    await channels.hideFromPlaylist('E2E Manual Channel');
    await channels.expectAlert('E2E Manual Channel is now hidden from the playlist.');
    await expect.poll(async () => (await api.getChannel(E2E_ID))?.is_active, { timeout: 15_000 }).toBe(false);
    await expect(channels.row('E2E Manual Channel')).toContainText('Hidden');
    await channels.showInPlaylist('E2E Manual Channel');
    await channels.expectAlert('E2E Manual Channel is back in the playlist.');
    await expect.poll(async () => (await api.getChannel(E2E_ID))?.is_active, { timeout: 15_000 }).toBe(true);

    await channels.deleteChannel('E2E Manual Channel');
    await channels.expectAlert('Deleted E2E Manual Channel.');
    await expect.poll(async () => api.getChannel(E2E_ID), { timeout: 15_000 }).toBeUndefined();
    await expect(channels.row('E2E Manual Channel')).toHaveCount(0);
  });

  test('the CSV export downloads a file with every channel', async ({ page, api }) => {
    const channels = new ChannelsPage(page);
    await channels.open();
    const downloadPromise = page.waitForEvent('download', { timeout: 30_000 });
    await channels.csvButton().click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/\.csv$/);
    const path = await download.path();
    expect(path).toBeTruthy();
    const { readFileSync } = await import('node:fs');
    const csv = readFileSync(path as string, 'utf8');
    const total = (await api.listChannels({ page_size: 1 })).total;
    expect(csv.split('\n').filter((l) => l.trim()).length).toBeGreaterThanOrEqual(total);
  });
});

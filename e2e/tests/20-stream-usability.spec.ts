import { test, expect } from '../src/fixtures';

test('manual additions can link immediately and similar names require review', async ({ page, api }) => {
  const tv = await api.createTvChannel({ name: 'E2E National Geographic' });
  const manualId = 'e2e3090000000000000000000000000000000001';
  const similarId = 'e2e3090000000000000000000000000000000002';
  try {
    await page.goto('/acestream-channels');
    await page.getByRole('button', { name: 'Add channel', exact: true }).click();
    const editor = page.getByRole('dialog', { name: 'Add channel', exact: true });
    await editor.getByRole('textbox', { name: /^Name/ }).fill('E2E manually linked');
    await editor.getByRole('textbox', { name: /^Acestream ID/ }).fill(manualId);
    await editor.getByRole('combobox', { name: 'Link to TV channel (optional)' }).fill(tv.name);
    await page.getByRole('option', { name: tv.name, exact: true }).click();
    await editor.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(editor).toBeHidden();
    expect((await api.getChannel(manualId))?.tv_channel_id).toBe(tv.id);

    await api.createChannel({ id: similarId, name: 'E2E National Geographik HD' });
    await page.goto('/tv-channels');
    await page.getByRole('button', { name: 'Auto-match streams', exact: true }).click();
    const matching = page.getByRole('dialog', { name: 'Auto-match streams', exact: true });
    await matching.getByRole('checkbox', { name: 'Include similar names for review' }).check();
    await matching.getByRole('button', { name: 'Find matches', exact: true }).click();
    await matching.getByRole('searchbox', { name: 'Filter matches' }).fill(tv.name);
    const suggestion = matching.getByRole('checkbox', { name: /E2E National Geographik HD/ });
    await expect(suggestion).not.toBeChecked();
    await expect(matching.getByRole('button', { name: 'Assign selected (0)' })).toBeDisabled();
    await suggestion.check();
    await matching.getByRole('button', { name: 'Assign selected (1)' }).click();
    await expect(matching.getByText(/1 streams assigned/)).toBeVisible();
    expect((await api.getChannel(similarId))?.tv_channel_id).toBe(tv.id);
  } finally {
    await api.deleteTvChannel(tv.id);
    await api.deleteChannel(manualId);
    await api.deleteChannel(similarId);
  }
});

test('offline cleanup is previewed before its cadence is saved', async ({ page, api }) => {
  const endpoint = '/api/v1/config/offline-cleanup';
  const original = await api.raw('get', endpoint).then(response => response.json());
  try {
    await page.goto('/settings?tab=automation');
    const form = page.getByRole('form', { name: 'Offline stream cleanup' });
    await form.getByRole('button', { name: 'Preview cleanup' }).click();
    await expect(form.getByText(/qualify now/)).toBeVisible();
    expect(await api.raw('get', endpoint).then(response => response.json())).toEqual(original);
    await form.getByRole('checkbox', { name: 'Automatically remove long-offline AceStreams' }).check();
    await form.getByRole('spinbutton', { name: 'Offline for at least (days)' }).fill('21');
    await form.getByRole('spinbutton', { name: 'Run every (days)' }).fill('10');
    await form.getByRole('button', { name: 'Save cleanup settings' }).click();
    await expect(form.getByText('Offline cleanup settings saved.')).toBeVisible();
    expect(await api.raw('get', endpoint).then(response => response.json())).toMatchObject({ enabled: true, offline_days: 21, interval_days: 10, remove_linked: false });
    await page.reload();
    await expect(form.getByRole('spinbutton', { name: 'Offline for at least (days)' })).toHaveValue('21');
    expect((await api.backgroundTasks()).some(job => job.task_name === 'offline_stream_cleanup')).toBe(true);
  } finally {
    expect((await api.raw('put', endpoint, original)).ok()).toBe(true);
  }
});

import { test, expect } from '../src/fixtures';

test('Live TV schedules a guide programme without starting playback', async ({ page, api, request, scenario }) => {
  const tv = (await api.listTvChannels()).items.find(channel => channel.epg_source_id && channel.epg_id && channel.acestream_channels.some(stream => stream.is_active));
  expect(tv, 'earlier journeys created a mapped TV channel with an enabled stream').toBeTruthy();
  const guide = await api.resolveEpgChannel(tv!.epg_source_id!, tv!.epg_id!);
  expect(guide).toBeTruthy();
  const programme = (await api.epgPrograms(guide!.id)).find(item => Date.parse(item.start_time) > Date.now() + 60_000);
  expect(programme, `future programme in ${scenario.name}`).toBeTruthy();
  const original = await (await request.get('/api/v1/config/recordings')).json();
  let recordingId: string | undefined;
  let playerStarts = 0;
  page.on('request', request => {
    if (request.method() === 'POST' && new URL(request.url()).pathname === '/api/v1/player/sessions') playerStarts++;
  });
  try {
    const enabled = await request.put('/api/v1/config/recordings', { data: { ...original, enabled: true } });
    expect(enabled.ok(), await enabled.text()).toBe(true);
    await page.goto('/live-tv');
    await page.getByRole('button', { name: `TV guide for ${tv!.name}`, exact: true }).click();
    const schedule = page.getByRole('region', { name: `TV guide for ${tv!.name}`, exact: true });
    await expect(schedule.getByRole('tab', { name: 'Tomorrow', exact: true })).toBeVisible();
    const localDay = (date: Date) => date.toLocaleDateString('en-CA', { timeZone: 'Europe/Madrid' });
    if (localDay(new Date(programme!.start_time)) !== localDay(new Date())) {
      await schedule.getByRole('tab', { name: 'Tomorrow', exact: true }).click();
    }
    await schedule.getByRole('button', { name: `Record ${programme!.title}`, exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Schedule recording', exact: true });
    await expect(dialog.getByText(programme!.title, { exact: true })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Adjust recording times' })).toBeVisible();
    const created = page.waitForResponse(response => response.request().method() === 'POST' && new URL(response.url()).pathname === '/api/v1/recordings');
    await dialog.getByRole('button', { name: 'Schedule', exact: true }).click();
    const response = await created;
    expect(response.ok(), await response.text()).toBe(true);
    const saved = await response.json();
    recordingId = saved.id;
    expect(saved.state).toBe('scheduled');
    expect(Date.parse(saved.start_time)).toBe(Date.parse(programme!.start_time));
    expect(Date.parse(saved.end_time)).toBe(Date.parse(programme!.end_time));
    expect(saved.snapshot.title).toBe(programme!.title);
    await expect(dialog).toBeHidden();
    await expect(schedule.getByText('Recording saved. View it in Recordings.')).toBeVisible();
    expect(playerStarts).toBe(0);
    await expect(page.getByLabel(/Video player for/)).toHaveCount(0);
    await page.goto('/recordings');
    const scheduled = page.getByRole('article')
      .filter({ has: page.getByRole('heading', { name: programme!.title, exact: true }) })
      .filter({ has: page.getByText('scheduled', { exact: true }) });
    await expect(scheduled).toBeVisible();
  } finally {
    if (recordingId) {
      expect((await request.post(`/api/v1/recordings/${recordingId}/cancel`)).ok()).toBe(true);
      expect((await request.delete(`/api/v1/recordings/${recordingId}`)).ok()).toBe(true);
    }
    expect((await request.put('/api/v1/config/recordings', { data: original })).ok()).toBe(true);
  }
});

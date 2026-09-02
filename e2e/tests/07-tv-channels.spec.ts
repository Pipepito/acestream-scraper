import { test, expect } from '../src/fixtures';
import { TVChannelsPage, TVChannelDetailPage } from '../src/pages/tv-channels';
import { EPGChannelDetailPage } from '../src/pages/epg';
import { ChannelsPage } from '../src/pages/channels';
import type { AcestreamChannel } from '../src/api';

test.describe.configure({ mode: 'serial' });

test.describe('TV channels', () => {
  let stream: AcestreamChannel;

  test.beforeAll(async ({ request, baseURL }) => {
    const { Api } = await import('../src/api');
    const { loadScenario } = await import('../src/scenario/load');
    const api = new Api(request, baseURL ?? 'http://127.0.0.1:8000');
    const spec = loadScenario().tv.channels[0];
    const results = await api.search(spec.streamSearchQuery);
    const first = results.results.find((r) => r.id);
    if (!first) throw new Error(`engine search "${spec.streamSearchQuery}" returned nothing to attach`);
    stream = await api.createChannel({ id: first.id, name: first.name, group: first.categories[0] });
    const existing = await api.findTvChannel(spec.name);
    if (existing) await api.deleteTvChannel(existing.id);
  });

  test('a TV channel is created from the form', async ({ page, api, scenario }) => {
    const spec = scenario.tv.channels[0];
    const tv = new TVChannelsPage(page);
    await tv.open();
    await tv.add({ name: spec.name, category: spec.category, description: 'Created by the e2e journey' });
    await tv.expectAlert('TV channel created.');
    await expect(tv.row(spec.name)).toBeVisible();
    const created = await api.findTvChannel(spec.name);
    expect(created?.category).toBe(spec.category);
  });

  test('a stream is attached from the detail page', async ({ page, api, scenario }) => {
    const spec = scenario.tv.channels[0];
    const tvChannel = (await api.findTvChannel(spec.name))!;
    const detail = new TVChannelDetailPage(page);
    await detail.open(tvChannel.id, spec.name);
    await detail.addSingle(stream.name, [stream.name]);
    await detail.expectAlert(/Assigned 1 acestream source/);
    await expect(detail.coverage()).toContainText('1 linked acestream');
    await expect(detail.coverage()).toContainText(stream.name);
    const after = await api.getTvChannel(tvChannel.id);
    expect(after.acestream_channels.map((c) => c.id)).toContain(stream.id);
  });

  test('the TV channel is mapped to an EPG channel and its schedule appears', async ({ page, api, scenario }) => {
    const spec = scenario.tv.channels[0];
    const tvChannel = (await api.findTvChannel(spec.name))!;
    const source = (await api.findEpgSource(scenario.epg.sources[0].url))!;
    const epgChannel = (await api.resolveEpgChannel(source.id, spec.epgXmlId!))!;

    const epgDetail = new EPGChannelDetailPage(page);
    await epgDetail.open(epgChannel.id, new RegExp(scenario.epg.targetChannel.displayNameContains));
    await epgDetail.mapToTvChannel(spec.name);
    await epgDetail.expectAlert('Channel mapped successfully');
    const mapped = await api.getTvChannel(tvChannel.id);
    expect(mapped.epg_id).toBe(spec.epgXmlId);
    expect(mapped.epg_source_id).toBe(source.id);

    const detail = new TVChannelDetailPage(page);
    await detail.open(tvChannel.id, spec.name);
    await expect(detail.epgSchedule()).toContainText(/\d+ programs? loaded/, { timeout: 30_000 });
    await expect(detail.epgSchedule().getByRole('table')).toBeVisible();
  });

  test('the curated playlist and XMLTV carry the mapping', async ({ api, scenario }) => {
    const spec = scenario.tv.channels[0];
    const playlist = await api.playlist('/api/v1/playlists/tv-channels/m3u');
    expect(playlist.status).toBe(200);
    expect(playlist.body).toContain('#EXTM3U');
    expect(playlist.body).toContain(spec.name);
    expect(playlist.body).toContain(`tvg-id="${spec.epgXmlId}"`);
    const xml = await api.epgXml({ days_back: '0', days_forward: '2' });
    expect(xml).toContain(`<channel id="${spec.epgXmlId}">`);
    expect(xml).toContain('<programme ');
  });

  test('a stream can be removed and re-attached in batch', async ({ page, api, scenario }) => {
    const spec = scenario.tv.channels[0];
    const tvChannel = (await api.findTvChannel(spec.name))!;
    const detail = new TVChannelDetailPage(page);
    await detail.open(tvChannel.id, spec.name);
    await detail.removeStream(stream.name);
    await detail.expectAlert(/Removed acestream .* successfully/);
    await expect(detail.coverage()).toContainText('0 linked acestream');
    expect((await api.getTvChannel(tvChannel.id)).acestream_channels).toHaveLength(0);

    const dialog = await detail.batchAdd([stream.id]);
    await expect(dialog).toContainText(/Successfully associated 1 acestream/);
    await expect(dialog).toBeHidden({ timeout: 10_000 });
    await expect(detail.coverage()).toContainText('1 linked acestream');
    expect((await api.getTvChannel(tvChannel.id)).acestream_channels.map((c) => c.id)).toContain(stream.id);
  });

  test('favorite, edit and assignment from the channels grid work', async ({ page, api, scenario }) => {
    const spec = scenario.tv.channels[0];
    const tv = new TVChannelsPage(page);
    await tv.open();
    const wasFavorite = (await api.findTvChannel(spec.name))!.is_favorite;
    await tv.favoriteToggle(spec.name).click();
    await tv.expectAlert(wasFavorite ? `Removed ${spec.name} from favorites.` : `Added ${spec.name} to favorites.`);
    await expect.poll(async () => (await api.findTvChannel(spec.name))?.is_favorite).toBe(!wasFavorite);

    const dialog = await tv.openEdit(spec.name);
    await tv.fillForm(dialog, { category: 'Sports E2E' });
    await dialog.getByRole('button', { name: 'Update' }).click();
    await expect(dialog).toBeHidden();
    await tv.expectAlert('TV channel updated.');
    await expect.poll(async () => (await api.findTvChannel(spec.name))?.category).toBe('Sports E2E');

    // Attach a second stream from the Acestream Channels grid.
    const second = (await api.search(spec.streamSearchQuery)).results.filter((r) => r.id && r.id !== stream.id)[0];
    test.skip(!second, 'engine returned a single result');
    const created = await api.createChannel({ id: second.id, name: second.name });
    const tvId = (await api.findTvChannel(spec.name))!.id;
    await api.raw('delete', `/api/v1/tv-channels/${tvId}/acestreams/${created.id}`); // re-runnable: start unassigned
    const channels = new ChannelsPage(page);
    await channels.open();
    await channels.filterByName(created.name);
    const assign = await channels.openAssignTv(created.name);
    await channels.selectOption(assign.getByRole('combobox', { name: /^TV Channel/ }), spec.name);
    await assign.getByRole('button', { name: 'Assign' }).click();
    await expect(assign).toBeHidden();
    await expect.poll(async () => (await api.getChannel(created.id))?.tv_channel_id, { timeout: 15_000 }).toBe(tvId);
    // The grid marks linked streams with the TV shortcut/favorite actions rather than a name column.
    await expect(channels.row(created.name).first().getByRole('button', { name: `go to tv channel ${spec.name}` })).toBeVisible();
  });
});

/** @jest-environment node */
import { createServer, type Server } from 'node:http';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import apiClient from '../services/apiClient';
import { acestreamChannelService } from '../services/channelService';
import { recordingService } from '../services/recordingService';
import { tvChannelService } from '../services/tvChannelService';
import { setupService } from '../services/setupService';
import { telegramService } from '../services/telegramService';
import { configService } from '../services/configService';
import { scraperService } from '../services/scraperService';
import { epgService } from '../services/epgService';
import { mediaServerService } from '../services/mediaServerService';
import { tunerService } from '../services/tunerService';
import { eventService } from '../services/eventService';

interface Exchange { method: string; url: string; headers: Record<string, string | string[] | undefined>; body: string }
const exchanges: Exchange[] = [];
let server: Server;
const originalBase = apiClient.defaults.baseURL;
beforeAll(async () => {
  server = createServer(async (request, response) => {
    const body: Buffer[] = [];
    for await (const chunk of request) body.push(Buffer.from(chunk));
    exchanges.push({ method: request.method!, url: `http://contract.test${request.url}`, headers: request.headers, body: Buffer.concat(body).toString() });
    response.setHeader('Content-Type', 'application/json');
    response.end('{}');
  });
  await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Missing fixture port');
  apiClient.defaults.baseURL = `http://127.0.0.1:${address.port}/api`;
});
afterAll(async () => { apiClient.defaults.baseURL = originalBase; await new Promise<void>((resolve, reject) => server.close(error => error ? reject(error) : resolve())); });

it('validates production serializers after transport, including false, empty, zero and omitted values', async () => {
  await acestreamChannelService.bulkEditAcestreamChannels(['one', 'two'], { group: '', is_active: false });
  await acestreamChannelService.bulkActivateAcestreamChannels(['one', 'two'], false);
  await recordingService.list(undefined, 0, '');
  await recordingService.create({ tv_channel_id: 1, mode: 'schedule', timezone: 'Europe/Madrid',
    start_time: '2030-01-01T12:00:00Z', end_time: '2030-01-01T13:00:00Z', idempotency_key: 'a4450d44-2ceb-4339-a095-464b992136ea' });
  await recordingService.edit('fixture', { expected_revision: 1, end_time: '2030-01-01T13:30:00Z' });
  await tvChannelService.nowNext();
  await setupService.save({ expected_revision: 'a'.repeat(64), runtime: {}, setup_complete: false });
  expect(JSON.parse(exchanges[0].body)).toEqual({ acestreamchannel_ids: ['one', 'two'], fields: { group: '', is_active: false } });
  expect(exchanges[2].url).toContain('offset=0');
  expect(exchanges[2].url).not.toContain('state=');
  for (const collection of ['library', 'upcoming', 'history'] as const) await recordingService.list(undefined, 50, 'Evening', collection);
  expect(exchanges[7].url).toContain('collection=library');
  await tvChannelService.browse({ skip: 0, limit: 50, is_active: false, min_streams: 0, search: '100%_News', sort: 'channel_number', direction: 'desc' });
  await tvChannelService.inventory();
  await tvChannelService.nowNext([1, 2]);
  expect(exchanges[12].url).toContain('channel_ids=1&channel_ids=2');
  const result = execFileSync(path.resolve('../backend/venv/bin/python'), [path.resolve('../backend/scripts/validate_api_contracts.py')], { input: JSON.stringify(exchanges), encoding: 'utf8' });
  expect(result).toContain('Validated 13 actual consumer requests');
});

it('validates canonical source, guide and integration serializers with scoped credentials and independent saves', async () => {
  const begin = exchanges.length;
  await scraperService.getProviders();
  await scraperService.getURLs({ enabled: false, search: 'Original 100% name', page: 1, page_size: 50 });
  await scraperService.createURL({ name: '', url: 'https://fixture.test/channels.m3u', url_type: 'auto', enabled: false, scrape_bare_ids: false, extraction_recipe: null });
  await scraperService.updateURL(7, { name: null, extraction_recipe: null, enabled: true });
  await scraperService.deleteURL(7, false);
  await epgService.createSource({ name: 'Original guía', url: 'https://fixture.test/guide.xml', enabled: false });
  await epgService.updateSource(8, { enabled: true });
  await epgService.getChannels(8, 0, 50);
  await configService.updatePlaybackRouting({ use_acexy: false, acexy_url: '' });
  await configService.updateNotificationWebhookUrl('');
  await tunerService.updateSettings({ tuner_count: 1, max_channels: 100, only_online: false, hide_unusable: false });
  await mediaServerService.create({ kind: 'jellyfin', name: 'Home', base_url: 'http://192.168.1.20:8096', api_key: null, enabled: false });
  await mediaServerService.update(9, { api_key: '' });
  await eventService.updateSource('source-fixture', 1, false);
  await eventService.mapBroadcast('event-fixture', 1, 'broadcast-fixture', null, false);
  const telegram = telegramService('synthetic-scoped-admin');
  await telegram.status();
  await telegram.login(12345, 'a'.repeat(32), '+123456789');
  const source = { name: 'Original chat', chat_id: '-100123', enabled: false, topic_id: null, sender_ids: [],
    include: '', exclude: '', bare_ids: false, recipe: null, history_count: 0, history_since: null };
  await telegram.preview(source);
  await telegram.save(source);
  await telegram.save({ ...source, message_code: 'TELEGRAM_CHAT_LOST' } as typeof source, 10);
  const captured = exchanges.slice(begin);
  expect(captured).toHaveLength(20);
  expect(captured.slice(0, 15).every(exchange => exchange.headers['x-telegram-admin'] === undefined)).toBe(true);
  expect(captured.slice(15).every(exchange => exchange.headers['x-telegram-admin'] === 'synthetic-scoped-admin')).toBe(true);
  expect(JSON.parse(captured[19].body)).not.toHaveProperty('message_code');
  expect(JSON.parse(captured[19].body)).not.toHaveProperty('history_count');
  expect(captured.filter(exchange => exchange.body).every(exchange => String(exchange.headers['content-type']).startsWith('application/json'))).toBe(true);
  const result = execFileSync(path.resolve('../backend/venv/bin/python'), [path.resolve('../backend/scripts/validate_api_contracts.py')], {
    input: JSON.stringify(captured), encoding: 'utf8',
  });
  expect(result).toContain('Validated 20 actual consumer requests');
});

it('projects saved-search writes while retaining the reviewed revision and false/empty fields', async () => {
  const { savedSearchService } = await import('../services/savedSearchService');
  const start = exchanges.length;
  const row = { id: 7, revision: 3, name: 'Original name', query: 'Sports', category: '', refresh_enabled: false, created_at: '2030-01-01T00:00:00Z', updated_at: '2030-01-01T00:00:00Z' };
  await savedSearchService.save(row);
  await savedSearchService.save(row, row);
  expect(JSON.parse(exchanges[start].body)).toEqual({ name: row.name, query: row.query, category: '', refresh_enabled: false });
  expect(JSON.parse(exchanges[start + 1].body)).toEqual({ name: row.name, query: row.query, category: '', refresh_enabled: false, expected_revision: 3 });
  const result = execFileSync(path.resolve('../backend/venv/bin/python'), [path.resolve('../backend/scripts/validate_api_contracts.py')], { input: JSON.stringify(exchanges.slice(start)), encoding: 'utf8' });
  expect(result).toContain('Validated 2 actual consumer requests');
});

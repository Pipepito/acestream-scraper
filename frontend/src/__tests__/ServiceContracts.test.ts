/** @jest-environment node */
import { createServer, type Server } from 'node:http';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import apiClient from '../services/apiClient';
import { acestreamChannelService } from '../services/channelService';
import { recordingService } from '../services/recordingService';
import { tvChannelService } from '../services/tvChannelService';
import { setupService } from '../services/setupService';

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
  const result = execFileSync(path.resolve('../backend/venv/bin/python'), [path.resolve('../backend/scripts/validate_api_contracts.py')], { input: JSON.stringify(exchanges), encoding: 'utf8' });
  expect(result).toContain('Validated 7 actual consumer requests');
});

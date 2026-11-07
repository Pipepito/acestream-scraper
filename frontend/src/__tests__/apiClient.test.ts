import type { AxiosAdapter } from 'axios';
import apiClient from '../services/apiClient';

const response = (data: unknown, contentType = 'application/json', status = 200): AxiosAdapter => async config => ({
  data, status, statusText: 'OK', headers: { 'content-type': contentType }, config,
});

it('rejects Firefox navigation completions with status zero and no response headers', async () => {
  await expect(apiClient.get('/fixture', { adapter: response('', '', 0) })).rejects.toMatchObject({ code: 'API_CONNECTION_INTERRUPTED', canRetry: true });
});

it('retains JSON parsing, including valid empty strings and null', async () => {
  for (const [body, expected] of [['{"streams":[]}', { streams: [] }], ['""', ''], ['null', null]] as const) {
    expect((await apiClient.get('/fixture', { adapter: response(body) })).data).toEqual(expected);
  }
});

it('preserves empty no-content responses, HEAD responses and non-JSON downloads', async () => {
  expect((await apiClient.delete('/fixture', { adapter: response('', 'application/json', 204) })).status).toBe(204);
  expect((await apiClient.head('/fixture', { adapter: response('') })).status).toBe(200);
  expect((await apiClient.get('/fixture', { adapter: response('plain text', 'text/plain') })).data).toBe('plain text');
  const blob = new Blob(['data']);
  expect((await apiClient.get('/fixture', { responseType: 'blob', adapter: response(blob) })).data).toBe(blob);
});

import apiClient from '../services/apiClient';
import { systemService } from '../services/systemService';

jest.mock('../services/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() } }));

describe('systemService.getPublicUrl', () => {
  it('reads /v1/system/public-url', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: { url: 'http://x', source: 'request', warnings: ['unset'] } });
    await expect(systemService.getPublicUrl()).resolves.toEqual({ url: 'http://x', source: 'request', warnings: ['unset'] });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/system/public-url');
  });
});

it.each(['start', 'stop'] as const)('sends engine %s to the lifecycle endpoint', async (action) => {
  const result = { name: 'acestream', success: true, message: 'Requested.' };
  (apiClient.post as jest.Mock).mockResolvedValue({ data: result });
  await expect(systemService.controlEngine(action)).resolves.toEqual(result);
  expect(apiClient.post).toHaveBeenCalledWith(`/v1/system/services/acestream/${action}`);
});


it('controls the checking engine independently', async () => {
  const result = { name: 'acestream-check', success: true, message: 'Stopped' };
  jest.spyOn(apiClient, 'post').mockResolvedValueOnce({ data: result });
  await expect(systemService.controlEngine('stop', 'acestream-check')).resolves.toEqual(result);
  expect(apiClient.post).toHaveBeenLastCalledWith('/v1/system/services/acestream-check/stop');
});

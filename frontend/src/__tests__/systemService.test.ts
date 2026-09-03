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

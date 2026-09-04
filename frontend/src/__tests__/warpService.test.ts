import apiClient from '../services/apiClient';
import { connectWarp, disconnectWarp, getWarpStatus, registerWarpLicense, setWarpMode } from '../services/warpService';
import { WarpMode } from '../types/warpTypes';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockedClient = apiClient as unknown as { get: jest.Mock; post: jest.Mock };

describe('warpService', () => {
  beforeEach(() => {
    mockedClient.get.mockReset();
    mockedClient.post.mockReset();
    mockedClient.get.mockResolvedValue({ data: { running: false, connected: false } });
    mockedClient.post.mockResolvedValue({ data: { success: true } });
  });

  it('requests WARP status relative to the client base URL (no duplicated /api prefix)', async () => {
    await getWarpStatus();
    expect(mockedClient.get).toHaveBeenCalledWith('/v1/warp/status');
  });

  it('posts connect, disconnect and mode changes to /v1/warp/*', async () => {
    await connectWarp();
    await disconnectWarp();
    await setWarpMode(WarpMode.WARP);
    expect(mockedClient.post).toHaveBeenNthCalledWith(1, '/v1/warp/connect');
    expect(mockedClient.post).toHaveBeenNthCalledWith(2, '/v1/warp/disconnect');
    expect(mockedClient.post).toHaveBeenNthCalledWith(3, '/v1/warp/mode', { mode: 'warp' });
  });

  it('registers a license with the license_key field the backend schema declares', async () => {
    await registerWarpLicense('abcd-efgh-ijkl');
    expect(mockedClient.post).toHaveBeenCalledWith('/v1/warp/license', { license_key: 'abcd-efgh-ijkl' });
  });
});

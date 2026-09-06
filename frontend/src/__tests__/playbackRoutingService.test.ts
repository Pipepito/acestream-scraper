import apiClient from '../services/apiClient';
import { configService } from '../services/configService';
jest.mock('../services/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), put: jest.fn() } }));
it('reads and saves typed playback routing', async () => {
  const data = { use_acexy: true, acexy_url: 'http://proxy:8080' };
  (apiClient.get as jest.Mock).mockResolvedValue({ data });
  (apiClient.put as jest.Mock).mockResolvedValue({ data });
  expect(await configService.getPlaybackRouting()).toEqual(data);
  expect(await configService.updatePlaybackRouting(data)).toEqual(data);
  expect(apiClient.get).toHaveBeenCalledWith('/v1/config/playback-routing');
  expect(apiClient.put).toHaveBeenCalledWith('/v1/config/playback-routing', data);
});

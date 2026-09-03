import apiClient from '../services/apiClient';
import { playerService } from '../services/playerService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), delete: jest.fn() },
}));

describe('playerService', () => {
  beforeEach(() => jest.clearAllMocks());

  it('starts a session', async () => {
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { id: 's1', state: 'starting' } });
    await expect(playerService.startSession('a'.repeat(40))).resolves.toEqual({ id: 's1', state: 'starting' });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/player/sessions', { content_id: 'a'.repeat(40) });
  });

  it('reads status and capabilities', async () => {
    (apiClient.get as jest.Mock).mockResolvedValueOnce({ data: { id: 's1' } }).mockResolvedValueOnce({ data: { ffmpeg_available: true } });
    await playerService.getSession('s1');
    await playerService.getCapabilities();
    expect(apiClient.get).toHaveBeenNthCalledWith(1, '/v1/player/sessions/s1');
    expect(apiClient.get).toHaveBeenNthCalledWith(2, '/v1/player/capabilities');
  });

  it('leaves with a keepalive DELETE that carries the token', async () => {
    const fetchMock = jest.fn().mockResolvedValue({ ok: true });
    (global as unknown as { fetch: jest.Mock }).fetch = fetchMock;
    window.localStorage.setItem('apiToken', 't k');
    playerService.leaveSession('s1');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/player/sessions/s1?token=t+k', { method: 'DELETE', keepalive: true });
    window.localStorage.removeItem('apiToken');
  });
});

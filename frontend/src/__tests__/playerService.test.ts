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

  it('swallows a failed release instead of leaving an unhandled rejection', async () => {
    // try/catch around `void fetch(...)` cannot catch an async rejection: a
    // stopped backend or a closed tab would surface the fire-and-forget DELETE
    // as an unhandled promise rejection.
    const rejection = Promise.reject(new Error('offline'));
    const attach = jest.spyOn(rejection, 'catch');
    (global as unknown as { fetch: jest.Mock }).fetch = jest.fn().mockReturnValue(rejection);

    expect(() => playerService.leaveSession('s1')).not.toThrow();
    const handled = attach.mock.calls.length > 0;
    rejection.catch(() => undefined); // never leave it unhandled, even on a failing run
    expect(handled).toBe(true);
  });
});

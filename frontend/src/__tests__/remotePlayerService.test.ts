import apiClient from '../services/apiClient';
import { remotePlayerService } from '../services/remotePlayerService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), patch: jest.fn(), delete: jest.fn() },
}));

describe('remotePlayerService', () => {
  beforeEach(() => jest.clearAllMocks());

  it('uses /v1/remote-players paths', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { id: 1 } });
    (apiClient.patch as jest.Mock).mockResolvedValue({ data: { id: 1 } });
    (apiClient.delete as jest.Mock).mockResolvedValue({});
    await remotePlayerService.list();
    await remotePlayerService.create({ name: 'a', kind: 'vlc', host: 'h', port: 8080 });
    await remotePlayerService.update(1, { name: 'b' });
    await remotePlayerService.remove(1);
    await remotePlayerService.test({ kind: 'vlc', host: 'h', port: 8080 });
    await remotePlayerService.status(1);
    await remotePlayerService.play(1, 'a'.repeat(40), 'Arena');
    await remotePlayerService.command(1, 'volume', 50);
    await remotePlayerService.scan({ cidr: '192.168.1.0/24' });
    await remotePlayerService.scanDefault();
    expect(apiClient.get).toHaveBeenCalledWith('/v1/remote-players');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players', { name: 'a', kind: 'vlc', host: 'h', port: 8080 });
    expect(apiClient.patch).toHaveBeenCalledWith('/v1/remote-players/1', { name: 'b' });
    expect(apiClient.delete).toHaveBeenCalledWith('/v1/remote-players/1');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/test', { kind: 'vlc', host: 'h', port: 8080 });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/remote-players/1/status');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/1/play', { content_id: 'a'.repeat(40), title: 'Arena' });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/1/command', { command: 'volume', value: 50 });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/remote-players/scan', { cidr: '192.168.1.0/24' });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/remote-players/scan/default');
  });
});

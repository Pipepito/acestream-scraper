import apiClient from '../services/apiClient';
import { mediaServerService } from '../services/mediaServerService';
import { tunerService } from '../services/tunerService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), patch: jest.fn(), put: jest.fn(), delete: jest.fn() },
}));

describe('mediaServerService', () => {
  beforeEach(() => jest.clearAllMocks());

  it('uses /v1/media-servers paths', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: [] });
    (apiClient.post as jest.Mock).mockResolvedValue({ data: { id: 1 } });
    (apiClient.patch as jest.Mock).mockResolvedValue({ data: { id: 1 } });
    (apiClient.delete as jest.Mock).mockResolvedValue({});
    await mediaServerService.list();
    await mediaServerService.create({ kind: 'jellyfin', name: 'Jelly', base_url: 'http://192.168.1.12:8096' });
    await mediaServerService.update(1, { name: 'Jelly 2' });
    await mediaServerService.remove(1);
    await mediaServerService.test({ kind: 'jellyfin', base_url: 'http://192.168.1.12:8096', api_key: 'k' });
    await mediaServerService.connect(1);
    await mediaServerService.refresh(1);
    await mediaServerService.disconnect(1);
    await mediaServerService.status(1);
    expect(apiClient.get).toHaveBeenCalledWith('/v1/media-servers');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/media-servers', {
      kind: 'jellyfin',
      name: 'Jelly',
      base_url: 'http://192.168.1.12:8096',
    });
    expect(apiClient.patch).toHaveBeenCalledWith('/v1/media-servers/1', { name: 'Jelly 2' });
    expect(apiClient.delete).toHaveBeenCalledWith('/v1/media-servers/1');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/media-servers/test', {
      kind: 'jellyfin',
      base_url: 'http://192.168.1.12:8096',
      api_key: 'k',
    });
    expect(apiClient.post).toHaveBeenCalledWith('/v1/media-servers/1/connect');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/media-servers/1/refresh');
    expect(apiClient.post).toHaveBeenCalledWith('/v1/media-servers/1/disconnect');
    expect(apiClient.get).toHaveBeenCalledWith('/v1/media-servers/1/status');
  });
});

describe('tunerService', () => {
  beforeEach(() => jest.clearAllMocks());

  it('uses /v1/tuner paths', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: {} });
    (apiClient.put as jest.Mock).mockResolvedValue({ data: {} });
    await tunerService.getStatus();
    await tunerService.getSettings();
    await tunerService.updateSettings({ friendly_name: 'AceStream Tuner', max_channels: 450 });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/tuner/status');
    expect(apiClient.get).toHaveBeenCalledWith('/v1/tuner/settings');
    expect(apiClient.put).toHaveBeenCalledWith('/v1/tuner/settings', { friendly_name: 'AceStream Tuner', max_channels: 450 });
  });
});

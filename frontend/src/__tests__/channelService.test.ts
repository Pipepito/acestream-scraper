import apiClient from '../services/apiClient';
import { acestreamChannelService, AcestreamChannel } from '../services/channelService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;
const channel: AcestreamChannel = {
  id: `deadbeef${'1'.repeat(32)}`,
  name: 'Alpha',
  last_seen: '2026-10-20T10:00:00Z',
  status: 'active',
  is_online: null,
  epg_update_protected: false,
};

describe('acestreamChannelService canonical collection URLs', () => {
  beforeEach(() => jest.clearAllMocks());

  it('lists channels without relying on a redirect and preserves ID search filters', async () => {
    const payload = { items: [channel], total: 1 };
    mockedApiClient.get.mockResolvedValue({ data: payload });
    const filters = {
      search: channel.id,
      group: 'Sports',
      is_active: false,
      is_online: false,
      assigned: false,
      page: 2,
      page_size: 10,
    };

    const result = await acestreamChannelService.getAcestreamChannels(filters);

    expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/acestream-channels/', {
      params: { ...filters, active_only: false },
    });
    expect(result).toEqual(payload);
  });

  it('creates channels without relying on a POST redirect', async () => {
    mockedApiClient.post.mockResolvedValue({ data: channel });
    const input = { id: channel.id, name: channel.name };

    const result = await acestreamChannelService.createAcestreamChannel(input);

    expect(mockedApiClient.post).toHaveBeenCalledWith('/v1/acestream-channels/', input);
    expect(result).toEqual(channel);
  });
});

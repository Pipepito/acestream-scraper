import apiClient from '../services/apiClient';
import { baseUrlService, StreamBaseUrl } from '../services/baseUrlService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockedApiClient = apiClient as jest.Mocked<typeof apiClient>;

const sampleEntry: StreamBaseUrl = {
  id: 1,
  name: 'Ace player',
  pattern: 'acestream://',
  is_default: true,
};

describe('baseUrlService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('lists named base URLs from /v1/base-urls', async () => {
    mockedApiClient.get.mockResolvedValue({ data: [sampleEntry] });

    const result = await baseUrlService.getBaseUrls();

    expect(mockedApiClient.get).toHaveBeenCalledWith('/v1/base-urls');
    expect(result).toEqual([sampleEntry]);
  });

  it('creates a named base URL with name, pattern, and default flag', async () => {
    mockedApiClient.post.mockResolvedValue({ data: sampleEntry });

    const result = await baseUrlService.createBaseUrl({
      name: 'Ace player',
      pattern: 'acestream://',
      is_default: true,
    });

    expect(mockedApiClient.post).toHaveBeenCalledWith('/v1/base-urls', {
      name: 'Ace player',
      pattern: 'acestream://',
      is_default: true,
    });
    expect(result).toEqual(sampleEntry);
  });

  it('patches a named base URL by id', async () => {
    const updated = { ...sampleEntry, is_default: false };
    mockedApiClient.patch.mockResolvedValue({ data: updated });

    const result = await baseUrlService.updateBaseUrl(1, { is_default: false });

    expect(mockedApiClient.patch).toHaveBeenCalledWith('/v1/base-urls/1', { is_default: false });
    expect(result).toEqual(updated);
  });

  it('deletes a named base URL by id', async () => {
    mockedApiClient.delete.mockResolvedValue({ data: undefined });

    await baseUrlService.deleteBaseUrl(4);

    expect(mockedApiClient.delete).toHaveBeenCalledWith('/v1/base-urls/4');
  });
});

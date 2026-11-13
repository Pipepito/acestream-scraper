import apiClient from '../services/apiClient';
import { configService } from '../services/configService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), put: jest.fn() },
}));

const mockedClient = apiClient as unknown as { get: jest.Mock; put: jest.Mock };

describe('configService stream check timeout', () => {
  beforeEach(() => {
    mockedClient.get.mockReset();
    mockedClient.put.mockReset();
  });

  it('reads the saved timeout as a number of seconds', async () => {
    // Settings are stored as text; the form compares the value with a number.
    mockedClient.get.mockResolvedValue({ data: { key: 'acestream_check_timeout', value: '25' } });
    await expect(configService.getAcestreamCheckTimeout()).resolves.toBe(25);
    expect(mockedClient.get).toHaveBeenCalledWith('/v1/config/acestream_check_timeout');
  });

  it('saves the timeout as the text value the settings API expects', async () => {
    mockedClient.put.mockResolvedValue({ data: {} });
    await configService.updateAcestreamCheckTimeout(30);
    expect(mockedClient.put).toHaveBeenCalledWith('/v1/config/acestream_check_timeout', { value: '30' });
  });
});

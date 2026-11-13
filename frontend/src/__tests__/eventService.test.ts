import apiClient from '../services/apiClient';
import { eventService } from '../services/eventService';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), put: jest.fn(), patch: jest.fn(), delete: jest.fn() },
}));

const mockedClient = apiClient as unknown as { post: jest.Mock };

describe('eventService.apply', () => {
  beforeEach(() => {
    mockedClient.post.mockReset();
    mockedClient.post.mockResolvedValue({ data: [] });
  });

  it('keeps a one-off import reviewed-only unless refresh and automatic import are asked for', async () => {
    await eventService.apply('review', ['a']);
    expect(mockedClient.post).toHaveBeenCalledWith('/v1/events/apply', {
      token: 'review', selected_ids: ['a'], refresh_source: false, import_new: false,
    });
  });

  it('sends the saved source choices with the reviewed selection', async () => {
    const saved = [{ id: 'a' }];
    mockedClient.post.mockResolvedValue({ data: saved });
    await expect(eventService.apply('review', [], true, true)).resolves.toBe(saved);
    expect(mockedClient.post).toHaveBeenCalledWith('/v1/events/apply', {
      token: 'review', selected_ids: [], refresh_source: true, import_new: true,
    });
  });
});

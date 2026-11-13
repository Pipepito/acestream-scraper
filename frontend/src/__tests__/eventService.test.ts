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

describe('eventService.providerInterests', () => {
  beforeEach(() => mockedClient.post.mockReset());

  it('asks the server for the names a provider publishes and waits for its upstream fetch', async () => {
    const names = { sports: ['Football'], competitions: ['COPA'], teams: [] };
    mockedClient.post.mockResolvedValue({ data: names });
    const input = { provider_options: { provider: 'marca_es' as const, window_days: 7 }, timezone: 'Europe/Madrid' };
    await expect(eventService.providerInterests(input)).resolves.toBe(names);
    // The server allows the provider 15 s by default: the browser must not give up first.
    expect(mockedClient.post).toHaveBeenCalledWith('/v1/events/providers/interests', input, { timeout: 45000 });
    await eventService.providerInterests({ ...input, timeout_seconds: 60 });
    expect(mockedClient.post).toHaveBeenLastCalledWith('/v1/events/providers/interests', { ...input, timeout_seconds: 60 }, { timeout: 90000 });
  });
});

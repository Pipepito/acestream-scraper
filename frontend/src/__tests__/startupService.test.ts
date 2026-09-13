import apiClient from '../services/apiClient';
import { startupService } from '../services/startupService';

jest.mock('../services/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() } }));
const get = apiClient.get as jest.Mock;
const post = apiClient.post as jest.Mock;

beforeEach(() => jest.resetAllMocks());

it('uses the versioned startup API under the shared /api base', async () => {
  const snapshot = { status: 'starting', phase: 'Preparing', events: [], recovery_token: 'nonce' };
  get.mockResolvedValue({ data: snapshot });
  expect(await startupService.status()).toEqual(snapshot);
  expect(get).toHaveBeenCalledWith('/v1/startup', { timeout: 10000 });
  post.mockResolvedValue({ data: snapshot });
  await startupService.recover('salvage', 'nonce');
  expect(post).toHaveBeenCalledWith('/v1/startup/recover', {
    action: 'salvage', recovery_token: 'nonce', confirm: true,
  }, { timeout: 10000 });
});

it('rejects an HTML fallback instead of passing it to the startup screen', async () => {
  get.mockResolvedValue({ data: '<html>gateway fallback</html>' });
  await expect(startupService.status()).rejects.toThrow('Invalid startup response');
});

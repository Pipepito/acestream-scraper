import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import UpdateAvailableNotice from '../components/UpdateAvailableNotice';
import { systemService } from '../services/systemService';

jest.mock('../services/systemService', () => ({ systemService: { getUpdates: jest.fn() } }));
const fetch = jest.mocked(systemService.getUpdates);
let version = 0;
const setup = (deployment: 'docker' | 'native' = 'docker', available = true) => {
  const tag = `v9.0.${++version}`;
  fetch.mockResolvedValue({ current_version: 'v2.2.0', latest_version: tag,
    update_available: available, deployment, status: 'checked', release_url: null });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = render(<QueryClientProvider client={client}><UpdateAvailableNotice /></QueryClientProvider>);
  return { ...view, tag, client };
};
afterEach(() => { jest.restoreAllMocks(); localStorage.clear(); });

it.each(['docker', 'native'] as const)('gives manual %s instructions and shows once per release', async deployment => {
  const { tag, unmount, client } = setup(deployment);
  expect(await screen.findByText(`${tag} is available`)).toBeVisible();
  expect(screen.getByText(deployment === 'docker' ? /pull the new Docker image/ : /download the latest release/)).toBeVisible();
  expect(screen.getByText(/The app does not update itself/)).toBeVisible();
  expect(localStorage.getItem('acestream.published-update.seen.v1')).toBe(tag);
  await userEvent.setup().click(screen.getByRole('button', { name: 'Dismiss new version notice' }));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  unmount();
  render(<QueryClientProvider client={client}><UpdateAvailableNotice /></QueryClientProvider>);
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('stays quiet for an equal or older release', async () => {
  setup('native', false);
  await waitFor(() => expect(fetch).toHaveBeenCalled());
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('remembers an announcement when browser storage is denied', async () => {
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('denied'); });
  const { tag, client, unmount } = setup();
  expect(await screen.findByText(`${tag} is available`)).toBeVisible();
  unmount();
  render(<QueryClientProvider client={client}><UpdateAvailableNotice /></QueryClientProvider>);
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('stays quiet when checking fails', async () => {
  fetch.mockRejectedValue(new Error('offline'));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><UpdateAvailableNotice /></QueryClientProvider>);
  await waitFor(() => expect(client.getQueryState(['published-release'])?.status).toBe('error'));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

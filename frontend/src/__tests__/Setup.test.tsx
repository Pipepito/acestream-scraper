import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import Setup from '../pages/Setup';
import SetupNotice from '../components/SetupNotice';
import { setupService, type SetupState } from '../services/setupService';

jest.mock('../services/setupService', () => ({ setupQueryKey: ['installation-setup'], setupService: { get: jest.fn(), save: jest.fn() } }));
const service = jest.mocked(setupService);
const initial: SetupState = {
  version: 1, setup_complete: false, revision: 'a'.repeat(64), restart_required: false, api_protected: false,
  runtime: { PLAYER_MAX_SESSIONS: 3, ENABLE_IPFS: false }, unavailable: { ENABLE_IPFS: 'Not included in this image' },
  options: [
    { name: 'PLAYER_MAX_SESSIONS', label: 'Maximum browser sessions', default: 3, kind: 'integer', group: 'playback', help: '', minimum: 1, maximum: 100 },
    { name: 'ENABLE_IPFS', label: 'IPFS', default: false, kind: 'boolean', group: 'services', help: '' },
  ],
};
function renderSetup(node: React.ReactNode, mode: 'light' | 'dark' = 'light') {
  return render(<ThemeProvider theme={createAppTheme(mode)}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><TestMemoryRouter>{node}</TestMemoryRouter></QueryClientProvider></ThemeProvider>);
}
beforeEach(() => { jest.resetAllMocks(); service.get.mockResolvedValue(initial); });

it.each(['light', 'dark'] as const)('reviews and saves a draft with restart guidance in %s mode', async mode => {
  service.save.mockResolvedValue({ ...initial, runtime: { ...initial.runtime, PLAYER_MAX_SESSIONS: 5 }, setup_complete: true, restart_required: true });
  renderSetup(<Setup />, mode);
  fireEvent.change(await screen.findByRole('spinbutton', { name: 'Maximum browser sessions' }), { target: { value: '5' } });
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByText(/No API token is configured/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByRole('checkbox', { name: 'IPFS' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByText('Maximum browser sessions: 5')).toBeInTheDocument();
  expect(service.save).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Save setup' }));
  await screen.findByText(/Setup saved. Restart the container/);
  expect(service.save.mock.calls[0][0]).toEqual({ expected_revision: initial.revision, runtime: { ...initial.runtime, PLAYER_MAX_SESSIONS: 5 }, setup_complete: true });
  expect(screen.getByRole('link', { name: 'Add an official broadcaster' })).toHaveAttribute('href', '/scraper');
});

it('keeps the draft after a failed save', async () => {
  service.save.mockRejectedValue(new Error('write failed'));
  renderSetup(<Setup />);
  fireEvent.change(await screen.findByRole('spinbutton', { name: 'Maximum browser sessions' }), { target: { value: '6' } });
  for (let index = 0; index < 3; index++) fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save setup' }));
  await screen.findByRole('button', { name: 'Reload saved configuration' });
  expect(screen.getByText('Maximum browser sessions: 6')).toBeInTheDocument();
  expect(screen.queryByText('Build your catalogue')).not.toBeInTheDocument();
});

it('offers first-run setup without blocking navigation', async () => {
  renderSetup(<SetupNotice />);
  expect(await screen.findByRole('link', { name: 'Set up scraper' })).toHaveAttribute('href', '/setup');
  expect(service.save).not.toHaveBeenCalled();
});

it('does not show first-run setup again for an existing installation', async () => {
  service.get.mockResolvedValue({ ...initial, setup_complete: true });
  renderSetup(<SetupNotice />);
  await waitFor(() => expect(service.get).toHaveBeenCalled());
  expect(screen.queryByRole('link', { name: 'Set up scraper' })).not.toBeInTheDocument();
});

it('offers retry when loading fails', async () => {
  service.get.mockRejectedValue(new Error('offline'));
  renderSetup(<Setup />);
  await screen.findByText('Setup could not be loaded.');
  service.get.mockResolvedValue(initial);
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  await screen.findByRole('spinbutton', { name: 'Maximum browser sessions' });
});

import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import NetworkSettings from '../components/settings/NetworkSettings';
import { TestMemoryRouter } from '../testUtils/router';
import { createAppTheme } from '../theme';
import { setupQueryKey, setupService, type SetupState } from '../services/setupService';
import { ApiError } from '../services/apiErrors';

jest.mock('../services/setupService', () => ({ setupQueryKey: ['installation-setup'], setupService: { get: jest.fn(), save: jest.fn() } }));
const service = jest.mocked(setupService);
const initial: SetupState = {
  version: 1, setup_complete: false, revision: 'a'.repeat(64), restart_required: false, api_protected: false,
  runtime: { FORWARDED_ALLOW_IPS: '127.0.0.1,192.168.0.0/16', ALLOW_PRIVATE_SOURCE_URLS: true, PLAYER_MAX_SESSIONS: 7 }, unavailable: {},
  options: [
    { name: 'FORWARDED_ALLOW_IPS', label: 'Trusted reverse proxies', default: '127.0.0.1', kind: 'networks', group: 'network', help: 'Use only actual proxy addresses.' },
    { name: 'ALLOW_PRIVATE_SOURCE_URLS', label: 'Allow sources on private networks', default: true, kind: 'boolean', group: 'network', help: '' },
    { name: 'PLAYER_MAX_SESSIONS', label: 'Maximum browser sessions', default: 3, kind: 'integer', group: 'playback', help: '' },
  ],
};
function renderPage(mode: 'light' | 'dark' = 'light') {
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(<ThemeProvider theme={createAppTheme(mode)}><QueryClientProvider client={cache}><TestMemoryRouter><NetworkSettings /></TestMemoryRouter></QueryClientProvider></ThemeProvider>);
  return { cache };
}
beforeEach(() => { jest.resetAllMocks(); service.get.mockResolvedValue(initial); });

it.each(['light', 'dark'] as const)('edits only network options outside setup and explains restart in %s mode', async mode => {
  service.save.mockResolvedValue({ ...initial, revision: 'b'.repeat(64), runtime: { ...initial.runtime, FORWARDED_ALLOW_IPS: '127.0.0.1,172.17.0.16' }, restart_required: true });
  renderPage(mode);
  const input = await screen.findByRole('textbox', { name: 'Trusted reverse proxies' });
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument();
  expect(screen.getByText(/adding a narrower range does not remove/)).toBeVisible();
  expect(screen.getByRole('button', { name: 'Save network settings' })).toBeDisabled();
  fireEvent.change(input, { target: { value: '127.0.0.1,172.17.0.16' } });
  expect(screen.queryByText(/adding a narrower range does not remove/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Save network settings' }));
  expect(await screen.findByText('Network settings saved.')).toBeVisible();
  expect(service.save).toHaveBeenCalledWith({ expected_revision: initial.revision, runtime: { FORWARDED_ALLOW_IPS: '127.0.0.1,172.17.0.16' }, setup_complete: false });
  expect(screen.getByText(/Restart required/)).toBeVisible();
  expect(input).toHaveValue('127.0.0.1,172.17.0.16');
});

it('keeps an edited draft and original revision during refetch, then explicitly reloads after conflict', async () => {
  const { cache } = renderPage();
  const input = await screen.findByRole('textbox', { name: 'Trusted reverse proxies' });
  fireEvent.change(input, { target: { value: '127.0.0.1,172.17.0.16' } });
  const newer = { ...initial, revision: 'b'.repeat(64), runtime: { ...initial.runtime, FORWARDED_ALLOW_IPS: '127.0.0.1,10.1.1.2' } };
  await act(async () => { cache.setQueryData(setupQueryKey, newer); });
  expect(input).toHaveValue('127.0.0.1,172.17.0.16');
  service.save.mockRejectedValue(new ApiError({ message: 'Conflict', status: 409, kind: 'validation', canRetry: false }));
  fireEvent.click(screen.getByRole('button', { name: 'Save network settings' }));
  expect(await screen.findByText(/Configuration changed in another session/)).toBeVisible();
  expect(service.save.mock.calls[0][0].expected_revision).toBe(initial.revision);
  expect(input).toHaveValue('127.0.0.1,172.17.0.16');
  service.get.mockResolvedValue(newer);
  fireEvent.click(screen.getByRole('button', { name: 'Reload saved settings' }));
  await waitFor(() => expect(input).toHaveValue('127.0.0.1,10.1.1.2'));
  expect(screen.getByRole('button', { name: 'Save network settings' })).toBeDisabled();
});

it('updates untouched fields on refetch and discards edits without saving', async () => {
  const { cache } = renderPage();
  const input = await screen.findByRole('textbox', { name: 'Trusted reverse proxies' });
  await act(async () => { cache.setQueryData(setupQueryKey, { ...initial, runtime: { ...initial.runtime, FORWARDED_ALLOW_IPS: '127.0.0.1' } }); });
  await waitFor(() => expect(input).toHaveValue('127.0.0.1'));
  fireEvent.click(screen.getByRole('checkbox', { name: 'Allow sources on private networks' }));
  fireEvent.click(screen.getByRole('button', { name: 'Discard changes' }));
  expect(screen.getByRole('checkbox', { name: 'Allow sources on private networks' })).toBeChecked();
  expect(service.save).not.toHaveBeenCalled();
});

it('shows load failure with retry and retains draft after a save failure', async () => {
  service.get.mockRejectedValueOnce(new Error('offline'));
  renderPage();
  fireEvent.click(await screen.findByRole('button', { name: 'Reload saved settings' }));
  const input = await screen.findByRole('textbox', { name: 'Trusted reverse proxies' });
  fireEvent.change(input, { target: { value: '127.0.0.1' } });
  service.save.mockRejectedValue(new Error('write failed'));
  fireEvent.click(screen.getByRole('button', { name: 'Save network settings' }));
  expect(await screen.findByText(/Could not save network settings/)).toBeVisible();
  expect(input).toHaveValue('127.0.0.1');
});

import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { Route, Routes } from 'react-router-dom';
import { TestMemoryRouter } from '../testUtils/router';
import Setup from '../pages/Setup';
import { scraperService } from '../services/scraperService';
import { epgService } from '../services/epgService';
import SetupNotice from '../components/SetupNotice';
import { setupService, type SetupState } from '../services/setupService';

jest.mock('../services/setupService', () => ({ setupQueryKey: ['installation-setup'], setupService: { get: jest.fn(), save: jest.fn() } }));
jest.mock('../services/scraperService');
jest.mock('../services/epgService');
const service = jest.mocked(setupService);
const initial: SetupState = {
  version: 1, setup_complete: false, revision: 'a'.repeat(64), restart_required: false, api_protected: false,
  runtime: { PLAYER_MAX_SESSIONS: 7, ENABLE_IPFS: false }, unavailable: { ENABLE_IPFS: 'Not included in this image' },
  options: [
    { name: 'PLAYER_MAX_SESSIONS', label: 'Maximum browser sessions', default: 3, kind: 'integer', group: 'playback', help: '', minimum: 1, maximum: 100 },
    { name: 'ENABLE_IPFS', label: 'IPFS', default: false, kind: 'boolean', group: 'services', help: '' },
  ],
};
function renderSetup(node: React.ReactNode, mode: 'light' | 'dark' = 'light', path = '/') {
  return render(<ThemeProvider theme={createAppTheme(mode)}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><TestMemoryRouter initialEntries={[path]}>{node}</TestMemoryRouter></QueryClientProvider></ThemeProvider>);
}
beforeEach(() => { jest.resetAllMocks(); jest.mocked(scraperService.getURLs).mockResolvedValue([]); jest.mocked(epgService.getSources).mockResolvedValue([]); service.get.mockResolvedValue(initial); });

it.each(['light', 'dark'] as const)('reviews and saves a draft with restart guidance in %s mode', async mode => {
  service.save.mockResolvedValue({ ...initial, runtime: { ...initial.runtime, PLAYER_MAX_SESSIONS: 5 }, setup_complete: true, restart_required: true });
  renderSetup(<Setup />, mode);
  fireEvent.click(await screen.findByRole('button', { name: 'Connection settings (advanced)' }));
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
  expect(service.save.mock.calls[0][0]).toEqual({ expected_revision: initial.revision, runtime: { ...initial.runtime, PLAYER_MAX_SESSIONS: 5 }, setup_complete: false });
  expect(screen.getByText(/Return to setup to add channel sources/)).toBeVisible();
});

it('keeps the draft after a failed save', async () => {
  service.save.mockRejectedValue(new Error('write failed'));
  renderSetup(<Setup />);
  fireEvent.click(await screen.findByRole('button', { name: 'Connection settings (advanced)' }));
  fireEvent.change(await screen.findByRole('spinbutton', { name: 'Maximum browser sessions' }), { target: { value: '6' } });
  for (let index = 0; index < 3; index++) fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save setup' }));
  await screen.findByRole('button', { name: 'Reload saved configuration' });
  expect(screen.getByText('Maximum browser sessions: 6')).toBeInTheDocument();
  expect(screen.queryByText('Build your catalogue')).not.toBeInTheDocument();
});

it('opens first-run setup with imported values and allows postponing without saving', async () => {
  renderSetup(<SetupNotice />);
  expect(await screen.findByRole('dialog', { name: 'Set up scraper' })).toBeVisible();
  expect(screen.getByRole('textbox', { name: 'Channel source link' })).toBeVisible();
  expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Set up later' }));
  expect(await screen.findByRole('link', { name: 'Set up scraper' })).toHaveAttribute('href', '/setup');
  expect(service.save).not.toHaveBeenCalled();
});

it('does not show first-run setup again for an existing installation', async () => {
  service.get.mockResolvedValue({ ...initial, setup_complete: true });
  renderSetup(<SetupNotice />);
  await waitFor(() => expect(service.get).toHaveBeenCalled());
  expect(screen.queryByRole('link', { name: 'Set up scraper' })).not.toBeInTheDocument();
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('offers retry when loading fails', async () => {
  service.get.mockRejectedValue(new Error('offline'));
  renderSetup(<Setup />);
  await screen.findByText('Setup could not be loaded.');
  service.get.mockResolvedValue(initial);
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  await screen.findByRole('textbox', { name: 'Channel source link' });
});

 it('does not reopen automatic setup after postponing from the explicit setup route', async () => {
  renderSetup(<><SetupNotice /><Routes><Route path="/setup" element={<Setup />} /><Route path="/settings" element={<p>Settings page</p>} /></Routes></>, 'light', '/setup');
  await screen.findByRole('textbox', { name: 'Channel source link' });
  fireEvent.click(screen.getByRole('button', { name: 'Set up later' }));
  expect(await screen.findByText('Settings page')).toBeVisible();
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(service.save).not.toHaveBeenCalled();
});

const connectionOptions = [
  { name: 'ACE_ENGINE_URL', label: 'Playback engine address', default: '', kind: 'url', group: 'playback', help: '' },
  { name: 'ACE_CHECK_ENGINE_URL', label: 'Dedicated checking engine address', default: '', kind: 'url', group: 'playback', help: '' },
  { name: 'ENABLE_ACEXY', label: 'Acexy', default: false, kind: 'boolean', group: 'services', help: '' },
  { name: 'ACEXY_LISTEN_ADDR', label: 'Acexy listen address', default: ':8080', kind: 'listen', group: 'acexy', help: '' },
  { name: 'ACEXY_BUFFER_SIZE', label: 'Acexy buffer size', default: '5MiB', kind: 'bytes', group: 'acexy', help: '' },
];

it('shows bundled addresses for existing saved blanks without saving a managed checker as external', async () => {
  service.get.mockResolvedValue({ ...initial, options: [...initial.options, ...connectionOptions], runtime: {
    ...initial.runtime, ACE_ENGINE_URL: '', ACE_CHECK_ENGINE_URL: '', ENABLE_ACESTREAM_ENGINE: true,
    ENABLE_ACESTREAM_CHECK_ENGINE: true, ACESTREAM_HTTP_PORT: 16878, ENABLE_ACEXY: true,
    ACEXY_LISTEN_ADDR: ':8084', ACEXY_BUFFER_SIZE: '5MiB',
  } });
  service.save.mockResolvedValue({ ...initial, setup_complete: true });
  renderSetup(<Setup />);
  fireEvent.click(await screen.findByRole('button', { name: 'Connection settings (advanced)' }));
  expect(await screen.findByRole('textbox', { name: 'Playback engine address' })).toHaveValue('http://localhost:16878');
  expect(screen.getByRole('textbox', { name: 'Dedicated checking engine address' })).toHaveValue('http://127.0.0.1:6880');
  expect(screen.getByRole('textbox', { name: 'Dedicated checking engine address' })).toHaveAttribute('readonly');
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByRole('checkbox', { name: 'Acexy' })).toBeChecked();
  fireEvent.click(screen.getByRole('button', { name: 'Acexy connection and buffering' }));
  expect(screen.getByRole('textbox', { name: 'Acexy listen address' })).toHaveValue(':8084');
  fireEvent.change(screen.getByRole('textbox', { name: 'Acexy buffer size' }), { target: { value: '10MiB' } });
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
  expect(screen.getByText('Acexy buffer size: 10MiB')).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Save setup' }));
  await waitFor(() => expect(service.save).toHaveBeenCalled());
  expect(service.save.mock.calls[0][0].runtime).toMatchObject({ ACE_ENGINE_URL: '', ACE_CHECK_ENGINE_URL: '', ACEXY_BUFFER_SIZE: '10MiB' });
});

it('explains saved Settings overrides and only changes an external default after accepting a suggestion', async () => {
  service.get.mockResolvedValue({ ...initial, options: [...initial.options, ...connectionOptions],
    runtime: { ...initial.runtime, ENABLE_ACESTREAM_ENGINE: true, ACE_ENGINE_URL: 'http://external:9999' },
    saved_overrides: { ACE_ENGINE_URL: 'http://saved:6878' },
  });
  renderSetup(<Setup />);
  fireEvent.click(await screen.findByRole('button', { name: 'Connection settings (advanced)' }));
  expect(await screen.findByRole('textbox', { name: 'Playback engine address' })).toHaveValue('http://external:9999');
  expect(screen.getByText(/Playback currently uses the address saved in Settings: http:\/\/saved:6878/)).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Use bundled playback address' }));
  expect(screen.getByRole('textbox', { name: 'Playback engine address' })).toHaveValue('http://localhost:6878');
  expect(service.save).not.toHaveBeenCalled();
});

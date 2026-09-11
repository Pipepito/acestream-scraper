import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import StartupGate from '../components/StartupGate';
import { startupService, type StartupStatus } from '../services/startupService';
import { ApiError } from '../services/apiErrors';

jest.mock('../services/startupService', () => ({ startupService: { status: jest.fn(), recover: jest.fn(), download: jest.fn() } }));
const service = startupService as jest.Mocked<typeof startupService>;
const failed: StartupStatus = {
  status: 'failed', phase: 'Database update stopped', recovery_available: true,
  recovery_token: 'nonce', guidance: 'Free some space and try again.',
  events: [{ time: '2026-09-06T11:00:00Z', message: 'Backup saved', level: 'info' }],
};

function renderGate(path = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}>
    <StartupGate><div>Application content</div></StartupGate>
  </MemoryRouter></QueryClientProvider>);
}

beforeEach(() => jest.resetAllMocks());

it('keeps application requests unmounted during startup', async () => {
  service.status.mockResolvedValue({ ...failed, status: 'starting', recovery_available: false });
  renderGate();
  expect(await screen.findByText('Database update stopped')).toBeInTheDocument();
  expect(screen.queryByText('Application content')).not.toBeInTheDocument();
  expect(screen.getByRole('progressbar', { name: 'Startup in progress' })).toBeInTheDocument();
});

it('opens the application when ready and keeps background progress accessible', async () => {
  service.status.mockResolvedValue({ ...failed, status: 'ready', migration: { status: 'running', total: 100, processed: 20 } });
  renderGate();
  expect(await screen.findByText('Application content')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'View progress' })).toHaveAttribute('href', '/startup');
});

it('requires confirmation for a fresh database and sends the current nonce', async () => {
  service.status.mockResolvedValue(failed);
  service.recover.mockResolvedValue({ ...failed, status: 'starting' });
  renderGate();
  await userEvent.click(await screen.findByRole('button', { name: 'Start fresh' }));
  expect(service.recover).not.toHaveBeenCalled();
  expect(screen.getByText(/will be backed up first/)).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(service.recover).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button', { name: 'Start fresh' }));
  await userEvent.click(screen.getByRole('button', { name: 'Back up and start fresh' }));
  await waitFor(() => expect(service.recover).toHaveBeenCalledWith('fresh', 'nonce'));
  expect(screen.queryByRole('button', { name: 'Start fresh' })).not.toBeInTheDocument();
});

it('downloads diagnostics and shows a useful download failure', async () => {
  service.status.mockResolvedValue(failed);
  service.download.mockRejectedValue(new Error('offline'));
  renderGate();
  await userEvent.click(await screen.findByRole('button', { name: 'Download diagnostics' }));
  expect(await screen.findByText(/Could not download diagnostics/)).toBeInTheDocument();
});

it('lets users authenticate before the normal settings page is available', async () => {
  service.status.mockRejectedValueOnce(new ApiError({ message: 'token required', status: 401, kind: 'auth', canRetry: false }));
  service.status.mockResolvedValue(failed);
  renderGate();
  await userEvent.type(await screen.findByLabelText('API token'), 'test-token');
  await userEvent.click(screen.getByRole('button', { name: 'Connect' }));
  expect(await screen.findByRole('heading', { name: 'Startup needs your attention' })).toBeInTheDocument();
});

it('keeps diagnostics accessible after startup has completed', async () => {
  service.status.mockResolvedValue({ ...failed, status: 'ready' });
  renderGate('/startup');
  expect(await screen.findByRole('heading', { name: 'Startup and migration' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Open app' })).toBeInTheDocument();
});

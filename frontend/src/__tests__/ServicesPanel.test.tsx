import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ServicesPanel, { formatUptime, restartDisabledReason } from '../components/ServicesPanel';
import { createAppTheme } from '../theme';
import type { ServiceStatus } from '../services/systemService';

const mockUseSystemServices = jest.fn();
const mockMutateAsync = jest.fn();
const mockControlAsync = jest.fn();

jest.mock('../hooks/useSystemServices', () => ({
  useSystemServices: (...args: unknown[]) => mockUseSystemServices(...args),
  useControlEngine: () => ({ mutateAsync: mockControlAsync, isPending: false }),
  useRestartService: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}));

const service = (overrides: Partial<ServiceStatus>): ServiceStatus => ({
  name: 'acestream',
  label: 'AceStream engine',
  description: 'Resolves and plays acestream:// content.',
  state: 'running',
  installed: true,
  enabled: true,
  managed: true,
  running: true,
  endpoint: 'http://localhost:6878',
  version: '3.1.80 (android)',
  distribution: 'jopsis/acestream v3.2.17-fix',
  distribution_url: 'https://hub.docker.com/r/jopsis/acestream',
  message: 'Engine answering at http://localhost:6878',
  pid: 42,
  uptime_seconds: 3700,
  ...overrides,
});

const renderPanel = () =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <ServicesPanel pollIntervalMs={60000} />
    </ThemeProvider>
  );

describe('ServicesPanel', () => {
  beforeEach(() => {
    mockMutateAsync.mockReset();
    mockControlAsync.mockReset();
    mockUseSystemServices.mockReset();
  });

  it('renders one card per service with its state, details and a restart control', () => {
    mockUseSystemServices.mockReturnValue({
      data: {
        supervised: true,
        checked_at: '2026-09-02T12:00:00Z',
        services: [
          service({}),
          service({ name: 'acexy', label: 'Acexy proxy', state: 'disabled', enabled: false, managed: false, running: false, pid: null, uptime_seconds: null, version: null, message: 'Installed but turned off (ENABLE_ACEXY=false).' }),
          service({ name: 'warp', label: 'Cloudflare WARP', state: 'not-installed', installed: false, enabled: false, managed: false, running: false, pid: null, uptime_seconds: null, version: null, endpoint: null, message: 'Not included in this image flavor.' }),
        ],
      },
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    });

    renderPanel();

    const engine = screen.getByRole('group', { name: 'Service AceStream engine' });
    expect(within(engine).getByText('Running')).toBeInTheDocument();
    expect(within(engine).getByText('Version: 3.1.80 (android)')).toBeInTheDocument();
    expect(within(engine).getByRole('link', { name: 'jopsis/acestream v3.2.17-fix' })).toHaveAttribute(
      'href',
      'https://hub.docker.com/r/jopsis/acestream'
    );
    expect(within(engine).getByText('Up for 1h 1m')).toBeInTheDocument();
    expect(within(engine).getByRole('button', { name: 'Restart AceStream engine' })).toBeEnabled();

    const acexy = screen.getByRole('group', { name: 'Service Acexy proxy' });
    expect(within(acexy).getByText('Disabled')).toBeInTheDocument();
    expect(within(acexy).getByRole('button', { name: 'Restart Acexy proxy' })).toBeDisabled();
    expect(within(acexy).getByText(/Turned off; enable it/)).toBeInTheDocument();

    const warp = screen.getByRole('group', { name: 'Service Cloudflare WARP' });
    expect(within(warp).getByText('Not installed')).toBeInTheDocument();
    expect(within(warp).getByRole('button', { name: 'Restart Cloudflare WARP' })).toBeDisabled();
  });

  it('explains that nothing can be restarted when the app is not supervised', () => {
    mockUseSystemServices.mockReturnValue({
      data: { supervised: false, checked_at: '', services: [service({ state: 'external', managed: false, pid: null, uptime_seconds: null })] },
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    });

    renderPanel();

    expect(screen.getByText(/not running under the container entrypoint/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Restart AceStream engine' })).toBeDisabled();
    expect(screen.getByText('Managed outside this container; restart it where it runs.')).toBeInTheDocument();
  });

  it('asks for confirmation, then requests the restart and reports it', async () => {
    mockUseSystemServices.mockReturnValue({
      data: { supervised: true, checked_at: '', services: [service({})] },
      isLoading: false,
      isFetching: false,
      error: null,
      refetch: jest.fn(),
    });
    mockMutateAsync.mockResolvedValue({ name: 'acestream', success: true, message: 'Restart requested; the supervisor relaunches acestream in a moment.' });

    renderPanel();

    fireEvent.click(screen.getByRole('button', { name: 'Restart AceStream engine' }));
    const dialog = screen.getByRole('dialog', { name: 'Restart AceStream engine?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Restart service' }));

    await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledWith('acestream'));
    expect(await screen.findByText(/Restart requested; the supervisor relaunches acestream/)).toBeInTheDocument();
    expect(screen.getByText('Restarting…')).toBeInTheDocument();
  });

  it.each([['acestream', false], ['acestream', true], ['acestream-check', false], ['acestream-check', true]] as const)('requests %s stopped=%s state and reports pending action', async (name, stopped) => {
    mockUseSystemServices.mockReturnValue({
      data: { supervised: true, services: [service({ name, stopped_by_user: stopped, state: stopped ? 'stopped' : 'running', pid: stopped ? null : 42 })] },
      isLoading: false, isFetching: false, error: null, refetch: jest.fn(),
    });
    mockControlAsync.mockResolvedValue({ success: true, message: 'Action requested.' });
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: `${stopped ? 'Start' : 'Stop'} AceStream engine` }));
    await waitFor(() => expect(mockControlAsync).toHaveBeenCalledWith({ action: stopped ? 'start' : 'stop', name }));
    expect(await screen.findByText(stopped ? 'Starting…' : 'Stopping…')).toBeInTheDocument();
  });

  it('reports a rejected stop without showing a pending operation', async () => {
    mockUseSystemServices.mockReturnValue({
      data: { supervised: true, services: [service({})] },
      isLoading: false, isFetching: false, error: null, refetch: jest.fn(),
    });
    mockControlAsync.mockRejectedValue(new Error('Unavailable'));
    renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Stop AceStream engine' }));
    expect(await screen.findByText(/Could not stop AceStream engine/)).toBeInTheDocument();
    expect(screen.queryByText('Stopping…')).not.toBeInTheDocument();
  });

  it('confirms Stop only after the child has gone, then offers Start', async () => {
    const response = {
      data: { supervised: true, services: [service({})] },
      isLoading: false, isFetching: false, error: null, refetch: jest.fn(),
    };
    mockUseSystemServices.mockReturnValue(response);
    mockControlAsync.mockResolvedValue({ success: true, message: 'Requested.' });
    const { rerender } = renderPanel();
    fireEvent.click(screen.getByRole('button', { name: 'Stop AceStream engine' }));
    await screen.findByText('Stopping…');
    mockUseSystemServices.mockReturnValue({
      ...response, data: { supervised: true, services: [service({ state: 'stopped', stopped_by_user: true, pid: null, running: false })] },
    });
    rerender(<ThemeProvider theme={createAppTheme('light')}><ServicesPanel /></ThemeProvider>);
    expect(await screen.findByText('AceStream engine is stopped. Select Start to resume.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start AceStream engine' })).toBeEnabled();
  });

  it('formats uptime and restart reasons', () => {
    expect(formatUptime(45)).toBe('45s');
    expect(formatUptime(600)).toBe('10m');
    expect(formatUptime(3 * 86400)).toBe('3d 0h');
    expect(restartDisabledReason(service({}), true)).toBeNull();
    expect(restartDisabledReason(service({ managed: false, installed: false }), true)).toMatch(/Not included/);
    expect(restartDisabledReason(service({ managed: false, enabled: false }), true)).toMatch(/Turned off/);
    expect(restartDisabledReason(service({ managed: false }), false)).toMatch(/outside this container/);
  });
});


it('distinguishes a measured idle proxy from unavailable telemetry and scopes engine counts', () => {
  mockUseSystemServices.mockReturnValue({ data: { supervised: true, services: [
    service({ open_streams: 2, stream_count_scope: 'app' }),
    service({ name: 'acexy', label: 'Acexy proxy', open_streams: 0, stream_count_scope: 'service' }),
  ] } });
  const { rerender } = renderPanel();
  expect(screen.getByText('Open streams through this app: 2')).toBeInTheDocument();
  expect(screen.getByText('Open streams through Acexy: 0')).toBeInTheDocument();
  expect(screen.getByText(/excludes direct players and Acexy/)).toBeInTheDocument();
  mockUseSystemServices.mockReturnValue({ data: { supervised: true, services: [
    service({ name: 'acexy', label: 'Acexy proxy', open_streams: null, stream_count_scope: 'service' }),
  ] } });
  rerender(<ThemeProvider theme={createAppTheme('dark')}><ServicesPanel /></ThemeProvider>);
  expect(screen.getByText('Open streams through Acexy: Unavailable')).toBeInTheDocument();
});

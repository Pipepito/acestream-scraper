import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ServicesPanel, { formatUptime, restartDisabledReason } from '../components/ServicesPanel';
import { createAppTheme } from '../theme';
import type { ServiceStatus } from '../services/systemService';

const mockUseSystemServices = jest.fn();
const mockMutateAsync = jest.fn();

jest.mock('../hooks/useSystemServices', () => ({
  useSystemServices: (...args: unknown[]) => mockUseSystemServices(...args),
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

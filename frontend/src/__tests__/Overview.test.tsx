import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Overview from '../pages/Overview';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseSystemServices = jest.fn();
const mockUseStats = jest.fn();
const mockUseHealth = jest.fn();
const mockUseTvChannelStats = jest.fn();
const mockUseBackgroundTaskStatus = jest.fn();

jest.mock('../hooks/useSystemServices', () => ({ useSystemServices: (...args: unknown[]) => mockUseSystemServices(...args) }));
jest.mock('../hooks/useConfig', () => ({
  useHealth: (...args: unknown[]) => mockUseHealth(...args),
  useStats: (...args: unknown[]) => mockUseStats(...args),
  useTvChannelStats: (...args: unknown[]) => mockUseTvChannelStats(...args),
}));
jest.mock('../hooks/useDashboard', () => ({ useBackgroundTaskStatus: (...args: unknown[]) => mockUseBackgroundTaskStatus(...args) }));
jest.mock('../components/ServicesPanel', () => ({ __esModule: true, default: () => <div data-testid="services-panel" /> }));

const service = (name: string, state: string, extra: Record<string, unknown> = {}) => ({
  name,
  label: name,
  description: '',
  state,
  installed: true,
  enabled: true,
  managed: true,
  running: state === 'running' || state === 'external',
  endpoint: null,
  version: null,
  message: `${name} ${state}`,
  pid: null,
  uptime_seconds: null,
  ...extra,
});

const query = (data: unknown) => ({ data, isLoading: false, error: null, refetch: jest.fn() });

const renderPage = () =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter>
        <Overview />
      </TestMemoryRouter>
    </ThemeProvider>
  );

describe('Overview', () => {
  beforeEach(() => {
    jest.useFakeTimers().setSystemTime(new Date('2026-09-02T10:12:00Z'));
    mockUseSystemServices.mockReturnValue(query({ supervised: true, checked_at: '', services: [service('acestream', 'running', { label: 'AceStream engine', version: '3.1.80 (android)' }), service('acexy', 'running')] }));
    mockUseHealth.mockReturnValue(query({ status: 'healthy', acestream: { status: 'online', message: 'Acestream Engine is running' }, settings: {}, version: '2.1.0' }));
    mockUseStats.mockReturnValue(query({ channels: { total: 6, online: 1, offline: 5, unknown: 0 }, urls: { total: 2, active: 2, error: 0 }, epg: { sources: 1, channels: 638, programs: 81799 } }));
    mockUseTvChannelStats.mockReturnValue(query({ total: 1, active: 1, with_epg: 1, acestreams: 2 }));
    mockUseBackgroundTaskStatus.mockReturnValue(
      query([
        { task_name: 'channel_cleanup', last_run: null, next_run: '2026-09-03T10:12:00Z', status: 'idle', last_error: null, last_result: null, progress: null },
        { task_name: 'url_scraping', last_run: '2026-09-02T10:00:00Z', next_run: '2026-09-02T10:15:00Z', status: 'idle', last_error: null, last_result: { processed: 2, failures: 0 }, progress: null },
        { task_name: 'epg_refresh', last_run: '2026-09-02T09:12:00Z', next_run: '2026-09-02T10:12:30Z', status: 'error', last_error: 'HTTP error: 502', last_result: null, progress: null },
      ])
    );
  });
  afterEach(() => jest.useRealTimers());

  it('reports a healthy stack with measured facts and the scheduler table', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1, name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    const summary = screen.getByRole('status', { name: 'Overview summary' });
    expect(within(summary).getByText('3.1.80 (android)')).toBeInTheDocument();
    expect(within(summary).getByText('6, 1 online')).toBeInTheDocument();
    expect(within(summary).getByText('638 channels')).toBeInTheDocument();
    expect(within(summary).getByText('12 min ago')).toBeInTheDocument();
    expect(screen.getByTestId('services-panel')).toBeInTheDocument();

    const jobs = screen.getByRole('table', { name: 'Scheduled jobs' });
    const rows = within(jobs).getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Scrape sources');
    expect(rows[1]).toHaveTextContent('12 min ago');
    expect(rows[1]).toHaveTextContent('2 sources, 0 errors');
    expect(rows[1]).toHaveTextContent('in 3 min');
    expect(rows[2]).toHaveTextContent('Refresh EPG');
    expect(rows[2]).toHaveTextContent('HTTP error: 502');
    expect(rows[2]).toHaveTextContent('Error');
    expect(rows[3]).toHaveTextContent('Remove stale channels');
    expect(rows[3]).toHaveTextContent('never');

    const guide = screen.getByRole('region', { name: 'Sources and guide' });
    expect(within(guide).getByText('Programmes')).toBeInTheDocument();
    expect(within(guide).getByText('81799')).toBeInTheDocument();
    expect(screen.queryByText(/Stream capacity/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Recent Activity/)).not.toBeInTheDocument();
  });

  it('reports an external engine as online when the in-container one is switched off', () => {
    mockUseSystemServices.mockReturnValue(query({ supervised: true, checked_at: '', services: [service('acestream', 'disabled', { label: 'AceStream engine', enabled: false, running: false, message: 'Installed but turned off (ENABLE_ACESTREAM_ENGINE=false).' })] }));
    renderPage();
    expect(screen.getByText('HEALTHY')).toBeInTheDocument();
    expect(within(screen.getByRole('status', { name: 'Overview summary' })).getByText('online (external)')).toBeInTheDocument();
  });

  it('flags attention when the engine probe fails even if no service is marked stopped', () => {
    mockUseHealth.mockReturnValue(query({ status: 'healthy', acestream: { status: 'error', message: 'Connection refused' }, settings: {}, version: '2.1.0' }));
    renderPage();
    expect(screen.getByText('ATTENTION')).toBeInTheDocument();
    expect(within(screen.getByRole('status', { name: 'Overview summary' })).getByText('not reachable')).toBeInTheDocument();
  });

  it('flags attention when an enabled service is down and says which', () => {
    mockUseHealth.mockReturnValue(query({ status: 'degraded', acestream: { status: 'error', message: 'Connection refused' }, settings: {}, version: '2.1.0' }));
    mockUseSystemServices.mockReturnValue(query({ supervised: true, checked_at: '', services: [service('acestream', 'stopped', { label: 'AceStream engine', message: 'Enabled but not running.' })] }));
    renderPage();
    expect(screen.getByText('ATTENTION')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('AceStream engine: Enabled but not running.');
    expect(within(screen.getByRole('status', { name: 'Overview summary' })).getByText('not reachable')).toHaveAttribute('data-tone', 'error');
  });
});

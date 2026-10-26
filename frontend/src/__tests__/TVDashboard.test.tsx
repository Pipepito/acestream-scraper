import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
jest.mock('../components/overview/UpcomingEvents', () => function MockUpcomingEvents() { return <section aria-label="Up next">Upcoming events</section>; });
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import TVDashboard from '../pages/TVDashboard';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockStats = jest.fn();
const mockTvStats = jest.fn();
const mockTasks = jest.fn();
const mockPlayback = jest.fn();
jest.mock('../hooks/useConfig', () => ({ useStats: () => mockStats(), useTvChannelStats: () => mockTvStats() }));
jest.mock('../hooks/useDashboard', () => ({ useBackgroundTaskStatus: () => mockTasks() }));
jest.mock('../hooks/usePlayer', () => ({ useActiveStreams: () => mockPlayback() }));
const query = (data: unknown) => ({ data, error: null, refetch: jest.fn() });
const renderPage = (mode: 'light' | 'dark' = 'light') => render(<QueryClientProvider client={new QueryClient()}><ThemeProvider theme={createAppTheme(mode)}><TestMemoryRouter><TVDashboard /></TestMemoryRouter></ThemeProvider></QueryClientProvider>);

beforeEach(() => {
  mockStats.mockReturnValue(query({ channels: { total: 6, online: 1, offline: 2, unknown: 3 }, urls: { total: 2, active: 2, error: 0 }, epg: { sources: 1, channels: 12, programs: 50 } }));
  mockTvStats.mockReturnValue(query({ total: 4, active: 3, with_epg: 2, acestreams: 6 }));
  mockTasks.mockReturnValue(query(['url_scraping', 'channel_status', 'channel_cleanup'].map(task_name => ({ task_name, status: 'waiting', last_run: null, next_run: null }))));
  mockPlayback.mockReturnValue(query({ streams: [] }));
});

it.each(['light', 'dark'] as const)('leads with TV and content, with links to watching and management in %s mode', mode => {
  renderPage(mode);
  expect(screen.getByRole('heading', { level: 1, name: 'TV dashboard' })).toBeVisible();
  expect(screen.getByRole('link', { name: 'Watch TV' })).toHaveAttribute('href', '/live-tv');
  expect(screen.getByRole('link', { name: 'Events' })).toHaveAttribute('href', '/events');
  expect(screen.getByRole('link', { name: 'All scheduled jobs' })).toHaveAttribute('href', '/system');
  expect(screen.getByText('Nothing is playing through this app right now.')).toBeVisible();
  const inventory = screen.getByRole('region', { name: 'Streams' });
  expect(within(inventory).getByText('Not checked yet')).toBeInTheDocument();
  expect(within(inventory).getByText('3')).toBeInTheDocument();
  const jobs = screen.getByRole('region', { name: 'Next updates' });
  expect(jobs).toHaveTextContent('Sources');
  expect(jobs).toHaveTextContent('Stream checks');
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
  expect(jobs).not.toHaveTextContent('Remove stale channels');
  expect(screen.queryByRole('heading', { name: 'Services' })).not.toBeInTheDocument();
});

it('shows browser and relay facts, but only counts playing sessions', () => {
  mockPlayback.mockReturnValue(query({ streams: [
    { id: 'a', kind: 'browser', content_id: 'a'.repeat(40), channel_name: 'Sports live', state: 'ready', viewers: 2, peers: 0 },
    { id: 'b', kind: 'relay', content_id: 'b'.repeat(40), channel_name: 'News relay', state: 'streaming', viewers: 1, client_label: 'tuner:192.0.2.1', started_at: null },
    { id: 'c', kind: 'browser', content_id: 'c'.repeat(40), channel_name: null, state: 'error', viewers: 0, peers: null },
    { id: 'd', kind: 'browser', content_id: 'd'.repeat(40), channel_name: 'Starting channel', state: 'starting', viewers: 1, peers: null },
  ] }));
  renderPage();
  expect(within(screen.getByRole('status', { name: 'TV dashboard summary' })).getByText('2')).toBeInTheDocument();
  expect(screen.getByText('In a browser · 2 viewers · 0 peers')).toBeVisible();
  expect(screen.getByText(/Media server or player at 192.0.2.1/)).toBeVisible();
  expect(screen.getByText('Unnamed stream cccccccc…')).toBeVisible();
  expect(screen.getByText('Failed')).toBeVisible();
  expect(screen.getByText('Starting')).toBeVisible();
});

it('does not claim empty playback or a stopped scheduler during loading', () => {
  mockPlayback.mockReturnValue(query(undefined));
  mockTasks.mockReturnValue(query(undefined));
  renderPage();
  expect(screen.getByText('Loading playback…')).toBeVisible();
  expect(screen.getByText('Loading next updates…')).toBeVisible();
  expect(screen.queryByText(/Nothing is playing/)).not.toBeInTheDocument();
  expect(screen.queryByText('The scheduler is not running.')).not.toBeInTheDocument();
});

it('keeps TV counts available when inventory fails and hides stale playback claims', () => {
  mockStats.mockReturnValue({ ...mockStats(), error: new Error('Inventory unavailable') });
  const retry = jest.fn();
  mockPlayback.mockReturnValue({ ...query({ streams: [] }), error: new Error('Playback unavailable'), refetch: retry });
  renderPage();
  expect(screen.getByRole('region', { name: 'TV channels' })).toHaveTextContent('4');
  expect(screen.getByRole('region', { name: 'Next updates' })).toBeInTheDocument();
  expect(screen.queryByText(/Nothing is playing/)).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Retry playback' }));
  expect(retry).toHaveBeenCalledTimes(1);
});

it('offers source setup for an empty inventory', () => {
  mockStats.mockReturnValue(query({ ...mockStats().data, channels: { total: 0, online: 0, offline: 0, unknown: 0 } }));
  renderPage();
  expect(screen.getByRole('link', { name: 'Add sources' })).toHaveAttribute('href', '/scraper');
});


describe('next update timing', () => {
  beforeEach(() => jest.useFakeTimers().setSystemTime(new Date('2026-10-26T10:00:00Z')));
  afterEach(() => jest.useRealTimers());

  it('shows only upcoming times and advances the countdown without a changed API response', () => {
    mockTasks.mockReturnValue(query([
      { task_name: 'url_scraping', status: 'idle', next_run: '2026-10-26T10:02:00Z', last_error: 'Old failure', last_result: { processed: 99 } },
      { task_name: 'epg_refresh', status: 'idle', next_run: '2026-10-26T12:00:00Z' },
    ]));
    renderPage();
    const updates = screen.getByRole('region', { name: 'Next updates' });
    expect(updates).toHaveTextContent('in 2 min');
    expect(updates).toHaveTextContent('in 2 h');
    expect(updates).toHaveTextContent('Not scheduled');
    expect(updates).not.toHaveTextContent('Old failure');
    expect(updates).not.toHaveTextContent('99');
    act(() => jest.advanceTimersByTime(90_000));
    expect(updates).toHaveTextContent('In less than a minute');
    act(() => jest.advanceTimersByTime(30_000));
    expect(updates).toHaveTextContent('Due');
  });

  it('distinguishes running, queued and unscheduled updates', () => {
    mockTasks.mockReturnValue(query([
      { task_name: 'url_scraping', status: 'running', next_run: '2026-10-27T10:00:00Z' },
      { task_name: 'epg_refresh', status: 'waiting', next_run: '2026-10-26T16:00:00Z' },
      { task_name: 'channel_status', status: 'idle', next_run: null },
    ]));
    renderPage();
    const updates = screen.getByRole('region', { name: 'Next updates' });
    expect(updates).toHaveTextContent('Running now');
    expect(updates).toHaveTextContent('Waiting to run');
    expect(updates).toHaveTextContent('Not scheduled');
  });

  it('keeps a failed schedule read unavailable instead of claiming no schedules', () => {
    mockTasks.mockReturnValue({ ...query([]), error: new Error('Schedule unavailable') });
    renderPage();
    expect(screen.getByRole('region', { name: 'Next updates' })).toHaveTextContent('Could not load next updates');
    expect(screen.queryByText('Not scheduled')).not.toBeInTheDocument();
  });
});

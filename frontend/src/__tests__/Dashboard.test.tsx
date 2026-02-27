import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';
import * as dashboardHooks from '../hooks/useDashboard';

// Mock apiClient to avoid axios import issues
jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

// Mock the dashboard hooks
jest.mock('../hooks/useDashboard');

const mockActivity = {
  results: [
    { id: 1, message: 'Scrape started', type: 'scrape', timestamp: new Date().toISOString(), user: 'system', details: { foo: 'bar' } },
    { id: 2, message: 'Scrape finished', type: 'scrape', timestamp: new Date().toISOString(), user: 'system', details: null }
  ],
  total_pages: 1
};
const mockBackgroundTasks = [
  { id: 'task1', task_name: 'Scrape', last_run: '2025-07-10T10:00:00Z', next_run: '2025-07-10T11:00:00Z', status: 'success', last_error: null, last_result: { count: 5 } }
];
const mockStreams = { count: 3, source: 'acexy' };
const mockWarp = { status: 'connected', error: null };
const mockConfig = { retention_days: 7, auto_refresh_interval: 60 };

beforeEach(() => {
  (dashboardHooks.useRecentActivity as jest.Mock).mockReturnValue({ data: mockActivity, isLoading: false });
  (dashboardHooks.useBackgroundTaskStatus as jest.Mock).mockReturnValue({ data: mockBackgroundTasks, isLoading: false });
  (dashboardHooks.useActiveStreams as jest.Mock).mockReturnValue({ data: mockStreams, isLoading: false });
  (dashboardHooks.useWarpStatus as jest.Mock).mockReturnValue({ data: mockWarp, isLoading: false });
  (dashboardHooks.useDashboardConfig as jest.Mock).mockReturnValue({ data: mockConfig, isLoading: false });
  (dashboardHooks.useUpdateDashboardConfig as jest.Mock).mockReturnValue({ mutate: jest.fn() });
});

describe('Dashboard UI', () => {
  it('renders activity, background tasks, streams, and warp status', async () => {
    render(<Dashboard />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Scrape started')).toBeInTheDocument();
    expect(screen.getByText('Scrape finished')).toBeInTheDocument();
    expect(screen.getByText('Background Tasks')).toBeInTheDocument();
    expect(screen.getByText('Scrape')).toBeInTheDocument();
    expect(screen.getByText('Active Streams')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Warp Status')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    (dashboardHooks.useDashboardConfig as jest.Mock).mockReturnValue({ data: undefined, isLoading: true });
    render(<Dashboard />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles error state', () => {
    (dashboardHooks.useDashboardConfig as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Config error!') });
    (dashboardHooks.useRecentActivity as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Activity error!') });
    (dashboardHooks.useBackgroundTaskStatus as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Task error!') });
    (dashboardHooks.useActiveStreams as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Streams error!') });
    (dashboardHooks.useWarpStatus as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Warp error!') });
    render(<Dashboard />);
    // Use a matcher function to find any error message
    expect(screen.getByText((content) => content.toLowerCase().includes('error'))).toBeInTheDocument();
  });
});

describe('Dashboard UI - settings and feedback', () => {
  it('persists auto-refresh toggle in localStorage', () => {
    localStorage.clear();
    render(<Dashboard />);
    const toggle = screen.getByLabelText('Auto-Refresh');
    expect(toggle).toBeChecked(); // default true
    fireEvent.click(toggle);
    expect(localStorage.getItem('dashboard-auto-refresh')).toBe('false');
    fireEvent.click(toggle);
    expect(localStorage.getItem('dashboard-auto-refresh')).toBe('true');
  });

  it('shows Snackbar on config update success', () => {
    (dashboardHooks.useUpdateDashboardConfig as jest.Mock).mockReturnValue({
      mutate: (_: any, opts: any) => opts.onSuccess && opts.onSuccess(),
    });
    render(<Dashboard />);
    const selects = screen.getAllByRole('combobox');
    const retentionSelect = selects[0];
    fireEvent.mouseDown(retentionSelect);
    const option = screen.getByRole('option', { name: '3 days' });
    fireEvent.click(option);
    expect(screen.getByText(/updated/i)).toBeInTheDocument();
  });

  it('shows Snackbar on config update error', () => {
    (dashboardHooks.useUpdateDashboardConfig as jest.Mock).mockReturnValue({
      mutate: (_: any, opts: any) => opts.onError && opts.onError(),
    });
    render(<Dashboard />);
    const selects = screen.getAllByRole('combobox');
    const retentionSelect = selects[0];
    fireEvent.mouseDown(retentionSelect);
    const option = screen.getByRole('option', { name: '3 days' });
    fireEvent.click(option);
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
  });
});

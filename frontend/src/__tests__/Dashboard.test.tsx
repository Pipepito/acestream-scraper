import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Dashboard from '../pages/Dashboard';
import * as dashboardHooks from '../hooks/useDashboard';
import { MemoryRouter } from 'react-router-dom';
import { createAppTheme, type ThemeMode } from '../theme';

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

const renderDashboard = (mode: ThemeMode = 'light') => {
  const theme = createAppTheme(mode);

  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </ThemeProvider>
  );
};

describe('Dashboard UI', () => {
  it('renders activity, background tasks, streams, and warp status', async () => {
    renderDashboard();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Scrape started')).toBeInTheDocument();
    expect(screen.getByText('Scrape finished')).toBeInTheDocument();
    expect(screen.getAllByText('Background Tasks').length).toBeGreaterThan(0);
    expect(screen.getByText('Scrape')).toBeInTheDocument();
    expect(screen.getByText('1. Confirm live stream capacity')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('2. Review protected routing')).toBeInTheDocument();
    expect(screen.getByText(/warp status: connected/i)).toBeInTheDocument();
  });

  it('renders activity when backend returns paginated items instead of results', () => {
    (dashboardHooks.useRecentActivity as jest.Mock).mockReturnValue({
      data: {
        items: [
          { id: 3, message: 'Backend item shape', type: 'sync', timestamp: new Date().toISOString(), user: 'system', details: null },
        ],
        total: 1,
        page: 1,
        page_size: 10,
      },
      isLoading: false,
    });

    renderDashboard();

    expect(screen.getByText('Backend item shape')).toBeInTheDocument();
  });

  it.each<ThemeMode>(['light', 'dark'])(
    'renders the shared page header and key sections in %s mode',
    (mode) => {
      renderDashboard(mode);

      expect(screen.getByRole('heading', { level: 1, name: 'Dashboard' })).toHaveClass('MuiTypography-pageTitle');
      expect(screen.getByText('Controls')).toBeInTheDocument();
      expect(screen.getByText('Operational path')).toBeInTheDocument();
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getAllByText('Background Tasks').length).toBeGreaterThan(0);
    }
  );

  it('renders dashboard primary actions inside the shared header action area', () => {
    renderDashboard();

    const primaryActions = screen.getByRole('navigation', { name: 'Dashboard primary actions' });

    expect(within(primaryActions).getByRole('link', { name: 'Open Scraper' })).toBeInTheDocument();
    expect(within(primaryActions).getByRole('link', { name: 'Channels' })).toBeInTheDocument();
    expect(within(primaryActions).getByRole('link', { name: 'EPG' })).toBeInTheDocument();
  });

  it.each<ThemeMode>(['light', 'dark'])(
    'keeps a visible focus-visible treatment available for dashboard actions in %s mode',
    (mode) => {
      renderDashboard(mode);

      expect(screen.getByRole('link', { name: 'EPG' })).toBeInTheDocument();

      const theme = createAppTheme(mode);
      const rootStyles = theme.components?.MuiButton?.styleOverrides?.root as Record<string, any>;

      expect(rootStyles['&.Mui-focusVisible']).toMatchObject({
        outline: '2px solid currentColor',
        outlineOffset: 2,
        boxShadow: expect.stringContaining(theme.appTokens.action.focusRing),
      });
    }
  );

  it('communicates operational status with text cues instead of color alone', () => {
    renderDashboard();

    expect(screen.getByRole('heading', { level: 2, name: 'Operational path' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/protected connection active/i);
    expect(screen.getByText(/streams available right now/i)).toBeInTheDocument();
    expect(screen.getByText(/scheduler is keeping background tasks on cadence/i)).toBeInTheDocument();
  });

  it('handles loading state', () => {
    (dashboardHooks.useDashboardConfig as jest.Mock).mockReturnValue({ data: undefined, isLoading: true });
    renderDashboard();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles error state', () => {
    (dashboardHooks.useDashboardConfig as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Config error!') });
    (dashboardHooks.useRecentActivity as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Activity error!') });
    (dashboardHooks.useBackgroundTaskStatus as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Task error!') });
    (dashboardHooks.useActiveStreams as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Streams error!') });
    (dashboardHooks.useWarpStatus as jest.Mock).mockReturnValue({ data: undefined, isLoading: false, error: new Error('Warp error!') });
    renderDashboard();
    // Use a matcher function to find any error message
    expect(screen.getByText((content) => content.toLowerCase().includes('error'))).toBeInTheDocument();
  });
});

describe('Dashboard UI - settings and feedback', () => {
  it('persists auto-refresh toggle in localStorage', () => {
    localStorage.clear();
    renderDashboard();
    const toggle = screen.getByRole('checkbox', { name: 'Auto-Refresh' });
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
    renderDashboard();
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
    renderDashboard();
    const selects = screen.getAllByRole('combobox');
    const retentionSelect = selects[0];
    fireEvent.mouseDown(retentionSelect);
    const option = screen.getByRole('option', { name: '3 days' });
    fireEvent.click(option);
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
  });
});

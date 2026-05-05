import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Dashboard from '../pages/Dashboard';
import * as dashboardHooks from '../hooks/useDashboard';
import { createAppTheme, type ThemeMode } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

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
      <TestMemoryRouter>
        <Dashboard />
      </TestMemoryRouter>
    </ThemeProvider>
  );
};

describe('Dashboard UI', () => {
  it('renders activity, background tasks, streams, and warp status', async () => {
    renderDashboard();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Scraper pulse')).toBeInTheDocument();
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('Scrape started')).toBeInTheDocument();
    expect(screen.getByText('Scrape finished')).toBeInTheDocument();
    expect(screen.getAllByText('Background Tasks').length).toBeGreaterThan(0);
    expect(screen.getByText('Scrape')).toBeInTheDocument();
    expect(screen.queryByText('1. Confirm live stream capacity')).not.toBeInTheDocument();
    expect(screen.getByText('Stream capacity')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Protected routing')).toBeInTheDocument();
    expect(screen.getByText('Scheduler follow-through')).toBeInTheDocument();
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
      expect(screen.getByText('Check readiness and move to the next workflow.')).toHaveStyle({ marginTop: '4px' });
      expect(screen.getByText('Dashboard tools')).toBeInTheDocument();
      expect(screen.getByText('Filter activity and adjust refresh behavior.')).toBeInTheDocument();
      expect(screen.getByText('System readiness')).toBeInTheDocument();
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getAllByText('Background Tasks').length).toBeGreaterThan(0);
    }
  );

  it('keeps recent activity metadata compact and only shows the user when present', () => {
    renderDashboard();

    expect(screen.getAllByText(/scrape - .* - system/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/User:/i)).not.toBeInTheDocument();
  });

  it('keeps background task metadata compact while preserving run timing and status', () => {
    renderDashboard();

    expect(screen.getByText(/last run 2025-07-10T10:00:00Z/i)).toBeInTheDocument();
    expect(screen.getByText(/next run 2025-07-10T11:00:00Z/i)).toBeInTheDocument();
    expect(screen.getByText(/status success/i)).toBeInTheDocument();
  });

  it('renders dashboard primary actions inside the shared header action area', () => {
    renderDashboard();

    const primaryActions = screen.getByRole('navigation', { name: 'Dashboard primary actions' });
    const headerActions = screen.getByTestId('page-header-actions');
    const epgButton = within(primaryActions).getByRole('link', { name: 'EPG' });
    const channelsButton = within(primaryActions).getByRole('link', { name: 'Channels' });
    const scraperButton = within(primaryActions).getByRole('link', { name: 'Open Scraper' });

    expect(headerActions).toContainElement(primaryActions);
    expect(scraperButton).toBeInTheDocument();
    expect(channelsButton).toBeInTheDocument();
    expect(epgButton).toBeInTheDocument();
    expect(epgButton.className).toContain('MuiButton-contained');
    expect(scraperButton.className).toContain('MuiButton-outlined');
    expect(channelsButton.className).toContain('MuiButton-outlined');
  });

  it('keeps dashboard header actions in the shared primary group contract', () => {
    renderDashboard();

    const primaryGroup = screen.getByTestId('page-header-primary-actions');
    const headerActions = screen.getByTestId('page-header-actions');

    expect(headerActions.firstChild).toBe(primaryGroup);
    expect(within(primaryGroup).getByRole('navigation', { name: 'Dashboard primary actions' })).toBeInTheDocument();
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

    expect(screen.getByRole('heading', { level: 2, name: 'System readiness' })).toBeInTheDocument();
    expect(screen.getByText(/^Freshness$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Next step$/i)).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/protected connection active/i);
    expect(screen.getByText(/streams available right now/i)).toBeInTheDocument();
    expect(screen.getByText(/latest run:/i)).toBeInTheDocument();
  });

  it('promotes scraper readiness as the dominant hero and keeps supporting metrics secondary', () => {
    renderDashboard();

    expect(screen.getByText('Scraper pulse')).toBeInTheDocument();
    expect(screen.getByText(/scraper is active and ready for the next scheduled pass/i)).toBeInTheDocument();
    expect(screen.getByText(/^Freshness$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Attention needed$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Next step$/i)).toBeInTheDocument();
    expect(screen.getByText(/open scraper to review job details/i)).toBeInTheDocument();
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

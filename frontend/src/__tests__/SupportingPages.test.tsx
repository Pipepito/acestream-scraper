import React from 'react';
import { render, screen, within, waitFor, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import * as routerDom from 'react-router-dom';
import { Route, Routes } from 'react-router-dom';
import Health from '../pages/Health';
import Playlist from '../pages/Playlist';
import Settings from '../pages/Settings';
import WarpPage from '../pages/WARP';
import NotFound from '../pages/NotFound';
import App from '../App';
import Channels from '../pages/Channels';
import ChannelDetail from '../pages/ChannelDetail';
import SearchNew from '../pages/SearchNew';
import Stats from '../pages/Stats';
import EPGMappings from '../pages/EPGMappings';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import * as configHooks from '../hooks/useConfig';
import * as epgHooks from '../hooks/useEPG';
import * as playlistHooks from '../hooks/usePlaylists';
import * as warpHooks from '../hooks/useWarp';
import { configService } from '../services/configService';
import { WarpMode } from '../types/warpTypes';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';
import { useMediaQuery } from '@mui/material';

const actualRouterDom = jest.requireActual('react-router-dom');
const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');

  return {
    ...actual,
    useNavigate: jest.fn(),
  };
});

jest.mock('../bootstrap/AppBootstrap', () => {
  const actual = jest.requireActual('../bootstrap/AppBootstrap');

  return {
    ...actual,
    useAppThemeMode: jest.fn(),
  };
});

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

jest.mock('../components/layout/AppShell', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

jest.mock('../hooks/useConfig');
jest.mock('../components/ServicesPanel', () => ({
  __esModule: true,
  default: () => <div data-testid="services-panel" />,
}));
jest.mock('../hooks/useEPG');
jest.mock('../hooks/usePlaylists');
jest.mock('../hooks/useWarp');
jest.mock('../hooks/useBaseUrls', () => ({
  useBaseUrls: () => ({ data: [], isLoading: false, error: undefined }),
  useCreateBaseUrl: () => ({ mutate: jest.fn(), isPending: false }),
  usePatchBaseUrl: () => ({ mutate: jest.fn(), isPending: false }),
  useDeleteBaseUrl: () => ({ mutate: jest.fn(), isPending: false }),
}));
jest.mock('../services/configService', () => ({
  configService: {
    getAppId: jest.fn(),
    updateAppId: jest.fn(),
  },
}));

const renderPage = (ui: React.ReactElement) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter>{ui}</TestMemoryRouter>
    </ThemeProvider>
  );

const renderAppAtRoute = (initialEntries: string[]) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter initialEntries={initialEntries}>
        <App />
      </TestMemoryRouter>
    </ThemeProvider>
  );

const renderLegacyPageWithRoutes = (routePath: string, page: React.ReactElement) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter initialEntries={[routePath]}>
        <Routes>
          <Route path={routePath} element={page} />
          <Route path="/tv-channels" element={<div>TV Channels destination</div>} />
          <Route path="/acestream-channels" element={<div>Acestream Channels destination</div>} />
          <Route path="/epg" element={<div>EPG destination</div>} />
          <Route path="/search" element={<div>Search destination</div>} />
        </Routes>
      </TestMemoryRouter>
    </ThemeProvider>
  );

const renderNotFoundWithRoutes = (initialRoute: string) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="*" element={<NotFound />} />
          <Route path="/" element={<div>Dashboard destination</div>} />
          <Route path="/tv-channels" element={<div>TV Channels destination</div>} />
          <Route path="/search" element={<div>Search destination</div>} />
        </Routes>
      </TestMemoryRouter>
    </ThemeProvider>
  );

beforeEach(() => {
  jest.clearAllMocks();
  mockUseMediaQuery.mockReset();
  (routerDom.useNavigate as jest.Mock).mockImplementation(() => actualRouterDom.useNavigate());

  mockResponsiveShellQueries(mockUseMediaQuery, createAppTheme('light'), {
    isPhone: false,
    isDesktop: true,
    isWideDesktop: true,
  });

  (configHooks.useHealth as jest.Mock).mockReturnValue({
    data: {
      status: 'healthy',
      version: '1.0.0',
      acestream: { status: 'online', message: 'Engine reachable' },
      settings: { region: 'EU', profile: 'Default' },
    },
    isLoading: false,
    error: undefined,
    refetch: jest.fn(),
  });

  (configHooks.useStats as jest.Mock).mockReturnValue({
    data: {
      channels: { total: 120, online: 112, offline: 4, unknown: 4 },
      urls: { total: 210, active: 202, error: 8 },
      epg: { sources: 7, channels: 95, programs: 5000 },
    },
    isLoading: false,
    error: undefined,
    refetch: jest.fn(),
  });

  (epgHooks.useAllEPGStringMappings as jest.Mock).mockReturnValue({
    data: [
      { id: 11, epg_channel_id: 101, search_pattern: 'Sport TV', is_exclusion: false },
      { id: 12, epg_channel_id: 202, search_pattern: 'Regional Feed', is_exclusion: true },
    ],
    isLoading: false,
    error: undefined,
  });

  (epgHooks.useDeleteGlobalEPGStringMapping as jest.Mock).mockReturnValue({
    mutateAsync: jest.fn(),
    isPending: false,
  });

  (configHooks.useBaseUrl as jest.Mock).mockReturnValue({ data: 'acestream://', isLoading: false });
  (configHooks.useUpdateBaseUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  (configHooks.useAceEngineUrl as jest.Mock).mockReturnValue({ data: 'http://localhost:6878', isLoading: false });
  (configHooks.useUpdateAceEngineUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  (configHooks.useRescrapeInterval as jest.Mock).mockReturnValue({ data: 24, isLoading: false });
  (configHooks.useUpdateRescrapeInterval as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  (configHooks.useAddPid as jest.Mock).mockReturnValue({ data: true, isLoading: false });
  (configHooks.useUpdateAddPid as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  (configHooks.useAllSettings as jest.Mock).mockReturnValue({
    data: {
      base_url: 'acestream://',
      ace_engine_url: 'http://localhost:6878',
      rescrape_interval: '24',
      addpid: 'true',
      appid: 'true',
      playlist_name: 'Daily Channels',
      xmltv_url: 'https://example.test/epg.xml',
    },
    isLoading: false,
    error: undefined,
  });
  (configHooks.useAcestreamStatus as jest.Mock).mockReturnValue({
    data: { status: 'online', message: 'Engine online and ready' },
    isLoading: false,
    error: undefined,
    refetch: jest.fn(),
  });

  (playlistHooks.useChannelGroups as jest.Mock).mockReturnValue({
    data: ['News', 'Sports'],
    isLoading: false,
  });

  (warpHooks.useWarpStatus as jest.Mock).mockReturnValue({
    data: {
      running: true,
      connected: true,
      mode: WarpMode.WARP,
      account_type: 'free',
      ip: '203.0.113.1',
      cf_trace: { colo: 'LHR' },
    },
    isLoading: false,
    error: undefined,
  });
  (warpHooks.useWarpConnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  (warpHooks.useWarpDisconnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isPending: false });
  (warpHooks.useWarpSetMode as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
  (warpHooks.useWarpRegisterLicense as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isPending: false });

  (configService.getAppId as jest.Mock).mockResolvedValue(true);
  (configService.updateAppId as jest.Mock).mockResolvedValue(undefined);
});

describe('Supporting page normalization', () => {
  beforeEach(() => {
    (useAppThemeMode as jest.Mock).mockReturnValue({
      mode: 'light',
      setMode: jest.fn(),
      toggleMode: jest.fn(),
    });
  });

  const renderHealthPage = () => renderPage(<Health />);

  it('renders Health with a shared page title and operational sections', () => {
    renderHealthPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Health' })).toBeInTheDocument();
    expect(
      screen.getByText('Check system readiness, confirm engine connectivity, and review core service totals.')
    ).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Status overview' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Operational details' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Supporting totals' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Runtime details' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Configuration snapshot' })).toBeInTheDocument();
  });

  it('renders the healthy readiness summary and next step only when the system is healthy and the engine is online', () => {
    renderHealthPage();

    expect(screen.getByText('Healthy and ready for scraper, playlist, channel, and EPG work.')).toBeInTheDocument();
    expect(screen.getByText('Next step')).toBeInTheDocument();
    expect(screen.getByText('Continue with scraper, playlist, channel, or EPG work.')).toBeInTheDocument();
  });

  it('uses the review guidance when the overall status is healthy but the engine is not online', () => {
    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: {
        status: 'healthy',
        version: '1.0.0',
        acestream: { status: 'offline', message: 'Engine unavailable' },
        settings: { region: 'EU', profile: 'Default' },
      },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    renderHealthPage();

    expect(screen.getByText('The system needs review before you continue.')).toBeInTheDocument();
    expect(screen.getByText('Stop and review engine connection and saved settings before proceeding.')).toBeInTheDocument();
    expect(screen.queryByText('Healthy and ready for scraper, playlist, channel, and EPG work.')).not.toBeInTheDocument();
  });

  it('aligns the page-header status chip with the not-ready branch when the engine is offline', () => {
    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: {
        status: 'healthy',
        version: '1.0.0',
        acestream: { status: 'offline', message: 'Engine unavailable' },
        settings: { region: 'EU', profile: 'Default' },
      },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    renderHealthPage();

    const headerActions = screen.getByTestId('page-header-actions');

    expect(screen.getByText('The system needs review before you continue.')).toBeInTheDocument();
    expect(within(headerActions).getByText('ERROR')).toBeInTheDocument();
    expect(within(headerActions).queryByText('HEALTHY')).not.toBeInTheDocument();
  });

  it('uses degraded readiness guidance when the overall status is degraded', () => {
    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: {
        status: 'degraded',
        version: '1.0.0',
        acestream: { status: 'online', message: 'Engine reachable with warnings' },
        settings: { region: 'EU', profile: 'Default' },
      },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    renderHealthPage();

    expect(screen.getByText('Healthy enough to continue, but one or more systems need attention.')).toBeInTheDocument();
    expect(screen.getByText('Review engine reachability and configuration before continuing.')).toBeInTheDocument();
  });

  it('uses the fallback review guidance when the overall status is in an error branch', () => {
    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: {
        status: 'error',
        version: '1.0.0',
        acestream: { status: 'offline', message: 'Engine unavailable' },
        settings: { region: 'EU', profile: 'Default' },
      },
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    renderHealthPage();

    expect(screen.getByText('The system needs review before you continue.')).toBeInTheDocument();
    expect(screen.getByText('Stop and review engine connection and saved settings before proceeding.')).toBeInTheDocument();
  });

  it('keeps overall system status and Acestream engine status explicit in text', () => {
    renderHealthPage();

    expect(screen.getByText('Overall system status')).toBeInTheDocument();
    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.getAllByText('Acestream engine status').length).toBeGreaterThan(0);
    expect(screen.getAllByText('online').length).toBeGreaterThan(0);
  });

  it('refetches both health and stats when Refresh status is clicked', () => {
    const refetchHealth = jest.fn();
    const refetchStats = jest.fn();

    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: {
        status: 'healthy',
        version: '1.0.0',
        acestream: { status: 'online', message: 'Engine reachable' },
        settings: { region: 'EU', profile: 'Default' },
      },
      isLoading: false,
      error: undefined,
      refetch: refetchHealth,
    });
    (configHooks.useStats as jest.Mock).mockReturnValue({
      data: {
        channels: { total: 120, online: 112, offline: 4, unknown: 4 },
        urls: { total: 210, active: 202, error: 8 },
        epg: { sources: 7, channels: 95, programs: 5000 },
      },
      isLoading: false,
      error: undefined,
      refetch: refetchStats,
    });

    renderHealthPage();

    fireEvent.click(screen.getByRole('button', { name: 'Refresh status' }));

    expect(refetchHealth).toHaveBeenCalledTimes(1);
    expect(refetchStats).toHaveBeenCalledTimes(1);
  });

  it('keeps the shared Retry error action refetching both health and stats', () => {
    const refetchHealth = jest.fn();
    const refetchStats = jest.fn();

    (configHooks.useHealth as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('health failed'),
      refetch: refetchHealth,
    });
    (configHooks.useStats as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: undefined,
      refetch: refetchStats,
    });

    renderHealthPage();

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(refetchHealth).toHaveBeenCalledTimes(1);
    expect(refetchStats).toHaveBeenCalledTimes(1);
  });

  it('shows explicit fallback totals when stats are unavailable without a stats query error', () => {
    (configHooks.useStats as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    renderHealthPage();

    expect(screen.getByRole('heading', { level: 2, name: 'Supporting totals' })).toBeInTheDocument();
    expect(screen.getByText('No channel totals available')).toBeInTheDocument();
    expect(screen.getByText('No URL totals available')).toBeInTheDocument();
    expect(screen.getByText('No EPG totals available')).toBeInTheDocument();
  });

  it('shows Acestream engine status, Acestream engine message, software version, and current settings in the supporting detail groups', () => {
    renderHealthPage();

    const runtimeDetails = screen.getByRole('region', { name: 'Runtime details' });
    const configurationSnapshot = screen.getByRole('region', { name: 'Configuration snapshot' });

    expect(within(runtimeDetails).getByRole('heading', { level: 3, name: 'Runtime details' })).toBeInTheDocument();
    expect(within(configurationSnapshot).getByRole('heading', { level: 3, name: 'Configuration snapshot' })).toBeInTheDocument();
    expect(within(runtimeDetails).getByText('Acestream engine status')).toBeInTheDocument();
    expect(within(runtimeDetails).getByText('Acestream engine message')).toBeInTheDocument();
    expect(within(runtimeDetails).getByText('Software version')).toBeInTheDocument();
    expect(within(configurationSnapshot).getByText('region')).toBeInTheDocument();
    expect(within(configurationSnapshot).getByText('profile')).toBeInTheDocument();
  });

  it('renders Playlist with the shared header and a clearer primary action path', () => {
    renderPage(<Playlist />);

    expect(screen.getByRole('heading', { level: 1, name: 'Playlist' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Generate playlist' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Show advanced options' })).toBeInTheDocument();
  });

  it('renders Settings with shared sections and explicit engine status text', async () => {
    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Engine connection' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Appearance' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Light theme' })).toBeChecked();
    expect(screen.getByRole('radio', { name: 'Dark theme' })).not.toBeChecked();
    expect(screen.getByText(/engine online and ready/i)).toBeInTheDocument();
  });

  it('renders a grouped settings inventory with saved backend values and unknown keys', async () => {
    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 2, name: 'Settings inventory' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Common connection settings' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Automation settings' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: 'Advanced/internal settings' })).toBeInTheDocument();
    expect(screen.getByText('base_url')).toBeInTheDocument();
    expect(screen.getByText('ace_engine_url')).toBeInTheDocument();
    expect(screen.getByText('playlist_name')).toBeInTheDocument();
    expect(screen.getByText('xmltv_url')).toBeInTheDocument();
    expect(screen.getByText(/saved backend values appear here\./i)).toBeInTheDocument();
    expect(screen.getByText(/unsaved edits above do not appear here until save succeeds\./i)).toBeInTheDocument();
  });

  it('keeps editable connection and automation keys visible in the read-only inventory', async () => {
    renderPage(<Settings />);

    const inventorySection = await screen.findByRole('region', { name: 'Settings inventory' });
    const commonGroup = within(inventorySection).getByRole('region', { name: 'Common connection settings' });
    const automationGroup = within(inventorySection).getByRole('region', { name: 'Automation settings' });

    expect(within(commonGroup).getByRole('heading', { level: 3, name: 'Common connection settings' })).toBeInTheDocument();
    expect(within(automationGroup).getByRole('heading', { level: 3, name: 'Automation settings' })).toBeInTheDocument();
    expect(within(commonGroup).getByText('base_url')).toBeInTheDocument();
    expect(within(commonGroup).getByText('ace_engine_url')).toBeInTheDocument();
    expect(within(automationGroup).getByText('rescrape_interval')).toBeInTheDocument();
    expect(within(automationGroup).getByText('addpid')).toBeInTheDocument();
    expect(within(automationGroup).getByText('appid')).toBeInTheDocument();
  });

  it('renders unknown keys under advanced internal settings', async () => {
    renderPage(<Settings />);

    const inventorySection = await screen.findByRole('region', { name: 'Settings inventory' });
    const advancedGroup = within(inventorySection).getByRole('region', { name: 'Advanced/internal settings' });

    expect(within(advancedGroup).getByRole('heading', { level: 3, name: 'Advanced/internal settings' })).toBeInTheDocument();
    expect(within(advancedGroup).getByText('playlist_name')).toBeInTheDocument();
    expect(within(advancedGroup).getByText('xmltv_url')).toBeInTheDocument();
  });

  it('renders not set when an inventory value is empty', async () => {
    (configHooks.useAllSettings as jest.Mock).mockReturnValue({
      data: { playlist_name: '' },
      isLoading: false,
      error: undefined,
    });

    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 2, name: 'Settings inventory' })).toBeInTheDocument();
    expect(screen.getByText('playlist_name')).toBeInTheDocument();
    expect(screen.getByText('Not set')).toBeInTheDocument();
  });

  it('shows an inventory loading state without blocking editable controls', async () => {
    (configHooks.useAllSettings as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: true,
      error: undefined,
    });

    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 2, name: 'Settings inventory' })).toBeInTheDocument();
    expect(screen.getByText(/loading saved settings inventory/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Connection settings' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save base URL' })).toBeInTheDocument();
  });

  it('shows an inventory error state without blocking editable controls', async () => {
    (configHooks.useAllSettings as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('inventory failed'),
    });

    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 2, name: 'Settings inventory' })).toBeInTheDocument();
    expect(screen.getByText(/could not load the saved settings inventory/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Automation settings' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /append pid to generated acestream links/i })).toBeInTheDocument();
  });

  it('shows an inventory empty state when no stored settings are available', async () => {
    (configHooks.useAllSettings as jest.Mock).mockReturnValue({
      data: {},
      isLoading: false,
      error: undefined,
    });

    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 2, name: 'Settings inventory' })).toBeInTheDocument();
    expect(screen.getByText(/no stored settings are available to review right now/i)).toBeInTheDocument();
  });

  it('updates theme mode through the shared settings appearance control', async () => {
    const setMode = jest.fn();
    (useAppThemeMode as jest.Mock).mockReturnValue({
      mode: 'light',
      setMode,
      toggleMode: jest.fn(),
    });

    renderPage(<Settings />);

    fireEvent.click(await screen.findByRole('radio', { name: 'Dark theme' }));

    expect(setMode).toHaveBeenCalledWith('dark');
  });

  it('recovers from AppID load failures and re-enables the toggle after update failures', async () => {
    (configService.getAppId as jest.Mock).mockRejectedValueOnce(new Error('load failed'));
    (configService.updateAppId as jest.Mock).mockRejectedValueOnce(new Error('save failed'));

    renderPage(<Settings />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument();
    expect(screen.getByText(/could not load appid setting/i)).toBeInTheDocument();

    const appIdToggle = screen.getByRole('checkbox', { name: /use appid in acestream links/i });

    fireEvent.click(appIdToggle);

    await waitFor(() => expect(configService.updateAppId).toHaveBeenCalledWith(true));
    await waitFor(() => expect(appIdToggle).not.toBeDisabled());
    expect(appIdToggle).not.toBeChecked();
    expect(screen.getByText(/failed to update appid setting/i)).toBeInTheDocument();
  });

  it('updates the saved appid inventory row after a successful toggle', async () => {
    let allSettingsData = {
      base_url: 'acestream://',
      ace_engine_url: 'http://localhost:6878',
      rescrape_interval: '24',
      addpid: 'true',
      appid: 'true',
    };

    const refetchAllSettings = jest.fn().mockImplementation(() => {
      allSettingsData = {
        ...allSettingsData,
        appid: 'false',
      };

      return Promise.resolve({ data: allSettingsData });
    });

    (configHooks.useAllSettings as jest.Mock).mockReturnValue({
      get data() {
        return allSettingsData;
      },
      isLoading: false,
      error: undefined,
      refetch: refetchAllSettings,
    });

    renderPage(<Settings />);

    const inventorySection = await screen.findByRole('region', { name: 'Settings inventory' });
    const automationInventory = within(inventorySection).getByRole('region', { name: 'Automation settings' });
    const getAppidRow = () => within(automationInventory).getByTestId('settings-inventory-row-appid');

    expect(within(automationInventory).getByText('appid')).toBeInTheDocument();
    expect(getAppidRow()).toHaveTextContent('appid');
    expect(getAppidRow()).toHaveTextContent('true');

    fireEvent.click(screen.getByRole('checkbox', { name: /use appid in acestream links/i }));

    await waitFor(() => expect(configService.updateAppId).toHaveBeenCalledWith(false));
    await waitFor(() => expect(getAppidRow()).toHaveTextContent('false'));
  });

  it('renders WARP actions inside the shared responsive header actions area', () => {
    renderPage(<WarpPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'WARP' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Connect' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Disconnect' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Connection status' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/connected/i);
  });

  it('syncs the WARP mode selector with backend status before allowing mode changes', () => {
    (warpHooks.useWarpStatus as jest.Mock).mockReturnValue({
      data: {
        running: true,
        connected: false,
        mode: WarpMode.DOT,
        account_type: 'free',
        ip: '203.0.113.1',
        cf_trace: {},
      },
      isLoading: false,
      error: undefined,
    });

    renderPage(<WarpPage />);

    expect(screen.getByRole('combobox', { name: 'Mode' })).toHaveTextContent(/dot/i);
    expect(screen.getByRole('button', { name: 'Set Mode' })).toBeDisabled();
    expect(screen.getByRole('alert')).toHaveTextContent(/mode: dot/i);
  });

  it('renders NotFound as an unsupported-route recovery surface with stronger navigation paths', () => {
    renderPage(<NotFound />);

    const headerCopy = screen.getByTestId('page-header-copy');
    const sectionCopy = screen.getByTestId('content-section-copy');
    const recoveryStatus = screen.getByText(/unsupported route: restart from dashboard, tv channels, or search/i);
    const supportCopy = screen.getByText(/use one of the supported routes below to recover quickly/i);
    const dashboardAction = screen.getByRole('button', { name: 'Open Dashboard' });

    expect(screen.getByRole('heading', { level: 1, name: 'Page not found' })).toBeInTheDocument();
    expect(headerCopy).toHaveTextContent(/unsupported or outdated route/i);
    expect(headerCopy).toHaveTextContent(/restart from a supported workspace/i);
    expect(screen.getByRole('heading', { level: 2, name: 'Go to a supported workflow' })).toBeInTheDocument();
    expect(sectionCopy).toHaveTextContent(/old bookmark|stale link|unsupported path/i);
    expect(screen.getByRole('button', { name: 'Open Dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open TV Channels' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open Search' })).toBeInTheDocument();
    expect(headerCopy.compareDocumentPosition(sectionCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(sectionCopy.compareDocumentPosition(recoveryStatus) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(recoveryStatus.compareDocumentPosition(dashboardAction) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(dashboardAction.compareDocumentPosition(supportCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('navigates from NotFound to the primary and likely supported destinations', () => {
    const view = renderNotFoundWithRoutes('/unsupported-route');

    fireEvent.click(screen.getByRole('button', { name: 'Open Dashboard' }));
    expect(screen.getByText('Dashboard destination')).toBeInTheDocument();

    view.unmount();

    const { unmount: unmountTvRecovery } = renderNotFoundWithRoutes('/unsupported-route');
    fireEvent.click(screen.getByRole('button', { name: 'Open TV Channels' }));
    expect(screen.getByText('TV Channels destination')).toBeInTheDocument();

    unmountTvRecovery();

    renderNotFoundWithRoutes('/unsupported-route');
    fireEvent.click(screen.getByRole('button', { name: 'Open Search' }));
    expect(screen.getByText('Search destination')).toBeInTheDocument();
  });

  it('replaces unsupported-route history entries when using NotFound recovery actions', () => {
    const navigate = jest.fn();
    (routerDom.useNavigate as jest.Mock).mockReturnValue(navigate);

    renderPage(<NotFound />);

    fireEvent.click(screen.getByRole('button', { name: 'Open Dashboard' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open TV Channels' }));
    fireEvent.click(screen.getByRole('button', { name: 'Open Search' }));

    expect(navigate).toHaveBeenNthCalledWith(1, '/', { replace: true });
    expect(navigate).toHaveBeenNthCalledWith(2, '/tv-channels', { replace: true });
    expect(navigate).toHaveBeenNthCalledWith(3, '/search', { replace: true });
  });

  it('wires legacy routes in App to explicit recovery pages', () => {
    const { unmount: unmountChannelsRoute } = renderAppAtRoute(['/channels']);
    expect(screen.getByRole('heading', { level: 1, name: 'Channels' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open TV Channels' })).toBeInTheDocument();
    unmountChannelsRoute();

    const { unmount: unmountChannelDetailRoute } = renderAppAtRoute(['/channels/legacy-id']);
    expect(screen.getByRole('heading', { level: 1, name: 'Channel detail' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open TV Channels' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open EPG' })).toBeInTheDocument();
    unmountChannelDetailRoute();

    renderAppAtRoute(['/search-new']);
    expect(screen.getByRole('heading', { level: 1, name: 'Search' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open Search' })).toBeInTheDocument();
  });

  it('renders the Stats page through the real app route table', () => {
    renderAppAtRoute(['/stats']);

    expect(screen.getByRole('heading', { level: 1, name: 'Stats' })).toBeInTheDocument();
  });

  it('renders the EPG Mappings page through the real app route table', () => {
    renderAppAtRoute(['/epg/mappings']);

    expect(screen.getByRole('heading', { level: 1, name: 'EPG Mappings' })).toBeInTheDocument();
  });

  it('renders EPG Mappings with the global rules table and rule chips', () => {
    renderPage(<EPGMappings />);

    expect(screen.getByRole('heading', { level: 1, name: 'EPG Mappings' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Global mapping rules' })).toBeInTheDocument();
    expect(screen.getByText('Sport TV')).toBeInTheDocument();
    expect(screen.getByText('Include')).toBeInTheDocument();
    expect(screen.getByText('Exclude')).toBeInTheDocument();
  });

  it('renders Stats with the required summary and grouped total sections', () => {
    renderPage(<Stats />);

    expect(screen.getByRole('heading', { level: 1, name: 'Stats' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Inventory snapshot' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Totals by source' })).toBeInTheDocument();
    expect(screen.getByText('Channel totals')).toBeInTheDocument();
    expect(screen.getByText('URL totals')).toBeInTheDocument();
    expect(screen.getByText('EPG totals')).toBeInTheDocument();
  });

  it('keeps Stats fallback copy explicit when data is unavailable', () => {
    (configHooks.useStats as jest.Mock).mockReturnValue({
      data: undefined,
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    renderPage(<Stats />);

    expect(screen.getByText(/stats are not available yet/i)).toBeInTheDocument();
  });

  it('stacks Stats summary and breakdown groups vertically on phone widths', () => {
    const theme = createAppTheme('light');

    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      isPhone: true,
      isDesktop: false,
      isWideDesktop: false,
    });

    render(
      <ThemeProvider theme={theme}>
        <TestMemoryRouter>
          <Stats />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByTestId('stats-summary-metrics')).toHaveStyle({ flexDirection: 'column' });
    expect(screen.getByTestId('stats-breakdown-groups')).toHaveStyle({ flexDirection: 'column' });
  });

  it('renders Channels as a legacy recovery surface instead of a blank page', () => {
    renderPage(<Channels />);

    const headerCopy = screen.getByTestId('page-header-copy');
    const sectionCopy = screen.getByTestId('content-section-copy');
    const recoveryStatus = screen.getByText(/legacy route: recover channel work from tv channels/i);
    const supportCopy = screen.getByText(/use the supported inventory routes instead of this older entry point/i);
    const primaryAction = screen.getByRole('button', { name: 'Open TV Channels' });

    expect(screen.getByRole('heading', { level: 1, name: 'Channels' })).toBeInTheDocument();
    expect(within(headerCopy).getByText(/route is now a recovery point for the supported channel inventory/i)).toBeInTheDocument();
    expect(within(sectionCopy).getByText(/open tv channels for the primary inventory path/i)).toBeInTheDocument();
    expect(within(sectionCopy).getByText(/acestream channels remains separate when you need source-level context/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Go to the current channel views' })).toBeInTheDocument();
    expect(primaryAction).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Open Acestream Channels' })).not.toBeInTheDocument();
    expect(headerCopy.compareDocumentPosition(sectionCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(sectionCopy.compareDocumentPosition(recoveryStatus) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(recoveryStatus.compareDocumentPosition(primaryAction) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(primaryAction.compareDocumentPosition(supportCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('navigates from Channels to TV Channels with the recovery action', () => {
    renderLegacyPageWithRoutes('/channels', <Channels />);

    fireEvent.click(screen.getByRole('button', { name: 'Open TV Channels' }));

    expect(screen.getByText('TV Channels destination')).toBeInTheDocument();
  });

  it('renders ChannelDetail as a legacy recovery surface with TV Channels and EPG actions', () => {
    renderPage(<ChannelDetail />);

    const headerCopy = screen.getByTestId('page-header-copy');
    const sectionCopy = screen.getByTestId('content-section-copy');
    const recoveryStatus = screen.getByText(/legacy detail route: reopen the item from tv channels or epg/i);
    const supportCopy = screen.getByText(/use a current list first, then return to the detail screen from there/i);
    const primaryAction = screen.getByRole('button', { name: 'Open TV Channels' });

    expect(screen.getByRole('heading', { level: 1, name: 'Channel detail' })).toBeInTheDocument();
    expect(within(headerCopy).getByText(/detail route is no longer active/i)).toBeInTheDocument();
    expect(within(headerCopy).getByText(/reopen the item from a supported list/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Choose a supported channel workflow' })).toBeInTheDocument();
    expect(primaryAction).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open EPG' })).toBeInTheDocument();
    expect(headerCopy.compareDocumentPosition(sectionCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(sectionCopy.compareDocumentPosition(recoveryStatus) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(recoveryStatus.compareDocumentPosition(primaryAction) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(primaryAction.compareDocumentPosition(supportCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('navigates from ChannelDetail to supported TV Channels and EPG flows', () => {
    const view = renderLegacyPageWithRoutes('/channels/legacy-id', <ChannelDetail />);

    fireEvent.click(screen.getByRole('button', { name: 'Open TV Channels' }));
    expect(screen.getByText('TV Channels destination')).toBeInTheDocument();

    view.unmount();

    renderLegacyPageWithRoutes('/channels/legacy-id', <ChannelDetail />);
    fireEvent.click(screen.getByRole('button', { name: 'Open EPG' }));
    expect(screen.getByText('EPG destination')).toBeInTheDocument();
  });

  it('renders SearchNew as a legacy recovery surface for the current search workflow', () => {
    renderPage(<SearchNew />);

    const headerCopy = screen.getByTestId('page-header-copy');
    const sectionCopy = screen.getByTestId('content-section-copy');
    const recoveryStatus = screen.getByText(/legacy route: continue from the main search workflow/i);
    const supportCopy = screen.getByText(/use the current search page instead of this older entry point/i);
    const primaryAction = screen.getByRole('button', { name: 'Open Search' });

    expect(screen.getByRole('heading', { level: 1, name: 'Search' })).toBeInTheDocument();
    expect(within(headerCopy).getByText(/route moved/i)).toBeInTheDocument();
    expect(within(headerCopy).getByText(/continue in search from the supported path/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Continue in the supported search flow' })).toBeInTheDocument();
    expect(primaryAction).toBeInTheDocument();
    expect(headerCopy.compareDocumentPosition(sectionCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(sectionCopy.compareDocumentPosition(recoveryStatus) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(recoveryStatus.compareDocumentPosition(primaryAction) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(primaryAction.compareDocumentPosition(supportCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('navigates from SearchNew to the supported search flow', () => {
    renderLegacyPageWithRoutes('/search-new', <SearchNew />);

    fireEvent.click(screen.getByRole('button', { name: 'Open Search' }));

    expect(screen.getByText('Search destination')).toBeInTheDocument();
  });
});

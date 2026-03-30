import React, { act } from 'react';
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
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';
import * as playlistHooks from '../hooks/usePlaylists';
import * as warpHooks from '../hooks/useWarp';
import { configService } from '../services/configService';
import { WarpMode } from '../types/warpTypes';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

const actualRouterDom = jest.requireActual('react-router-dom');

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
jest.mock('../hooks/usePlaylists');
jest.mock('../hooks/useWarp');
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
  (routerDom.useNavigate as jest.Mock).mockImplementation(() => actualRouterDom.useNavigate());

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

  (configHooks.useBaseUrl as jest.Mock).mockReturnValue({ data: 'acestream://', isLoading: false });
  (configHooks.useUpdateBaseUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
  (configHooks.useAceEngineUrl as jest.Mock).mockReturnValue({ data: 'http://localhost:6878', isLoading: false });
  (configHooks.useUpdateAceEngineUrl as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
  (configHooks.useRescrapeInterval as jest.Mock).mockReturnValue({ data: 24, isLoading: false });
  (configHooks.useUpdateRescrapeInterval as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
  (configHooks.useAddPid as jest.Mock).mockReturnValue({ data: true, isLoading: false });
  (configHooks.useUpdateAddPid as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
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
  (warpHooks.useWarpConnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
  (warpHooks.useWarpDisconnect as jest.Mock).mockReturnValue({ mutate: jest.fn(), isLoading: false });
  (warpHooks.useWarpSetMode as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
  (warpHooks.useWarpRegisterLicense as jest.Mock).mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });

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

  it('renders Health with a shared page title and operational sections', () => {
    renderPage(<Health />);

    expect(screen.getByRole('heading', { level: 1, name: 'Health' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Status overview' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'System totals' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/healthy/i);
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

    await act(async () => {
      fireEvent.click(appIdToggle);
      await Promise.resolve();
    });

    await waitFor(() => expect(configService.updateAppId).toHaveBeenCalledWith(true));
    await waitFor(() => expect(appIdToggle).not.toBeDisabled());
    expect(appIdToggle).not.toBeChecked();
    expect(screen.getByText(/failed to update appid setting/i)).toBeInTheDocument();
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

    const tvView = renderNotFoundWithRoutes('/unsupported-route');
    fireEvent.click(screen.getByRole('button', { name: 'Open TV Channels' }));
    expect(screen.getByText('TV Channels destination')).toBeInTheDocument();

    tvView.unmount();

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
    const channelsRoute = renderAppAtRoute(['/channels']);
    expect(screen.getByRole('heading', { level: 1, name: 'Channels' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open TV Channels' })).toBeInTheDocument();
    channelsRoute.unmount();

    const channelDetailRoute = renderAppAtRoute(['/channels/legacy-id']);
    expect(screen.getByRole('heading', { level: 1, name: 'Channel detail' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open TV Channels' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open EPG' })).toBeInTheDocument();
    channelDetailRoute.unmount();

    renderAppAtRoute(['/search-new']);
    expect(screen.getByRole('heading', { level: 1, name: 'Search' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Open Search' })).toBeInTheDocument();
  });

  it('renders Channels as a legacy recovery surface instead of a blank page', () => {
    renderPage(<Channels />);

    const headerCopy = screen.getByTestId('page-header-copy');
    const sectionCopy = screen.getByTestId('content-section-copy');
    const recoveryStatus = screen.getByText(/legacy route: recover channel work from tv channels/i);
    const supportCopy = screen.getByText(/use the supported inventory routes instead of this older entry point/i);
    const primaryAction = screen.getByRole('button', { name: 'Open TV Channels' });

    expect(screen.getByRole('heading', { level: 1, name: 'Channels' })).toBeInTheDocument();
    expect(within(headerCopy).getByText(/route now redirects to the supported channel inventory/i)).toBeInTheDocument();
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

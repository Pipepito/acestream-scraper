import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import * as routerDom from 'react-router-dom';
import { Route, Routes } from 'react-router-dom';
import Playlist from '../pages/Playlist';
import WarpPage from '../pages/WARP';
import NotFound from '../pages/NotFound';
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
    (playlistHooks.usePlaylistChannelSummary as jest.Mock).mockReturnValue({ data: undefined });

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













  it('renders Playlist with the shared header and its options', () => {
    renderPage(<Playlist />);

    expect(screen.getByRole('heading', { level: 1, name: 'Playlist' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Your playlist' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Group filters' })).toBeInTheDocument();
  });

  it('renders WARP actions inside the shared responsive header actions area', () => {
    renderPage(<WarpPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'WARP' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Connect' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Disconnect' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Connection details' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'WARP status' })).toHaveTextContent(/connected/i);
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
    expect(screen.getByRole('status', { name: 'WARP status' })).toHaveTextContent(/mode dot/i);
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



});

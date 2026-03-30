import React, { act } from 'react';
import { render, screen, within, waitFor, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Health from '../pages/Health';
import Playlist from '../pages/Playlist';
import Settings from '../pages/Settings';
import WarpPage from '../pages/WARP';
import NotFound from '../pages/NotFound';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as configHooks from '../hooks/useConfig';
import * as playlistHooks from '../hooks/usePlaylists';
import * as warpHooks from '../hooks/useWarp';
import { configService } from '../services/configService';
import { WarpMode } from '../types/warpTypes';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

jest.mock('../bootstrap/AppBootstrap', () => {
  const actual = jest.requireActual('../bootstrap/AppBootstrap');

  return {
    ...actual,
    useAppThemeMode: jest.fn(),
  };
});

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

beforeEach(() => {
  jest.clearAllMocks();

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

  it('renders NotFound with the shared page skeleton and recovery action', () => {
    renderPage(<NotFound />);

    expect(screen.getByRole('heading', { level: 1, name: 'Page not found' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Get back on track' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Return to dashboard' })).toBeInTheDocument();
  });
});

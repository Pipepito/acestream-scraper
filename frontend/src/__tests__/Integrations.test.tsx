import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import Integrations from '../pages/Integrations';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockPublicUrl = jest.fn();
const mockUpdatePublicBaseUrl = jest.fn();
const mockCapabilities = jest.fn();
const mockSessions = jest.fn();
const mockPlayers = jest.fn();
const mockStatus = jest.fn();
const mockDelete = jest.fn();
const mockCommand = jest.fn();
const mockTest = jest.fn();
const mockServers = jest.fn();
const mockServerStatus = jest.fn();
const mockCreateServer = jest.fn();
const mockUpdateServer = jest.fn();
const mockDeleteServer = jest.fn();
const mockTestServer = jest.fn();
const mockConnectServer = jest.fn();
const mockRefreshServer = jest.fn();
const mockDisconnectServer = jest.fn();
const mockTunerStatus = jest.fn();
const mockTunerSettings = jest.fn();
const mockUpdateTunerSettings = jest.fn();
const mockInvalidateQueries = jest.fn();

jest.mock('../hooks/useSystemServices', () => ({ usePublicUrl: () => mockPublicUrl(), PUBLIC_URL_QUERY_KEY: ['system', 'public-url'] }));
jest.mock('../services/configService', () => ({ configService: { updatePublicBaseUrl: (...a: unknown[]) => mockUpdatePublicBaseUrl(...a) } }));
jest.mock('../hooks/usePlayer', () => ({ usePlayerCapabilities: () => mockCapabilities(), usePlayerSessions: () => mockSessions() }));
jest.mock('../hooks/useRemotePlayers', () => ({
  useRemotePlayers: () => mockPlayers(),
  useRemotePlayerStatus: (id: number) => mockStatus(id),
  useDeleteRemotePlayer: () => ({ mutateAsync: mockDelete, isPending: false }),
  useRemotePlayerCommand: () => ({ mutateAsync: mockCommand, isPending: false }),
  useCreateRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useUpdateRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
  useTestRemotePlayer: () => ({ mutateAsync: mockTest, isPending: false }),
  useScanRemotePlayers: () => ({ mutateAsync: jest.fn(), isPending: false, data: undefined }),
  useScanDefault: () => ({ data: { cidr: '192.168.1.0/24', hint: '' } }),
  usePlayOnRemotePlayer: () => ({ mutateAsync: jest.fn(), isPending: false }),
}));
jest.mock('../hooks/useMediaServers', () => ({
  MEDIA_SERVERS_QUERY_KEY: ['media-servers'],
  useMediaServers: () => mockServers(),
  useMediaServerStatus: (id: number) => mockServerStatus(id),
  useCreateMediaServer: () => ({ mutateAsync: mockCreateServer, isPending: false }),
  useUpdateMediaServer: () => ({ mutateAsync: mockUpdateServer, isPending: false }),
  useDeleteMediaServer: () => ({ mutateAsync: mockDeleteServer, isPending: false }),
  useTestMediaServer: () => ({ mutateAsync: mockTestServer, isPending: false }),
  useConnectMediaServer: () => ({ mutateAsync: mockConnectServer, isPending: false }),
  useRefreshMediaServer: () => ({ mutateAsync: mockRefreshServer, isPending: false }),
  useDisconnectMediaServer: () => ({ mutateAsync: mockDisconnectServer, isPending: false }),
}));
jest.mock('../hooks/useTuner', () => ({
  useTunerStatus: () => mockTunerStatus(),
  useTunerSettings: () => mockTunerSettings(),
  useUpdateTunerSettings: () => ({ mutateAsync: mockUpdateTunerSettings, isPending: false }),
}));
jest.mock('../hooks/useBaseUrls', () => ({ useBaseUrls: () => ({ data: [], isLoading: false }) }));
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => ({ data: [], isLoading: false }) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: () => ({ data: { items: [] }, isLoading: false }) }));
jest.mock('@tanstack/react-query', () => ({ ...jest.requireActual('@tanstack/react-query'), useQueryClient: () => ({ invalidateQueries: mockInvalidateQueries }) }));

const PLEX_STEPS = [
  'In Plex Web open Settings > Live TV & DVR and choose Set Up Plex Tuner (Plex Pass is required).',
  'Click "Don\'t see your HDHomeRun device? Enter its network address manually" and paste the tuner address.',
  'Pick any country, then choose "Have an XMLTV guide on your server?" and paste the guide URL.',
  'Review the channel mapping and finish. After channels change here, use Manage Channels > Rescan in Plex.',
];

const tunerStatus = (overrides: Record<string, unknown> = {}) => ({
  data: {
    channel_count: 12,
    renumbered: [],
    overflow: 0,
    device_id: 'ACE12345',
    urls: {
      tuner: 'http://192.168.1.10:8000/tuner',
      lineup: 'http://192.168.1.10:8000/tuner/lineup.json',
      guide: 'http://192.168.1.10:8000/tuner/guide.xml',
      playlist: 'http://192.168.1.10:8000/tuner/playlist.m3u',
      epg: 'http://192.168.1.10:8000/tuner/epg.xml',
      stream_template: 'http://192.168.1.10:8000/tuner/stream/{content_id}.ts',
    },
    ffmpeg_available: true,
    allowed_networks: ['192.168.0.0/16'],
    client_ip: '192.168.1.5',
    peer: '192.168.1.5',
    client_allowed: true,
    client_source: 'direct',
    warnings: [],
    recent_denials: [],
    ...overrides,
  },
});

const renderPage = () =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter>
        <Integrations />
      </TestMemoryRouter>
    </ThemeProvider>
  );

describe('Integrations page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPublicUrl.mockReturnValue({ data: { url: 'http://localhost:8000', source: 'request', warnings: ['localhost', 'unset'] }, isLoading: false });
    mockCapabilities.mockReturnValue({ data: { ffmpeg_available: true, ffmpeg_path: '/opt/ffmpeg/bin/ffmpeg', max_sessions: 3, hls_dir: '/tmp/x' } });
    mockSessions.mockReturnValue({ data: { sessions: [] } });
    mockPlayers.mockReturnValue({
      data: [{ id: 1, name: 'Living room', kind: 'vlc', host: '192.168.1.20', port: 8080, username: null, base_url_id: null, has_password: true, created_at: '', updated_at: '' }],
      isLoading: false,
    });
    mockStatus.mockReturnValue({ data: { state: 'playing', title: 'Arena TV', position_s: 61, length_s: null, volume_pct: 50, message: null }, error: null });
    mockServers.mockReturnValue({
      data: [
        {
          id: 1, kind: 'jellyfin', name: 'Jelly', base_url: 'http://192.168.1.12:8096', tuner_mode: 'hdhomerun', enabled: true,
          auto_refresh: true, has_api_key: true, connected: true, tuner_host_id: 'th-1', listing_provider_id: 'lp-1', dvr_key: null,
          last_sync_at: new Date(Date.now() - 12 * 60_000).toISOString(), last_sync_status: 'ok', last_error: null,
          server_version: '10.9.11', created_at: '', updated_at: '',
        },
        {
          id: 2, kind: 'plex', name: 'Plex', base_url: 'http://192.168.1.13:32400', tuner_mode: 'hdhomerun', enabled: true,
          auto_refresh: true, has_api_key: false, connected: true, tuner_host_id: null, listing_provider_id: null, dvr_key: 'dvr-9',
          last_sync_at: null, last_sync_status: 'manual', last_error: null, server_version: '1.40.0', created_at: '', updated_at: '',
        },
      ],
      isLoading: false,
    });
    mockServerStatus.mockImplementation((id: number) =>
      id === 1
        ? { data: { connected: true, channel_count: 42, refresh_state: 'Idle', last_result: 'Completed', steps: [], paste: {}, error: null } }
        : {
            data: {
              connected: true, channel_count: null, refresh_state: null, last_result: null, steps: PLEX_STEPS,
              paste: {
                tuner_address: '192.168.1.10:8000/tuner',
                guide_url: 'http://192.168.1.10:8000/tuner/guide.xml',
                device_id: 'ACE12345',
              },
              error: null,
            },
          }
    );
    mockTunerStatus.mockReturnValue(tunerStatus());
    mockTunerSettings.mockReturnValue({ data: { friendly_name: 'AceStream Tuner', tuner_count: 4, max_channels: 450, only_online: false }, isLoading: false });
  });

  it('renders the page skeleton with the four sections', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1, name: 'Integrations' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)).toEqual([
      'Public address',
      'Web player',
      'Remote players',
      'Media servers',
    ]);
    expect(screen.getByRole('status', { name: 'Integration summary' })).toHaveTextContent('Players1');
    expect(screen.getByRole('status', { name: 'Integration summary' })).toHaveTextContent('Media servers2');
  });

  it('warns about a localhost public address and saves a new one', async () => {
    mockUpdatePublicBaseUrl.mockResolvedValue(undefined);
    renderPage();
    const section = screen.getByRole('region', { name: 'Public address' });
    const warnings = within(section).getAllByRole('alert');
    expect(warnings).toHaveLength(2);
    expect(warnings[0]).toHaveTextContent(/only works from this machine/);
    fireEvent.change(within(section).getByRole('textbox', { name: 'Public address' }), { target: { value: 'http://192.168.1.10:8000' } });
    fireEvent.click(within(section).getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(mockUpdatePublicBaseUrl).toHaveBeenCalledWith('http://192.168.1.10:8000'));
    // The Plex cards paste absolute URLs built from this address, so their
    // status queries have to be re-read too.
    await waitFor(() => expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ['media-servers'] }));
  });

  it('reports a failed load instead of showing an empty list or claiming ffmpeg is ready', () => {
    mockServers.mockReturnValue({ data: undefined, isLoading: false, isError: true, error: new Error('Request failed'), refetch: jest.fn() });
    mockPlayers.mockReturnValue({ data: undefined, isLoading: false, isError: true, error: new Error('Request failed'), refetch: jest.fn() });
    mockCapabilities.mockReturnValue({ data: undefined, isError: true, error: new Error('Request failed') });
    renderPage();

    const servers = screen.getByRole('region', { name: 'Media servers' });
    expect(within(servers).getByText('Unable to load media servers')).toBeInTheDocument();
    expect(within(servers).queryByText('No media servers yet')).not.toBeInTheDocument();
    expect(within(servers).getByRole('button', { name: 'Try again' })).toBeInTheDocument();

    const players = screen.getByRole('region', { name: 'Remote players' });
    expect(within(players).getByText('Unable to load players')).toBeInTheDocument();
    expect(within(players).queryByText('No players yet')).not.toBeInTheDocument();

    const web = screen.getByRole('region', { name: 'Web player' });
    expect(within(web).getByText('Unable to check the web player')).toBeInTheDocument();
    expect(within(web).queryByText(/ffmpeg ready/)).not.toBeInTheDocument();
  });

  it('does not claim ffmpeg is ready before the capabilities answer', () => {
    mockCapabilities.mockReturnValue({ data: undefined, isError: false, error: null });
    renderPage();
    const web = screen.getByRole('region', { name: 'Web player' });
    expect(within(web).getByText('Checking ffmpeg…')).toBeInTheDocument();
    expect(within(web).queryByText(/ffmpeg ready/)).not.toBeInTheDocument();
  });

  it('shows player cards with live status, transport and a menu with confirm on delete', async () => {
    mockDelete.mockResolvedValue(undefined);
    renderPage();
    const card = screen.getByRole('group', { name: 'Player Living room' });
    expect(within(card).getByText(/Playing.*Arena TV/)).toBeInTheDocument();
    fireEvent.click(within(card).getByRole('button', { name: 'Pause Living room' }));
    await waitFor(() => expect(mockCommand).toHaveBeenCalledWith({ id: 1, command: 'pause' }));
    fireEvent.click(within(card).getByRole('button', { name: 'More actions for Living room' }));
    expect(screen.getByRole('menuitem', { name: 'Send channel…' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete Living room?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(mockDelete).toHaveBeenCalledWith(1));
  });

  it('keeps the volume where the user left it instead of snapping back to the last poll', async () => {
    mockCommand.mockResolvedValue(undefined);
    renderPage();
    const card = screen.getByRole('group', { name: 'Player Living room' });
    const slider = within(card).getByRole('slider', { name: 'Volume Living room' }) as HTMLInputElement;
    expect(slider.value).toBe('50');

    fireEvent.change(slider, { target: { value: '75' } });
    await waitFor(() => expect(mockCommand).toHaveBeenCalledWith({ id: 1, command: 'volume', value: 75 }));
    // The 5 s poll still reports 50; the slider must not jump back under the user.
    expect(slider.value).toBe('75');
  });

  it('opens the add dialog and runs Test connection with the guided VLC message', async () => {
    mockTest.mockResolvedValue({
      reachable: true,
      authenticated: false,
      version: null,
      message: 'no password',
      hint: "VLC's web interface has no password. In VLC: Tools > Preferences",
      tuner_access: { addresses: ['192.168.1.20'], allowed: true },
    });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Add player' }));
    const dialog = await screen.findByRole('dialog', { name: 'Add player' });
    fireEvent.change(within(dialog).getByRole('textbox', { name: 'Name' }), { target: { value: 'Bedroom' } });
    fireEvent.change(within(dialog).getByRole('textbox', { name: 'Host' }), { target: { value: '192.168.1.21' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }));
    expect(await within(dialog).findByText(/Tools > Preferences/)).toBeInTheDocument();
    expect(mockTest).toHaveBeenCalledWith(expect.objectContaining({ kind: 'vlc', host: '192.168.1.21', port: 8080 }));
  });

  it('shows a connected Jellyfin card with two visible actions and confirms Disconnect and Delete', async () => {
    mockDisconnectServer.mockResolvedValue(undefined);
    mockDeleteServer.mockResolvedValue(undefined);
    renderPage();
    const card = screen.getByRole('group', { name: 'Media server Jelly' });
    expect(within(card).getByText('Connected')).toBeInTheDocument();
    expect(within(card).getByText('Guide up to date')).toBeInTheDocument();
    expect(within(card).getByText(/42 channels/)).toBeInTheDocument();
    expect(within(card).getByRole('button', { name: 'Refresh now Jelly' })).toBeEnabled();

    fireEvent.click(within(card).getByRole('button', { name: 'More actions for Jelly' }));
    const menu = screen.getByRole('menu');
    expect(within(menu).getAllByRole('menuitem').map((item) => item.textContent)).toEqual(['Edit', 'Test connection', 'Delete']);
    fireEvent.keyDown(menu, { key: 'Escape' });

    fireEvent.click(within(card).getByRole('button', { name: 'Disconnect Jelly' }));
    const disconnect = await screen.findByRole('dialog', { name: 'Disconnect Jelly?' });
    expect(disconnect).toHaveTextContent(/removes the AceStream tuner and its guide provider from Jellyfin/);
    fireEvent.click(within(disconnect).getByRole('button', { name: 'Disconnect' }));
    await waitFor(() => expect(mockDisconnectServer).toHaveBeenCalledWith(1));

    fireEvent.click(within(card).getByRole('button', { name: 'More actions for Jelly' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    expect(await screen.findByRole('dialog', { name: 'Delete Jelly?' })).toBeInTheDocument();
  });

  it('shows the Plex setup steps, copy buttons and a disabled refresh without a token', async () => {
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
    mockDisconnectServer.mockResolvedValue(undefined);
    renderPage();
    const card = screen.getByRole('group', { name: 'Media server Plex' });
    expect(within(card).getByText('Rescan the guide in Plex')).toBeInTheDocument();
    expect(within(card).getByText(/Set Up Plex Tuner/)).toBeInTheDocument();
    expect(within(card).getAllByRole('listitem')).toHaveLength(PLEX_STEPS.length);
    expect(within(card).getByRole('button', { name: 'Refresh now Plex' })).toBeDisabled();

    fireEvent.click(within(card).getByRole('button', { name: 'Copy tuner address' }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('192.168.1.10:8000/tuner'));
    fireEvent.click(within(card).getByRole('button', { name: 'Copy guide URL' }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('http://192.168.1.10:8000/tuner/guide.xml'));

    // Plex disconnect only forgets the DVR key here, so it does not confirm.
    fireEvent.click(within(card).getByRole('button', { name: 'Disconnect Plex' }));
    await waitFor(() => expect(mockDisconnectServer).toHaveBeenCalledWith(2));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('offers the tuner mode radio only for Jellyfin and shows the probe message', async () => {
    mockTestServer.mockResolvedValue({
      reachable: true,
      authenticated: true,
      version: '10.9.11',
      message: 'Jellyfin is reachable',
      tuner_access: { addresses: ['192.168.1.12'], allowed: false },
    });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Add media server' }));
    const dialog = await screen.findByRole('dialog', { name: 'Add media server' });
    expect(within(dialog).getByRole('radiogroup', { name: 'Channels reach Jellyfin as' })).toBeInTheDocument();

    fireEvent.change(within(dialog).getByRole('textbox', { name: 'Address' }), { target: { value: 'http://192.168.1.12:8096' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Test connection' }));
    expect(await within(dialog).findByText(/Jellyfin is reachable/)).toBeInTheDocument();
    expect(within(dialog).getByText(/is outside TUNER_ALLOWED_NETWORKS/)).toBeInTheDocument();

    fireEvent.mouseDown(within(dialog).getByRole('combobox', { name: 'Media server' }));
    fireEvent.click(screen.getByRole('option', { name: 'Plex' }));
    expect(within(dialog).queryByRole('radiogroup')).not.toBeInTheDocument();
  });

  it('explains an ineffective allowlist and the requests it denied', () => {
    mockTunerStatus.mockReturnValue(
      tunerStatus({
        warnings: ['TUNER_ALLOWLIST_INEFFECTIVE'],
        recent_denials: [{ client_ip: '203.0.113.9', peer: '203.0.113.9', path: '/tuner/lineup.json', at: 1 }],
      })
    );
    renderPage();
    const section = screen.getByRole('region', { name: 'Public address' });
    const alerts = within(section).getAllByRole('alert');
    expect(alerts).toHaveLength(4);
    const text = alerts.map((alert) => alert.textContent).join(' | ');
    expect(text).toMatch(/hides real client addresses/);
    expect(text).toMatch(/Requests from 203\.0\.113\.9 were denied/);
    expect(text).toMatch(/\/tuner\/lineup\.json/);
  });

  it('warns instead of claiming success when connecting Plex leaves it without a DVR', async () => {
    const plex = {
      id: 2, kind: 'plex', name: 'Plex', base_url: 'http://192.168.1.13:32400', tuner_mode: 'hdhomerun', enabled: true,
      auto_refresh: true, has_api_key: false, connected: false, tuner_host_id: null, listing_provider_id: null, dvr_key: null,
      last_sync_at: null, last_sync_status: 'manual', last_error: null, server_version: '1.40.0', created_at: '', updated_at: '',
    };
    mockServers.mockReturnValue({ data: [plex], isLoading: false });
    mockConnectServer.mockResolvedValue(plex);
    renderPage();
    const card = screen.getByRole('group', { name: 'Media server Plex' });
    fireEvent.click(within(card).getByRole('button', { name: 'Connect Plex' }));
    await waitFor(() => expect(mockConnectServer).toHaveBeenCalledWith(2));
    expect(await screen.findByText(/Plex has no DVR using this tuner yet/)).toBeInTheDocument();
    expect(screen.queryByText('Plex is connected.')).not.toBeInTheDocument();
  });

  it('says a connected server is connected', async () => {
    const jelly = {
      id: 1, kind: 'jellyfin', name: 'Jelly', base_url: 'http://192.168.1.12:8096', tuner_mode: 'hdhomerun', enabled: true,
      auto_refresh: true, has_api_key: true, connected: false, tuner_host_id: null, listing_provider_id: null, dvr_key: null,
      last_sync_at: null, last_sync_status: 'never', last_error: null, server_version: '10.9.11', created_at: '', updated_at: '',
    };
    mockServers.mockReturnValue({ data: [jelly], isLoading: false });
    mockConnectServer.mockResolvedValue({ ...jelly, connected: true, tuner_host_id: 'th-1', listing_provider_id: 'lp-1' });
    renderPage();
    const card = screen.getByRole('group', { name: 'Media server Jelly' });
    fireEvent.click(within(card).getByRole('button', { name: 'Connect Jelly' }));
    expect(await screen.findByText('Jelly is connected.')).toBeInTheDocument();
  });

  it('keeps tuner numbers the API would reject out of the request', async () => {
    renderPage();
    const section = screen.getByRole('region', { name: 'Media servers' });
    fireEvent.click(within(section).getByRole('button', { name: 'Tuner settings' }));
    const streams = within(section).getByRole('spinbutton', { name: 'Streams at once' });
    const save = within(section).getByRole('button', { name: 'Save tuner settings' });

    fireEvent.change(streams, { target: { value: '' } });
    expect(within(section).getByText('Enter a whole number between 1 and 16.')).toBeInTheDocument();
    expect(save).toBeDisabled();

    fireEvent.change(streams, { target: { value: '20' } });
    expect(save).toBeDisabled();

    fireEvent.change(within(section).getByRole('spinbutton', { name: 'Most channels to publish' }), { target: { value: '0' } });
    expect(within(section).getByText('Enter a whole number between 1 and 1000.')).toBeInTheDocument();

    fireEvent.change(streams, { target: { value: '2' } });
    fireEvent.change(within(section).getByRole('spinbutton', { name: 'Most channels to publish' }), { target: { value: '300' } });
    expect(save).toBeEnabled();
    fireEvent.click(save);
    await waitFor(() => expect(mockUpdateTunerSettings).toHaveBeenCalledWith(expect.objectContaining({ tuner_count: 2, max_channels: 300 })));
  });

  it('saves the tuner settings from the collapsible block', async () => {
    mockUpdateTunerSettings.mockResolvedValue({ friendly_name: 'Living room tuner', tuner_count: 4, max_channels: 450, only_online: false });
    renderPage();
    const section = screen.getByRole('region', { name: 'Media servers' });
    fireEvent.click(within(section).getByRole('button', { name: 'Tuner settings' }));
    fireEvent.change(within(section).getByRole('textbox', { name: 'Tuner name' }), { target: { value: 'Living room tuner' } });
    fireEvent.click(within(section).getByRole('button', { name: 'Save tuner settings' }));
    await waitFor(() =>
      expect(mockUpdateTunerSettings).toHaveBeenCalledWith(
        expect.objectContaining({ friendly_name: 'Living room tuner', tuner_count: 4, max_channels: 450, only_online: false })
      )
    );
  });
});

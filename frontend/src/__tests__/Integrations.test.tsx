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
jest.mock('../hooks/useBaseUrls', () => ({ useBaseUrls: () => ({ data: [], isLoading: false }) }));
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => ({ data: [], isLoading: false }) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: () => ({ data: { items: [] }, isLoading: false }) }));
jest.mock('@tanstack/react-query', () => ({ ...jest.requireActual('@tanstack/react-query'), useQueryClient: () => ({ invalidateQueries: jest.fn() }) }));

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
  });

  it('renders the page skeleton with the three sections', () => {
    renderPage();
    expect(screen.getByRole('heading', { level: 1, name: 'Integrations' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent)).toEqual(['Public address', 'Web player', 'Remote players']);
    expect(screen.getByRole('status', { name: 'Integration summary' })).toHaveTextContent('Players1');
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
});

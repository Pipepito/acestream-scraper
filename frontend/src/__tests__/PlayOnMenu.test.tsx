import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PlayOnMenu from '../components/player/PlayOnMenu';
import { ApiError } from '../services/apiErrors';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { castService } from '../services/castService';

const mockPlayers = jest.fn();
const mockPlay = jest.fn();
const mockAccess = jest.fn();
jest.mock('../components/access/AccessContext', () => ({ useAccess: () => mockAccess() }));
jest.mock('../services/castService');
jest.mock('../services/browserCast', () => ({ loadBrowserCast: jest.fn().mockResolvedValue(false) }));
jest.mock('../hooks/useRemotePlayers', () => ({
  useRemotePlayers: () => mockPlayers(),
  usePlayOnRemotePlayer: () => ({ mutateAsync: mockPlay, isPending: false }),
}));

const mount = () =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter>
        <PlayOnMenu contentId={'a'.repeat(40)} title="Arena TV" />
      </TestMemoryRouter>
    </ThemeProvider></QueryClientProvider>
  );

describe('PlayOnMenu', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAccess.mockReturnValue(null);
  });

  it('lists server TVs alongside players and starts casting without opening the web player', async () => {
    mockAccess.mockReturnValue({ status: { mode: 'open', permissions: [] } });
    mockPlayers.mockReturnValue({ data: [], isLoading: false });
    jest.mocked(castService.capabilities).mockResolvedValue({ server_devices: true, media_url_configured: true, home_connection: true, compatibility_conversion: true, message: '', media_url: 'http://192.168.1.10:8000' });
    jest.mocked(castService.devices).mockResolvedValue([{ id: 'tv-id', name: 'Living room TV', model: 'Google Cast' }]);
    jest.mocked(castService.start).mockResolvedValue({ id: 'session' } as Awaited<ReturnType<typeof castService.start>>);
    mount();
    expect(castService.capabilities).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: /Living room TV/ }));
    await waitFor(() => expect(castService.start).toHaveBeenCalledWith({ content_id: 'a'.repeat(40), device_id: 'tv-id', audio_index: null, subtitle_index: null, compatibility: false, replace: false }));
    expect(await screen.findByText('Casting Arena TV to Living room TV.')).toBeInTheDocument();
    expect(mockPlay).not.toHaveBeenCalled();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('offers discovery when empty and never silently replaces playback on a busy TV', async () => {
    mockAccess.mockReturnValue({ status: { mode: 'open', permissions: [] } });
    mockPlayers.mockReturnValue({ data: [], isLoading: false });
    jest.mocked(castService.capabilities).mockResolvedValue({ server_devices: true, media_url_configured: true, home_connection: true, compatibility_conversion: true, message: '', media_url: '' });
    jest.mocked(castService.devices).mockResolvedValue([]);
    jest.mocked(castService.sessions).mockResolvedValue([]);
    jest.mocked(castService.discover).mockResolvedValue([{ id: 'tv-id', name: 'Living room TV', model: 'Google Cast' }]);
    jest.mocked(castService.start).mockRejectedValue(new Error('TV is busy'));
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Find TVs' }));
    fireEvent.click(await screen.findByRole('menuitem', { name: /Living room TV/ }));
    expect(await screen.findByRole('dialog', { name: 'Cast live video' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'Replace playback already on this TV' })).not.toBeChecked();
    expect(castService.start).toHaveBeenCalledTimes(1);
  });

  it('lists players and sends the channel', async () => {
    mockPlayers.mockReturnValue({
      data: [
        { id: 1, name: 'Living room', kind: 'vlc' },
        { id: 2, name: 'Kitchen', kind: 'kodi' },
      ],
      isLoading: false,
    });
    mockPlay.mockResolvedValue({ url: 'http://x' });
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
    await waitFor(() => expect(mockPlay).toHaveBeenCalledWith({ id: 1, contentId: 'a'.repeat(40), title: 'Arena TV' }));
    expect(await screen.findByText('Sent Arena TV to Living room.')).toBeInTheDocument();
  });

  it('warns instead of confirming when the link cannot reach the player', async () => {
    mockPlayers.mockReturnValue({ data: [{ id: 1, name: 'Living room', kind: 'vlc' }], isLoading: false });
    mockPlay.mockResolvedValue({ url: 'http://localhost:8000/tuner/stream/x.ts', warnings: ['localhost'] });
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Sent Arena TV to Living room.');
    expect(alert).toHaveTextContent(/means the player itself/);
    expect(alert.className).toContain('Warning');
  });

  it('points at Remote players setup when there are no players', () => {
    mockPlayers.mockReturnValue({ data: [], isLoading: false });
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    expect(screen.getByRole('menuitem', { name: /Add a player/ })).toHaveAttribute('href', '/integrations/remote-players');
  });

  it('explains a wrong password without the API-token notice', async () => {
    mockPlayers.mockReturnValue({ data: [{ id: 1, name: 'Living room', kind: 'vlc' }], isLoading: false });
    mockPlay.mockRejectedValue(
      new ApiError({
        message: 'nope',
        status: 502,
        kind: 'server',
        canRetry: true,
        code: 'REMOTE_PLAYER_AUTH',
        context: { kind: 'wrong_password' },
      })
    );
    const listener = jest.fn();
    window.addEventListener('acestream:api-token-required', listener);
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Living room (VLC)' }));
    expect(await screen.findByText(/Check the password/)).toBeInTheDocument();
    expect(listener).not.toHaveBeenCalled();
    window.removeEventListener('acestream:api-token-required', listener);
  });
});

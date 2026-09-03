import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PlayOnMenu from '../components/player/PlayOnMenu';
import { ApiError } from '../services/apiErrors';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockPlayers = jest.fn();
const mockPlay = jest.fn();
jest.mock('../hooks/useRemotePlayers', () => ({
  useRemotePlayers: () => mockPlayers(),
  usePlayOnRemotePlayer: () => ({ mutateAsync: mockPlay, isPending: false }),
}));

const mount = () =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter>
        <PlayOnMenu contentId={'a'.repeat(40)} title="Arena TV" />
      </TestMemoryRouter>
    </ThemeProvider>
  );

describe('PlayOnMenu', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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

  it('points at the Integrations page when there are no players', () => {
    mockPlayers.mockReturnValue({ data: [], isLoading: false });
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Play on…' }));
    expect(screen.getByRole('menuitem', { name: /Add a player/ })).toHaveAttribute('href', '/integrations');
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

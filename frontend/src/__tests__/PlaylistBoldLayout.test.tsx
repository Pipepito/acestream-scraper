import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';

import Playlist from '../pages/Playlist';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as playlistHooks from '../hooks/usePlaylists';
import * as baseUrlHooks from '../hooks/useBaseUrls';

jest.mock('../hooks/usePlaylists');
jest.mock('../hooks/useBaseUrls');

describe('Playlist bold layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (playlistHooks.useChannelGroups as jest.Mock).mockReturnValue({
      data: ['News', 'Sports'],
      isLoading: false,
    });
    (baseUrlHooks.useBaseUrls as jest.Mock).mockReturnValue({
      data: [
        { id: 1, name: 'Ace player', pattern: 'acestream://', is_default: true },
        {
          id: 2,
          name: 'Local HLS',
          pattern: 'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}',
          is_default: false,
        },
      ],
      isLoading: false,
    });
  });

  it('shows the playlist URL as a scannable QR code', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Playlist />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Show QR Code' }));

    const dialog = screen.getByRole('dialog', { name: 'Playlist QR code' });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'QR code for the playlist URL' })).toBeInTheDocument();
    expect(dialog).toHaveTextContent(/\/api\/v1\/playlists\/m3u\?/);
  });

  it('keeps the playlist primary path ahead of optional advanced controls', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Playlist />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByText('Playlist ready')).toBeInTheDocument();
    expect(screen.getByText(/download the playlist or share the link first/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Show advanced options' })).toBeInTheDocument();
    expect(screen.queryByText(/use them only when the basic download or share path needs extra filtering/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Show advanced options' }));

    expect(screen.getByText(/use them only when the basic download or share path needs extra filtering/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download M3U' })).toBeInTheDocument();
  });

  it('adds favorites-only playlist filtering to the primary export path', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Playlist />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    const checkbox = screen.getByRole('checkbox', { name: 'Only include favorite TV channels' });

    expect(checkbox).not.toBeChecked();
    expect(screen.getByDisplayValue(/\/api\/v1\/playlists\/m3u\?/i)).not.toHaveValue(expect.stringContaining('favorites_only=true'));

    fireEvent.click(checkbox);

    expect(checkbox).toBeChecked();
    expect((screen.getByDisplayValue(/\/api\/v1\/playlists\/m3u\?/i) as HTMLInputElement).value).toContain('favorites_only=true');
  });

  it('appends base_url_id to the playlist URL when a named base URL is selected', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Playlist />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    const urlField = () => screen.getByDisplayValue(/\/api\/v1\/playlists\/m3u\?/i) as HTMLInputElement;

    expect(urlField().value).not.toContain('base_url_id');

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Stream base URL' }));
    fireEvent.click(screen.getByRole('option', { name: 'Local HLS' }));

    expect(urlField().value).toContain('base_url_id=2');

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Stream base URL' }));
    fireEvent.click(screen.getByRole('option', { name: 'Default' }));

    expect(urlField().value).not.toContain('base_url_id');
  });
});

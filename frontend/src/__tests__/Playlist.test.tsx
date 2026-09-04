import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Playlist from '../pages/Playlist';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as playlistHooks from '../hooks/usePlaylists';
import * as baseUrlHooks from '../hooks/useBaseUrls';
import * as systemHooks from '../hooks/useSystemServices';

jest.mock('../hooks/usePlaylists');
jest.mock('../hooks/useBaseUrls');
jest.mock('../hooks/useSystemServices');

const urlField = () => screen.getByRole('textbox', { name: 'Playlist URL' }) as HTMLInputElement;

describe('Playlist page', () => {
  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Playlist />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  beforeEach(() => {
    jest.clearAllMocks();
    (playlistHooks.useChannelGroups as jest.Mock).mockReturnValue({ data: ['News', 'Sports'], isLoading: false });
    (playlistHooks.usePlaylistChannelSummary as jest.Mock).mockReturnValue({ data: { total_channels: 48, online: 12, offline: 30, unknown: 6 } });
    (baseUrlHooks.useBaseUrls as jest.Mock).mockReturnValue({
      data: [
        { id: 1, name: 'Ace player', pattern: 'acestream://', is_default: true },
        { id: 2, name: 'Local HLS', pattern: 'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}', is_default: false },
      ],
      isLoading: false,
    });
    window.localStorage.removeItem('apiToken');
    (systemHooks.usePublicUrl as jest.Mock).mockReturnValue({
      data: { url: 'http://scraper.lan:8000', source: 'setting', warnings: [] },
      isLoading: false,
    });
  });

  it('shows an absolute link, options with real counts, and no hero or how-to', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Playlist' })).toBeInTheDocument();
    expect(urlField().value).toMatch(/^http:\/\/scraper\.lan:8000\/api\/v1\/playlists\/m3u\?/);
    expect(urlField().value).not.toContain('only_online=true');
    expect(screen.getByRole('checkbox', { name: 'Only online channels' })).not.toBeChecked();
    expect(screen.getByText('12 of 48 channels are online right now')).toBeInTheDocument();
    expect(screen.getByText(/Import this URL in VLC, Kodi or your IPTV app/)).toBeInTheDocument();
    expect(screen.queryByText('Playlist ready')).not.toBeInTheDocument();
    expect(screen.queryByText(/How to use this playlist/)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download M3U' })).toHaveAttribute('href', expect.stringContaining('/api/v1/playlists/m3u?'));

    fireEvent.click(screen.getByRole('checkbox', { name: 'Only online channels' }));
    expect(urlField().value).toContain('only_online=true');
  });

  it('keeps group filters collapsed until asked', () => {
    renderPage();
    expect(screen.queryByLabelText('Include groups')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Group filters' }));
    expect(screen.getByLabelText('Include groups')).toBeInTheDocument();
    expect(screen.getByLabelText('Exclude groups')).toBeInTheDocument();
  });

  it('adds favorites-only to the link', () => {
    renderPage();
    const checkbox = screen.getByRole('checkbox', { name: 'Favorite TV channels only' });
    expect(urlField().value).not.toContain('favorites_only=true');
    fireEvent.click(checkbox);
    expect(urlField().value).toContain('favorites_only=true');
  });

  it('appends base_url_id when a named link format is selected', () => {
    renderPage();
    expect(urlField().value).not.toContain('base_url_id');
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Stream link format' }));
    fireEvent.click(screen.getByRole('option', { name: 'Local HLS' }));
    expect(urlField().value).toContain('base_url_id=2');
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Stream link format' }));
    fireEvent.click(screen.getByRole('option', { name: 'Default' }));
    expect(urlField().value).not.toContain('base_url_id');
  });

  it('copies the absolute link and shows the QR code', async () => {
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Copy playlist URL' }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(expect.stringMatching(/^http:\/\/scraper\.lan:8000\/api\/v1\/playlists\/m3u\?/)));
    expect(await screen.findByText('Playlist link copied.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Show QR code' }));
    const dialog = screen.getByRole('dialog', { name: 'Playlist QR code' });
    expect(screen.getByRole('img', { name: 'QR code for the playlist URL' })).toBeInTheDocument();
    expect(dialog).toHaveTextContent(/http:\/\/scraper\.lan:8000\/api\/v1\/playlists\/m3u\?/);
  });

  it('falls back to the page origin while the public URL is loading', () => {
    (systemHooks.usePublicUrl as jest.Mock).mockReturnValue({ data: undefined, isLoading: true });
    renderPage();
    expect(urlField().value).toMatch(/^http:\/\/localhost\/api\/v1\/playlists\/m3u\?/);
  });

  it('appends the stored API token so players can authenticate', () => {
    window.localStorage.setItem('apiToken', 's3cret');
    renderPage();
    expect(urlField().value).toContain('token=s3cret');
    window.localStorage.removeItem('apiToken');
  });
});

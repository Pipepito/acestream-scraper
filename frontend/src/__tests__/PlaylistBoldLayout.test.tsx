import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';

import Playlist from '../pages/Playlist';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import * as playlistHooks from '../hooks/usePlaylists';

jest.mock('../hooks/usePlaylists');

describe('Playlist bold layout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (playlistHooks.useChannelGroups as jest.Mock).mockReturnValue({
      data: ['News', 'Sports'],
      isLoading: false,
    });
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
});

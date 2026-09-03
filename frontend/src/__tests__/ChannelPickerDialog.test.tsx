import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import ChannelPickerDialog from '../components/player/ChannelPickerDialog';
import { createAppTheme } from '../theme';

const mockCatalog = jest.fn();
const mockChannels = jest.fn();
const mockPlay = jest.fn();
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: (...args: unknown[]) => mockCatalog(...args) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: (...args: unknown[]) => mockChannels(...args) }));
jest.mock('../hooks/useRemotePlayers', () => ({ usePlayOnRemotePlayer: () => ({ mutateAsync: mockPlay, isPending: false }) }));

const player = {
  id: 1,
  name: 'Living room',
  kind: 'vlc' as const,
  host: 'h',
  port: 8080,
  username: null,
  base_url_id: null,
  has_password: true,
  created_at: '',
  updated_at: '',
};

const mount = (onClose: () => void) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <ChannelPickerDialog open player={player} onClose={onClose} />
    </ThemeProvider>
  );

describe('ChannelPickerDialog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('picks a TV channel and sends its best stream', async () => {
    mockCatalog.mockReturnValue({
      data: [
        {
          id: 7,
          name: 'Arena TV',
          is_active: true,
          acestream_channels: [
            { id: 'best', name: 'Feed 1', is_online: true },
            { id: 'other', name: 'Feed 2' },
          ],
        },
        { id: 8, name: 'Empty', is_active: true, acestream_channels: [] },
      ],
      isLoading: false,
    });
    mockChannels.mockReturnValue({ data: { items: [] }, isLoading: false });
    mockPlay.mockResolvedValue({ url: 'x' });
    const onClose = jest.fn();
    mount(onClose);
    const input = screen.getByRole('combobox', { name: 'Channel' });
    fireEvent.mouseDown(input);
    expect(screen.queryByText('Empty')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('option', { name: /Arena TV/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Send to Living room' }));
    await waitFor(() => expect(mockPlay).toHaveBeenCalledWith({ id: 1, contentId: 'best', title: 'Arena TV' }));
    expect(onClose).toHaveBeenCalled();
  });

  it('switches to raw streams', () => {
    mockCatalog.mockReturnValue({ data: [], isLoading: false });
    mockChannels.mockReturnValue({
      data: { items: [{ id: 's1', name: 'Raw feed', group: 'Sports', is_online: true }] },
      isLoading: false,
    });
    mount(jest.fn());
    fireEvent.click(screen.getByRole('button', { name: 'Streams' }));
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Channel' }));
    expect(screen.getByRole('option', { name: /Raw feed/ })).toBeInTheDocument();
  });
});

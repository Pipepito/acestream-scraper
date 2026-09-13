import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ChannelRowActions from '../components/channels/ChannelRowActions';
import { createAppTheme } from '../theme';
import type { AcestreamChannel } from '../services/channelService';

const channel: AcestreamChannel = {
  id: 'abc',
  name: 'Alpha',
  status: 'active',
  last_seen: '',
  is_online: true,
  epg_update_protected: false,
  tv_channel_id: 7,
  tv_channel_name: 'Arena TV',
};

const mount = (overrides: Partial<AcestreamChannel> = {}) => {
  const handlers = {
    onPlay: jest.fn(),
    onPlayOn: jest.fn(),
    onCheckStatus: jest.fn(),
    onEdit: jest.fn(),
    onToggleHidden: jest.fn(),
    onAssignTV: jest.fn(),
    onOpenTV: jest.fn(),
    onToggleTVFavorite: jest.fn(),
    onDelete: jest.fn(),
  };
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <ChannelRowActions channel={{ ...channel, ...overrides }} {...handlers} />
    </ThemeProvider>
  );
  return handlers;
};

describe('ChannelRowActions', () => {
  it('shows exactly two visible actions: play and check status', () => {
    const handlers = mount();
    const buttons = screen.getAllByRole('button');
    expect(buttons.map((b) => b.getAttribute('aria-label'))).toEqual([
      'play channel Alpha',
      'check channel status Alpha',
      'More actions for Alpha',
    ]);

    fireEvent.click(screen.getByRole('button', { name: 'play channel Alpha' }));
    expect(handlers.onPlay).toHaveBeenCalledWith(expect.objectContaining({ id: 'abc' }));
  });

  it('moves the TV link into the menu', () => {
    const handlers = mount();
    fireEvent.click(screen.getByRole('button', { name: 'More actions for Alpha' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Open TV channel: Arena TV' }));
    expect(handlers.onOpenTV).toHaveBeenCalledWith(expect.objectContaining({ id: 'abc' }));
  });

  it('offers "Play on…" in the menu', () => {
    const handlers = mount();
    fireEvent.click(screen.getByRole('button', { name: 'More actions for Alpha' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Play on…' }));
    expect(handlers.onPlayOn).toHaveBeenCalledWith(expect.objectContaining({ id: 'abc' }));
  });

  it('offers linking when the channel has no TV channel', () => {
    const handlers = mount({ tv_channel_id: undefined, tv_channel_name: undefined });
    fireEvent.click(screen.getByRole('button', { name: 'More actions for Alpha' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Link to a TV channel' }));
    expect(handlers.onAssignTV).toHaveBeenCalledWith(expect.objectContaining({ id: 'abc' }));
  });
});

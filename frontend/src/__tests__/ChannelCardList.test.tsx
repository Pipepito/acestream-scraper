import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ChannelCardList from '../components/channels/ChannelCardList';
import { createAppTheme } from '../theme';
import type { AcestreamChannel } from '../services/channelService';

const channel: AcestreamChannel = {
  id: 'abc123',
  name: 'Alpha Sports',
  group: 'Sports',
  status: 'active',
  last_seen: '2024-01-15T13:45:00Z',
  last_checked: undefined,
  is_online: false,
  is_active: false,
  epg_update_protected: false,
  tv_channel_id: 7,
  tv_channel_name: 'Arena TV',
  tv_channel_is_favorite: false,
};

const renderList = (overrides: Partial<React.ComponentProps<typeof ChannelCardList>> = {}) => {
  const props = {
    channels: [channel],
    loading: false,
    checkingStatus: {},
    selectedIds: [] as string[],
    onSelectionChange: jest.fn(),
    totalCount: 60,
    page: 1,
    pageSize: 25,
    onPageChange: jest.fn(),
    onCopyId: jest.fn(),
    onCheckStatus: jest.fn(),
    onEdit: jest.fn(),
    onToggleHidden: jest.fn(),
    onAssignTV: jest.fn(),
    onOpenTV: jest.fn(),
    onToggleTVFavorite: jest.fn(),
    onDelete: jest.fn(),
    ...overrides,
  };
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <ChannelCardList {...props} />
    </ThemeProvider>
  );
  return props;
};

describe('ChannelCardList', () => {
  it('renders one card per channel with state, id, actions and selection', () => {
    const props = renderList();
    const card = screen.getByRole('article', { name: 'Alpha Sports' });

    expect(within(card).getByText('Sports · TV: Arena TV')).toBeInTheDocument();
    expect(within(card).getByText('Offline')).toBeInTheDocument();
    expect(within(card).getByText('Hidden')).toBeInTheDocument();
    expect(within(card).getByText('Checked never')).toBeInTheDocument();
    expect(within(card).getByText('abc123')).toBeInTheDocument();
    expect(within(card).getByRole('button', { name: 'go to tv channel Arena TV' })).toBeInTheDocument();

    fireEvent.click(within(card).getByRole('checkbox', { name: 'Select Alpha Sports' }));
    expect(props.onSelectionChange).toHaveBeenCalledWith(['abc123']);

    fireEvent.click(within(card).getByRole('button', { name: 'More actions for Alpha Sports' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Show in playlist' }));
    expect(props.onToggleHidden).toHaveBeenCalledWith(expect.objectContaining({ id: 'abc123' }));
  });

  it('paginates with previous/next and a range label', () => {
    const props = renderList();
    expect(screen.getByText('26–50 of 60')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Go to next page' }));
    expect(props.onPageChange).toHaveBeenCalledWith(2);
    fireEvent.click(screen.getByRole('button', { name: 'Go to previous page' }));
    expect(props.onPageChange).toHaveBeenCalledWith(0);
  });

  it('shows an empty state when nothing matches', () => {
    renderList({ channels: [], totalCount: 0 });
    expect(screen.getByText('No channels to show')).toBeInTheDocument();
  });
});

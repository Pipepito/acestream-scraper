import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AcestreamChannels from '../pages/AcestreamChannels';
import { createAppTheme } from '../theme';
import { ApiError } from '../services/apiErrors';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseAcestreamChannels = jest.fn();
const mockUseDeleteAcestreamChannel = jest.fn();
const mockUseAllTVChannels = jest.fn();
const mockGetGroups = jest.fn();
const mockCheckAllStatuses = jest.fn();
const mockUpdateAcestreamChannel = jest.fn();
const mockUpdateTVChannel = jest.fn();
const mockDeleteMutate = jest.fn();

type Row = { id: string; name: string; is_active?: boolean; tv_channel_id?: number; tv_channel_name?: string; tv_channel_is_favorite?: boolean };
type Handlers = {
  channels: Row[];
  loading: boolean;
  hasActiveFilters?: boolean;
  onDelete: (row: Row) => void;
  onToggleHidden: (row: Row) => void;
  onToggleTVFavorite: (row: Row) => void;
  onPlay: (row: Row) => void;
};

jest.mock('../components/ChannelTable', () => ({
  __esModule: true,
  default: ({ channels, loading, hasActiveFilters, onDelete, onToggleHidden, onToggleTVFavorite, onPlay }: Handlers) => (
    <div data-testid="channel-table">
      channels:{channels.length};loading:{String(loading)};filtered:{String(Boolean(hasActiveFilters))}
      {channels.map((channel) => (
        <div key={channel.id}>
          <span>{channel.name}</span>
          <button type="button" onClick={() => onDelete(channel)}>{`delete ${channel.name}`}</button>
          <button type="button" onClick={() => onToggleHidden(channel)}>{`hide ${channel.name}`}</button>
          <button type="button" onClick={() => onToggleTVFavorite(channel)}>{`favorite ${channel.name}`}</button>
          <button type="button" onClick={() => onPlay(channel)}>{`play ${channel.name}`}</button>
        </div>
      ))}
    </div>
  ),
}));
jest.mock('../components/player/StreamPlayerDialog', () => ({
  __esModule: true,
  default: ({ open, title }: { open: boolean; title: string }) => (open ? <div role="dialog">{title}</div> : null),
}));
jest.mock('../components/channels/ChannelFilterBar', () => ({
  __esModule: true,
  default: ({ groups, onChange }: { groups: string[]; onChange: (filters: { search?: string }) => void }) => (
    <div data-testid="filter-bar">
      groups:{groups.join(',') || 'none'}
      <button type="button" onClick={() => onChange({ search: 'alpha' })}>apply search</button>
    </div>
  ),
}));
jest.mock('../components/BulkOperations', () => ({ __esModule: true, default: () => null }));
jest.mock('../components/BatchAssignDialog', () => ({ __esModule: true, default: () => null }));
jest.mock('../components/QuickEditDialog', () => ({ __esModule: true, default: () => null }));
jest.mock('../components/AssignTVChannelDialog', () => ({ __esModule: true, default: () => null }));
jest.mock('../hooks/useChannels', () => ({
  useAcestreamChannels: (...args: unknown[]) => mockUseAcestreamChannels(...args),
  useDeleteAcestreamChannel: () => mockUseDeleteAcestreamChannel(),
}));
jest.mock('../hooks/useTVChannels', () => ({
  useAllTVChannels: () => mockUseAllTVChannels(),
}));
jest.mock('../services/channelService', () => ({
  acestreamChannelService: {
    getGroups: (...args: unknown[]) => mockGetGroups(...args),
    checkAllStatuses: (...args: unknown[]) => mockCheckAllStatuses(...args),
    updateAcestreamChannel: (...args: unknown[]) => mockUpdateAcestreamChannel(...args),
    checkAcestreamChannelStatus: jest.fn(),
    assignToTVChannel: jest.fn(),
    createAcestreamChannel: jest.fn(),
    bulkEditAcestreamChannels: jest.fn(),
    bulkDeleteAcestreamChannels: jest.fn(),
    bulkActivateAcestreamChannels: jest.fn(),
    exportAcestreamChannelsCSV: jest.fn(),
  },
}));
jest.mock('../services/tvChannelService', () => ({
  tvChannelService: { update: (...args: unknown[]) => mockUpdateTVChannel(...args) },
}));

const alpha: Row = {
  id: 'ace-100',
  name: 'Alpha Sports',
  is_active: true,
  tv_channel_id: 7,
  tv_channel_name: 'Arena TV',
  tv_channel_is_favorite: true,
};

describe('AcestreamChannels page', () => {
  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <AcestreamChannels />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  const user = () => userEvent.setup();
  let refetch: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    refetch = jest.fn();
    mockUseAcestreamChannels.mockImplementation((params: { is_online?: boolean; page_size?: number }) => {
      if (params.page_size === 1) {
        return { data: { items: [], total: params.is_online ? 3 : 12 }, isLoading: false, refetch: jest.fn(), error: null };
      }
      return { data: { items: [alpha], total: 1 }, isLoading: false, refetch, error: null };
    });
    mockUseDeleteAcestreamChannel.mockReturnValue({ mutate: mockDeleteMutate });
    mockUseAllTVChannels.mockReturnValue({ data: { items: [] } });
    mockGetGroups.mockResolvedValue(['Sports', 'News']);
    mockCheckAllStatuses.mockResolvedValue({ message: 'Acestream status check task triggered successfully.' });
    mockUpdateTVChannel.mockResolvedValue(undefined);
    mockUpdateAcestreamChannel.mockResolvedValue(undefined);
  });

  it('shows the summary line, filter bar and table without a hero or separate filters section', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByTestId('filter-bar')).toHaveTextContent('groups:Sports,News'));

    const summary = screen.getByRole('status', { name: 'Channel summary' });
    expect(summary).toHaveTextContent('Channels12');
    expect(summary).toHaveTextContent('Online3');
    expect(summary).toHaveTextContent('Matching filtersall');
    expect(summary).toHaveTextContent('Selected0');
    expect(screen.getByRole('heading', { level: 1, name: 'Acestream Channels' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Channels' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 2, name: 'Filters' })).not.toBeInTheDocument();
    expect(screen.queryByText(/routing stage/i)).not.toBeInTheDocument();
    expect(screen.getByTestId('channel-table')).toHaveTextContent('channels:1;loading:false;filtered:false');

    await user().click(screen.getByRole('button', { name: 'apply search' }));
    expect(screen.getByTestId('channel-table')).toHaveTextContent('filtered:true');
    expect(screen.getByRole('status', { name: 'Channel summary' })).toHaveTextContent('Matching filters1');
  });

  it('keeps the table usable when group loading fails', async () => {
    mockGetGroups.mockRejectedValueOnce(new ApiError({ message: 'Network Error', status: 0, kind: 'offline', canRetry: true }));
    renderPage();

    expect(await screen.findByText('Unable to load groups')).toBeInTheDocument();
    expect(screen.getByTestId('filter-bar')).toHaveTextContent('groups:none');
    expect(screen.getByTestId('channel-table')).toHaveTextContent('channels:1;loading:false');
  });

  it('renders a retryable channels notice while keeping the page usable', async () => {
    mockUseAcestreamChannels.mockImplementation((params: { page_size?: number }) =>
      params.page_size === 1
        ? { data: undefined, isLoading: false, refetch: jest.fn(), error: null }
        : { data: { items: [], total: 0 }, isLoading: false, refetch, error: new ApiError({ message: 'Network Error', status: 0, kind: 'offline', canRetry: true }) }
    );
    renderPage();

    expect(await screen.findByText('Unable to load channels')).toBeInTheDocument();
    expect(screen.getByText('Unable to reach the server. Check your connection and try again.')).toBeInTheDocument();
    await user().click(screen.getByRole('button', { name: 'Try again' }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('toggles the linked TV favorite from the row and refreshes', async () => {
    renderPage();
    await user().click(screen.getByRole('button', { name: 'favorite Alpha Sports' }));
    await waitFor(() => expect(mockUpdateTVChannel).toHaveBeenCalledWith(7, { is_favorite: false }));
    expect(refetch).toHaveBeenCalled();
  });

  it('hides a channel from the playlist and confirms with a snackbar', async () => {
    renderPage();
    await user().click(screen.getByRole('button', { name: 'hide Alpha Sports' }));
    await waitFor(() => expect(mockUpdateAcestreamChannel).toHaveBeenCalledWith('ace-100', { is_active: false }));
    expect(await screen.findByText('Alpha Sports is now hidden from the playlist.')).toBeInTheDocument();
  });

  it('asks for confirmation before deleting and reports failures once', async () => {
    let callbacks: { onSuccess?: () => void; onError?: (error: unknown) => void } | undefined;
    mockDeleteMutate.mockImplementation((_id: string, cb?: typeof callbacks) => {
      callbacks = cb;
    });
    renderPage();

    await user().click(screen.getByRole('button', { name: 'delete Alpha Sports' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete Alpha Sports?' });
    await user().click(within(dialog).getByRole('button', { name: 'Delete' }));
    await waitFor(() => expect(mockDeleteMutate).toHaveBeenCalledWith('ace-100', expect.any(Object)));

    callbacks?.onError?.(new ApiError({ message: 'Channel is still in use.', status: 400, kind: 'validation', canRetry: false }));
    expect(await screen.findByText('Failed to delete channel: Channel is still in use.')).toBeInTheDocument();
    expect(screen.getAllByText('Failed to delete channel: Channel is still in use.')).toHaveLength(1);
  });

  it('does not delete when the confirmation is cancelled', async () => {
    renderPage();
    await user().click(screen.getByRole('button', { name: 'delete Alpha Sports' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete Alpha Sports?' });
    await user().click(within(dialog).getByRole('button', { name: 'Cancel' }));
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Delete Alpha Sports?' })).not.toBeInTheDocument());
    expect(mockDeleteMutate).not.toHaveBeenCalled();
  });

  it('opens the player dialog for the channel picked from the row', async () => {
    renderPage();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await user().click(screen.getByRole('button', { name: 'play Alpha Sports' }));
    expect(await screen.findByRole('dialog')).toHaveTextContent('Alpha Sports');
  });

  it('routes check-all through the channel service and shows validation errors in the snackbar', async () => {
    mockCheckAllStatuses.mockRejectedValueOnce(new ApiError({ message: 'Status check already running.', status: 422, kind: 'validation', canRetry: false }));
    renderPage();

    await user().click(screen.getByRole('button', { name: 'Check all statuses' }));
    await waitFor(() => expect(mockCheckAllStatuses).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('Status check already running.')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Status check already running.');
  });
});

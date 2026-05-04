import React, { act } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
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
const mockUpdateTVChannel = jest.fn();
const mockDeleteMutate = jest.fn();
let latestOnDelete: ((id: string) => Promise<boolean>) | undefined;
let latestExtraActions: ((row: { id: string; name: string; tv_channel_id?: number; tv_channel_name?: string; tv_channel_is_favorite?: boolean }) => React.ReactNode) | undefined;

jest.mock('../components/ChannelTable', () => ({
  __esModule: true,
  default: ({
    channels,
    loading,
    onDelete,
    extraActions,
  }: {
    channels: Array<{ id: string; name: string; tv_channel_id?: number; tv_channel_name?: string; tv_channel_is_favorite?: boolean }>;
    loading: boolean;
    onDelete: (id: string) => Promise<boolean>;
    extraActions?: (row: { id: string; name: string; tv_channel_id?: number; tv_channel_name?: string; tv_channel_is_favorite?: boolean }) => React.ReactNode;
  }) => {
    latestOnDelete = onDelete;
    latestExtraActions = extraActions;
    return (
      <div data-testid="channel-table">
        channels:{channels.length};loading:{String(loading)}
        {channels.map((channel) => (
          <div key={channel.id}>
            <span>{channel.name}</span>
            <span>{channel.tv_channel_is_favorite ? 'favorite-tv-linked' : 'not-favorite-tv-linked'}</span>
            {extraActions ? <div>{extraActions(channel)}</div> : null}
          </div>
        ))}
      </div>
    );
  },
}));

jest.mock('../components/AdvancedSearch', () => ({
  __esModule: true,
  default: ({ groups }: { groups: string[] }) => <div data-testid="advanced-search">groups:{groups.join(',') || 'none'}</div>,
}));

jest.mock('../components/BulkOperations', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../components/BatchAssignDialog', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../components/QuickEditDialog', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../components/AssignTVChannelDialog', () => ({
  __esModule: true,
  default: () => null,
}));

jest.mock('../hooks/useChannels', () => ({
  useAcestreamChannels: (...args: unknown[]) => mockUseAcestreamChannels(...args),
  useDeleteAcestreamChannel: (...args: unknown[]) => mockUseDeleteAcestreamChannel(...args),
}));

jest.mock('../hooks/useTVChannels', () => ({
  useAllTVChannels: (...args: unknown[]) => mockUseAllTVChannels(...args),
}));

jest.mock('../services/channelService', () => ({
  __esModule: true,
  acestreamChannelService: {
    getGroups: (...args: unknown[]) => mockGetGroups(...args),
    updateAcestreamChannel: jest.fn(),
    createAcestreamChannel: jest.fn(),
    checkAcestreamChannelStatus: jest.fn(),
    checkAllStatuses: (...args: unknown[]) => mockCheckAllStatuses(...args),
    assignToTVChannel: jest.fn(),
    bulkEditAcestreamChannels: jest.fn(),
    bulkDeleteAcestreamChannels: jest.fn(),
    bulkActivateAcestreamChannels: jest.fn(),
    exportAcestreamChannelsCSV: jest.fn(),
  },
}));

jest.mock('../services/tvChannelService', () => ({
  __esModule: true,
  tvChannelService: {
    update: (...args: unknown[]) => mockUpdateTVChannel(...args),
  },
}));

describe('AcestreamChannels page hardening', () => {
  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <AcestreamChannels />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  const renderPageAndWaitForGroups = async (options?: { expectedGroupsText?: string }) => {
    renderPage();
    await waitFor(() => expect(mockGetGroups).toHaveBeenCalled());
    const expectedGroupsText = options?.expectedGroupsText;
    if (expectedGroupsText) {
      await waitFor(() => expect(screen.getByTestId('advanced-search')).toHaveTextContent(expectedGroupsText));
    }
  };

  const user = () => userEvent.setup();

  beforeEach(() => {
    jest.clearAllMocks();
    latestOnDelete = undefined;

    mockUseAcestreamChannels.mockReturnValue({
      data: {
        items: [
          {
            id: 'ace-100',
            name: 'Alpha Sports',
            group: 'Sports',
            is_active: true,
            is_online: true,
            tv_channel_id: 7,
            tv_channel_name: 'Arena TV',
            tv_channel_is_favorite: true,
          },
        ],
        total: 1,
      },
      isLoading: false,
      refetch: jest.fn(),
      error: null,
    });
    mockUseDeleteAcestreamChannel.mockReturnValue({ mutate: mockDeleteMutate });
    mockUseAllTVChannels.mockReturnValue({ data: { items: [] } });
    mockGetGroups.mockResolvedValue(['Sports', 'News']);
    mockCheckAllStatuses.mockResolvedValue({ message: 'Acestream status check task triggered successfully.' });
    mockUpdateTVChannel.mockResolvedValue(undefined);
  });

  it('surfaces linked TV favorite state inside the AceStream inventory', async () => {
    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    expect(screen.getByText('favorite-tv-linked')).toBeInTheDocument();
  });

  it('toggles the linked TV favorite state from the AceStream inventory shortcut', async () => {
    const refetch = jest.fn();
    mockUseAcestreamChannels.mockReturnValue({
      data: {
        items: [
          {
            id: 'ace-100',
            name: 'Alpha Sports',
            group: 'Sports',
            is_active: true,
            is_online: true,
            tv_channel_id: 7,
            tv_channel_name: 'Arena TV',
            tv_channel_is_favorite: true,
          },
        ],
        total: 1,
      },
      isLoading: false,
      refetch,
      error: null,
    });

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    expect(latestExtraActions).toBeDefined();
    expect(screen.getByRole('button', { name: 'Remove Arena TV from favorites' })).toBeInTheDocument();

    await user().click(screen.getByRole('button', { name: 'Remove Arena TV from favorites' }));

    await waitFor(() => expect(mockUpdateTVChannel).toHaveBeenCalledWith(7, { is_favorite: false }));
    expect(refetch).toHaveBeenCalled();
  });

  it('opens with an extracted-channel routing summary and keeps inventory primary', async () => {
    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    const channelsHeading = screen.getByRole('heading', { level: 2, name: 'Channels' });
    const filtersHeading = screen.getByRole('heading', { level: 2, name: 'Filters' });

    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Extracted channels')).toBeInTheDocument();
    expect(screen.getByText('TV organization')).toBeInTheDocument();
    expect(screen.getByText(/extracted-channel routing stage/i)).toBeInTheDocument();
    expect(screen.getByText(/inventory status/i)).toBeInTheDocument();
    expect(screen.getByText(/assign channels to tv entries/i)).toBeInTheDocument();
    expect(channelsHeading.compareDocumentPosition(filtersHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('keeps the inventory usable while group suggestions are still loading', () => {
    mockGetGroups.mockReturnValue(new Promise(() => undefined));

    renderPage();

    expect(screen.getByTestId('channel-table')).toHaveTextContent('channels:1;loading:false');
  });

  it('keeps filters and channels visible when group loading fails', async () => {
    mockGetGroups.mockRejectedValueOnce(
      new ApiError({
        message: 'Network Error',
        status: 0,
        kind: 'offline',
        canRetry: true,
      })
    );

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:none' });

    expect(await screen.findByText('Unable to load groups')).toBeInTheDocument();
    expect(screen.getByText('Unable to reach the server. Check your connection and try again.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Filters' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Channels' })).toBeInTheDocument();
    expect(screen.getByTestId('advanced-search')).toHaveTextContent('groups:none');
    expect(screen.getByTestId('channel-table')).toHaveTextContent('channels:1;loading:false');
  });

  it('renders a retryable channels notice while keeping the page usable', async () => {
    const refetch = jest.fn();

    mockUseAcestreamChannels.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
      refetch,
      error: new ApiError({
        message: 'Network Error',
        status: 0,
        kind: 'offline',
        canRetry: true,
      }),
    });

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    expect(await screen.findByText('Unable to load channels')).toBeInTheDocument();
    expect(screen.getByText('Unable to reach the server. Check your connection and try again.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Acestream Channels' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Filters' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Channels' })).toBeInTheDocument();

    await user().click(screen.getByRole('button', { name: 'Try again' }));

    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it('returns a delete promise that waits for mutation completion', async () => {
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    let capturedCallbacks: { onSuccess?: () => void; onError?: (error: unknown) => void } | undefined;

    mockDeleteMutate.mockImplementation((_id: string, callbacks?: { onSuccess?: () => void; onError?: (error: unknown) => void }) => {
      capturedCallbacks = callbacks;
    });

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    const deletePromise = latestOnDelete?.('ace-100');
    let resolved = false;
    deletePromise?.then(() => {
      resolved = true;
    });

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this channel?');
    expect(mockDeleteMutate).toHaveBeenCalledWith('ace-100', expect.any(Object));
    expect(deletePromise).toBeInstanceOf(Promise);

    await Promise.resolve();
    expect(resolved).toBe(false);

    capturedCallbacks?.onSuccess?.();
    await deletePromise;

    expect(resolved).toBe(true);
    confirmSpy.mockRestore();
  });

  it('surfaces a single clear page-level message when channel deletion fails', async () => {
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    let capturedCallbacks: { onSuccess?: () => void; onError?: (error: unknown) => void } | undefined;

    mockDeleteMutate.mockImplementation((_id: string, callbacks?: { onSuccess?: () => void; onError?: (error: unknown) => void }) => {
      capturedCallbacks = callbacks;
    });

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    const deletePromise = latestOnDelete?.('ace-100');
    const deleteError = new ApiError({
      message: 'Channel is still in use.',
      status: 400,
      kind: 'validation',
      canRetry: false,
    });

    await act(async () => {
      capturedCallbacks?.onError?.(deleteError);
      await expect(deletePromise).rejects.toBe(deleteError);
    });

    expect(await screen.findByText('Failed to delete channel: Channel is still in use.')).toBeInTheDocument();
    expect(screen.getAllByText('Failed to delete channel: Channel is still in use.')).toHaveLength(1);
    confirmSpy.mockRestore();
  });

  it('resolves false when deletion is canceled before mutation starts', async () => {
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    await expect(latestOnDelete?.('ace-100')).resolves.toBe(false);

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this channel?');
    expect(mockDeleteMutate).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('routes check-all status requests through the channel service and preserves validation snackbar handling', async () => {
    mockCheckAllStatuses.mockRejectedValueOnce(
      new ApiError({
        message: 'Status check already running.',
        status: 422,
        kind: 'validation',
        canRetry: false,
      })
    );

    await renderPageAndWaitForGroups({ expectedGroupsText: 'groups:Sports,News' });

    await user().click(screen.getByRole('button', { name: 'Check All Statuses' }));

    await waitFor(() => expect(mockCheckAllStatuses).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('Status check already running.')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Status check already running.');
    expect(screen.queryByText(/Failed to check all statuses:/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Acestream status check task triggered successfully.')).not.toBeInTheDocument();
  });
});

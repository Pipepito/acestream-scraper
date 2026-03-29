import React from 'react';
import { act } from 'react';
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
const mockFetch = jest.fn();
const mockDeleteMutate = jest.fn();
let latestOnDelete: ((id: string) => Promise<boolean>) | undefined;

jest.mock('../components/ChannelTable', () => ({
  __esModule: true,
  default: ({ channels, loading, onDelete }: { channels: Array<{ id: string }>; loading: boolean; onDelete: (id: string) => Promise<boolean> }) => {
    latestOnDelete = onDelete;
    return <div data-testid="channel-table">channels:{channels.length};loading:{String(loading)}</div>;
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
    assignToTVChannel: jest.fn(),
    bulkEditAcestreamChannels: jest.fn(),
    bulkDeleteAcestreamChannels: jest.fn(),
    bulkActivateAcestreamChannels: jest.fn(),
    exportAcestreamChannelsCSV: jest.fn(),
  },
}));

describe('AcestreamChannels page hardening', () => {
  let consoleErrorSpy: jest.SpyInstance;

  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <AcestreamChannels />
        </TestMemoryRouter>
      </ThemeProvider>
    );

  const renderPageAndWaitForGroups = async () => {
    await act(async () => {
      renderPage();
    });
    await waitFor(() => expect(mockGetGroups).toHaveBeenCalledTimes(1));
    await act(async () => {
      await Promise.resolve();
    });
  };

  beforeEach(() => {
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.clearAllMocks();
    global.fetch = mockFetch as unknown as typeof fetch;
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
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Acestream status check task triggered successfully.' }),
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  const getActWarnings = () =>
    consoleErrorSpy.mock.calls.filter(([message]) => String(message).includes('not wrapped in act'));

  it('keeps filters and channels visible when group loading fails', async () => {
    mockGetGroups.mockRejectedValueOnce(
      new ApiError({
        message: 'Network Error',
        status: 0,
        kind: 'offline',
        canRetry: true,
      })
    );

    await renderPageAndWaitForGroups();

    expect(await screen.findByText('Unable to load groups')).toBeInTheDocument();
    expect(screen.getByText('Unable to reach the server. Check your connection and try again.')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Filters' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Channels' })).toBeInTheDocument();
    expect(screen.getByTestId('advanced-search')).toHaveTextContent('groups:none');
    expect(screen.getByTestId('channel-table')).toHaveTextContent('channels:1;loading:false');
    expect(getActWarnings()).toHaveLength(0);
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

    await renderPageAndWaitForGroups();

    expect(await screen.findByText('Unable to load channels')).toBeInTheDocument();
    expect(screen.getByText('Unable to reach the server. Check your connection and try again.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Acestream Channels' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Filters' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Channels' })).toBeInTheDocument();

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'Try again' }));
    });

    expect(refetch).toHaveBeenCalledTimes(1);
    expect(getActWarnings()).toHaveLength(0);
  });

  it('returns a delete promise that waits for mutation completion', async () => {
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    let capturedCallbacks: { onSuccess?: () => void; onError?: (error: unknown) => void } | undefined;

    mockDeleteMutate.mockImplementation((_id: string, callbacks?: { onSuccess?: () => void; onError?: (error: unknown) => void }) => {
      capturedCallbacks = callbacks;
    });

    await renderPageAndWaitForGroups();

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
    expect(getActWarnings()).toHaveLength(0);
    confirmSpy.mockRestore();
  });

  it('surfaces a single clear page-level message when channel deletion fails', async () => {
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
    let capturedCallbacks: { onSuccess?: () => void; onError?: (error: unknown) => void } | undefined;

    mockDeleteMutate.mockImplementation((_id: string, callbacks?: { onSuccess?: () => void; onError?: (error: unknown) => void }) => {
      capturedCallbacks = callbacks;
    });

    await renderPageAndWaitForGroups();

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
    expect(getActWarnings()).toHaveLength(0);
    confirmSpy.mockRestore();
  });

  it('resolves false when deletion is canceled before mutation starts', async () => {
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

    await renderPageAndWaitForGroups();

    await expect(latestOnDelete?.('ace-100')).resolves.toBe(false);

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this channel?');
    expect(mockDeleteMutate).not.toHaveBeenCalled();
    expect(getActWarnings()).toHaveLength(0);
    confirmSpy.mockRestore();
  });

  it('preserves the check-all snackbar flow with shared validation error handling', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      json: async () => ({ detail: 'Status check already running.' }),
    });

    await renderPageAndWaitForGroups();

    await act(async () => {
      await userEvent.click(screen.getByRole('button', { name: 'Check All Statuses' }));
    });

    expect(await screen.findByText('Status check already running.')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Status check already running.');
    expect(screen.queryByText(/Failed to check all statuses:/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Acestream status check task triggered successfully.')).not.toBeInTheDocument();
    expect(getActWarnings()).toHaveLength(0);
  });
});

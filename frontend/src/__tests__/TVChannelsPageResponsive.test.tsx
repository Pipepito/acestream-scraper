import React, { act } from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import { ApiError } from '../services/apiErrors';

import TVChannels from '../pages/TVChannels';
import { createAppTheme } from '../theme';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
const mockNavigate = jest.fn();
const mockUseAllTVChannels = jest.fn();
const mockUseTVChannelCatalog = jest.fn();
const mockCatalogRefetch = jest.fn();
const mockUseDeleteTVChannel = jest.fn();
const mockUseCreateTVChannel = jest.fn();
const mockUseUpdateTVChannel = jest.fn();
const mockUseToggleTVChannelFavorite = jest.fn();

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');

  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

jest.mock('../hooks/useTVChannels', () => ({
  useAllTVChannels: (...args: unknown[]) => mockUseAllTVChannels(...args),
  useTVChannelCatalog: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
  useDeleteTVChannel: (...args: unknown[]) => mockUseDeleteTVChannel(...args),
  useCreateTVChannel: (...args: unknown[]) => mockUseCreateTVChannel(...args),
  useUpdateTVChannel: (...args: unknown[]) => mockUseUpdateTVChannel(...args),
  useToggleTVChannelFavorite: (...args: unknown[]) => mockUseToggleTVChannelFavorite(...args),
}));

type MockTableChannel = { id: number; name: string; acestream_channels: Array<{ id?: string; channel_id: string }> };

jest.mock('../components/player/StreamPlayerDialog', () => ({
  __esModule: true,
  default: ({ open, title, contentId }: { open: boolean; title: string; contentId: string | null }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        {contentId}
      </div>
    ) : null,
}));

jest.mock('../components/TVChannelsTable', () => ({
  __esModule: true,
  default: ({
    channels,
    totalCount,
    page,
    pageSize,
    onPageChange,
    onPageSizeChange,
    onEdit,
    onDelete,
    onToggleFavorite,
    onPlay,
  }: {
    channels: MockTableChannel[];
    totalCount: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
    onEdit: (channel: MockTableChannel) => void;
    onDelete: (id: number) => void;
    onToggleFavorite: (channel: MockTableChannel) => void;
    onPlay?: (channel: MockTableChannel) => void;
  }) => (
    <div data-testid="tv-channels-table">
      rows:{channels.length}
      total:{totalCount}
      page:{page}
      pageSize:{pageSize}
      <button type="button" onClick={() => onPageSizeChange(1)}>
        Set page size to 1
      </button>
      {channels[0] ? (
        <>
          <button type="button" onClick={() => onPageChange(page + 1)}>
            Next page
          </button>
          <button type="button" onClick={() => onEdit(channels[0])}>
            Open edit dialog
          </button>
          <button type="button" onClick={() => onDelete(channels[0].id)}>
            Open delete dialog
          </button>
          <button type="button" onClick={() => onToggleFavorite(channels[0])}>
            Toggle first favorite
          </button>
          <button type="button" disabled={!onPlay} onClick={() => onPlay?.(channels[0])}>
            Play first channel
          </button>
        </>
      ) : null}
    </div>
  ),
}));

type LegacyUserEventWithSetup = typeof userEvent & {
  setup?: () => {
    click: (element: Element) => Promise<void>;
  };
};

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;
let deleteMutateAsync: jest.Mock;
let createMutateAsync: jest.Mock;
let updateMutateAsync: jest.Mock;
let toggleFavoriteMutateAsync: jest.Mock;

const renderPage = ({
  isPhone = false,
  isDesktop = true,
  isWideDesktop = false,
  viewportWidth,
}: {
  isPhone?: boolean;
  isDesktop?: boolean;
  isWideDesktop?: boolean;
  viewportWidth?: number;
} = {}) => {
  const theme = createAppTheme('light');

  mockResponsiveShellQueries(mockUseMediaQuery, theme, {
    isPhone,
    isDesktop,
    isWideDesktop,
    viewportWidth,
  });

  return render(
    <ThemeProvider theme={theme}>
      <TVChannels />
    </ThemeProvider>
  );
};

const click = async (element: Element) => {
  const legacyUserEvent = userEvent as LegacyUserEventWithSetup;

  if (typeof legacyUserEvent.setup === 'function') {
    const user = legacyUserEvent.setup();
    await act(async () => {
      await user.click(element);
    });
    return;
  }

  await act(async () => {
    element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  });
};

describe('TVChannels responsive page behavior', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseMediaQuery.mockReset();

    mockUseAllTVChannels.mockReturnValue({
      data: {
        items: [
          {
            id: 7,
            name: 'Arena TV',
            logo_url: '',
            description: 'Primary sports feed',
            category: 'Sports',
            country: 'RS',
            language: 'en',
            channel_number: 7,
            is_active: true,
            is_favorite: false,
            acestream_channels: [{ id: 'ace-1', channel_id: 'ace-1' }],
          },
        ],
        total: 1,
      },
      isLoading: false,
      isError: false,
      refetch: jest.fn(),
    });
    mockCatalogRefetch.mockReset();
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        {
          id: 7,
          name: 'Arena TV',
          logo_url: '',
          description: 'Primary sports feed',
          category: 'Sports',
          country: 'RS',
          language: 'en',
          channel_number: 7,
          is_active: true,
          is_favorite: false,
          acestream_channels: [{ id: 'ace-1', channel_id: 'ace-1' }],
        },
        {
          id: 8,
          name: 'Cinema Plus',
          logo_url: '',
          description: 'Movie channel',
          category: 'Movies',
          country: 'US',
          language: 'en',
          channel_number: 12,
          is_active: false,
          is_favorite: false,
          acestream_channels: [],
        },
      ],
      isLoading: false,
      isError: false,
      refetch: mockCatalogRefetch,
    });
    deleteMutateAsync = jest.fn().mockResolvedValue(undefined);
    createMutateAsync = jest.fn().mockResolvedValue(undefined);
    updateMutateAsync = jest.fn().mockResolvedValue(undefined);
    toggleFavoriteMutateAsync = jest.fn().mockImplementation(({ id, value }: { id: number; value?: boolean }) =>
      Promise.resolve({ id, is_favorite: value ?? true })
    );
    mockUseDeleteTVChannel.mockReturnValue({ mutateAsync: deleteMutateAsync });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync: createMutateAsync, isPending: false });
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync: updateMutateAsync, isPending: false });
    mockUseToggleTVChannelFavorite.mockReturnValue({ mutateAsync: toggleFavoriteMutateAsync, isPending: false });
  });

  it('keeps primary actions visible while collapsing filters on phone', async () => {
    renderPage({ isPhone: true, isDesktop: false, isWideDesktop: false });

    expect(screen.getByText('The channels you publish. Each one groups its streams and carries the EPG for the playlist.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add TV Channel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /show filters/i })).toBeInTheDocument();
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:2');
    expect(screen.queryByRole('form', { name: /channel filters/i })).not.toBeInTheDocument();

    await click(screen.getByRole('button', { name: /show filters/i }));

    const filtersRegion = screen.getByRole('region', { name: 'Channels' });

    expect(within(filtersRegion).getByRole('form', { name: /channel filters/i })).toBeInTheDocument();
    expect(within(filtersRegion).getByRole('button', { name: 'Apply Filters' })).toBeInTheDocument();
    expect(within(filtersRegion).getByRole('button', { name: 'Reset Filters' })).toBeInTheDocument();
    expect(within(filtersRegion).getByRole('button', { name: 'Apply Filters' })).toHaveAttribute('data-action-priority', 'primary');
    expect(within(filtersRegion).getByRole('button', { name: 'Reset Filters' })).toHaveAttribute('data-action-priority', 'secondary');
    expect(within(filtersRegion).getByLabelText('Category')).toBeInTheDocument();
    expect(within(filtersRegion).getByLabelText('Country')).toBeInTheDocument();
    expect(within(filtersRegion).getByLabelText('Language')).toBeInTheDocument();
    expect(within(filtersRegion).getByLabelText('Active')).toBeInTheDocument();
    expect(within(filtersRegion).queryByLabelText('Group')).not.toBeInTheDocument();
    expect(within(filtersRegion).queryByLabelText('Status')).not.toBeInTheDocument();
    expect(within(filtersRegion).queryByLabelText('Sort By')).not.toBeInTheDocument();
    expect(within(filtersRegion).queryByLabelText('Online')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /hide filters/i })).toBeInTheDocument();
  });

  it('opens with a summary line and the filters inside the channel list', () => {
    const theme = createAppTheme('light');

    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      viewportWidth: 1440,
    });

    render(
      <ThemeProvider theme={theme}>
        <TVChannels />
      </ThemeProvider>
    );

    const summary = screen.getByRole('status', { name: 'TV channel summary' });
    expect(summary).toHaveTextContent('Channels2');
    expect(summary).toHaveTextContent('Favorites0');
    expect(summary).toHaveTextContent('With streams1');
    expect(summary).toHaveTextContent('Matching filtersall');

    expect(screen.queryByText('Sources')).not.toBeInTheDocument();
    expect(screen.queryByText(/downstream stage/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Filters' })).not.toBeInTheDocument();
    const channelsSection = screen.getByRole('region', { name: 'Channels' });
    expect(within(channelsSection).getByRole('form', { name: /channel filters/i })).toBeInTheDocument();
    expect(within(channelsSection).getByTestId('tv-channels-table')).toBeInTheDocument();
  });

  it('opens create and edit dialogs with mobile-safe full-screen sizing on phone', async () => {
    renderPage({ isPhone: true, isDesktop: false, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Add TV Channel' }));

    const createDialog = screen.getByRole('dialog', { name: 'Add TV Channel' });
    expect(within(createDialog).getByRole('textbox', { name: /channel name/i })).toBeInTheDocument();
    expect(within(createDialog).queryByText('Channel basics')).not.toBeInTheDocument();
    expect(within(createDialog).queryByText('Optional metadata')).not.toBeInTheDocument();
    expect(within(createDialog).queryByText('Visibility & favorites')).not.toBeInTheDocument();
    expect(within(createDialog).getByText('Optional details')).toBeInTheDocument();
    expect(within(createDialog).getByRole('button', { name: 'Create' })).toBeInTheDocument();
    expect(createDialog).toHaveClass('MuiDialog-paperFullScreen');

    await click(within(createDialog).getByRole('button', { name: 'Cancel' }));
    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Add TV Channel' })).not.toBeInTheDocument();
    });

    await click(screen.getByRole('button', { name: /show filters/i }));
    await click(screen.getByRole('button', { name: 'Open edit dialog' }));

    const editDialog = screen.getByRole('dialog', { name: 'Edit TV Channel' });
    expect(within(editDialog).getByDisplayValue('Arena TV')).toBeInTheDocument();
    expect(within(editDialog).queryByText('Channel basics')).not.toBeInTheDocument();
    expect(within(editDialog).queryByText('Optional metadata')).not.toBeInTheDocument();
    expect(within(editDialog).queryByText('Visibility & favorites')).not.toBeInTheDocument();
    expect(within(editDialog).getByText('Optional details')).toBeInTheDocument();
    expect(within(editDialog).getByRole('textbox', { name: /epg id/i })).toBeInTheDocument();
    expect(within(editDialog).getByRole('spinbutton', { name: /channel number/i })).toBeInTheDocument();
    expect(within(editDialog).getByRole('button', { name: 'Update' })).toBeInTheDocument();
    expect(editDialog).toHaveClass('MuiDialog-paperFullScreen');
  });

  it('uses a confirmation dialog before deleting a channel', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Open delete dialog' }));

    expect(deleteMutateAsync).not.toHaveBeenCalled();

    const dialog = screen.getByRole('dialog', { name: 'Delete TV Channel' });
    expect(within(dialog).getByText('Remove Arena TV from the TV channel inventory? This cannot be undone.')).toBeInTheDocument();

    await click(within(dialog).getByRole('button', { name: 'Cancel' }));

    await waitFor(() => {
      expect(screen.queryByRole('dialog', { name: 'Delete TV Channel' })).not.toBeInTheDocument();
    });
    expect(deleteMutateAsync).not.toHaveBeenCalled();

    await click(screen.getByRole('button', { name: 'Open delete dialog' }));

    const reopenedDialog = screen.getByRole('dialog', { name: 'Delete TV Channel' });
    expect(within(reopenedDialog).getByRole('button', { name: 'Cancel' })).toHaveAttribute('data-action-priority', 'primary');
    expect(within(reopenedDialog).getByRole('button', { name: 'Delete TV Channel' })).toHaveAttribute('data-action-priority', 'danger');

    await click(within(reopenedDialog).getByRole('button', { name: 'Delete TV Channel' }));

    await waitFor(() => {
      expect(deleteMutateAsync).toHaveBeenCalledWith(7);
    });
  });

  it('paginates the filtered catalog consistently and refreshes the catalog data source', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:2');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('total:2');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:0');

    await click(screen.getByRole('button', { name: 'Set page size to 1' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('pageSize:1');

    await click(screen.getByRole('button', { name: 'Next page' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('total:2');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:1');

    await click(screen.getByRole('button', { name: 'Refresh' }));

    expect(mockCatalogRefetch).toHaveBeenCalledTimes(1);
  });

  it('requests only favorite channels from the catalog when Favorites only is enabled', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    expect(mockUseTVChannelCatalog).toHaveBeenLastCalledWith(undefined);

    const filtersRegion = screen.getByRole('region', { name: 'Channels' });
    const favoritesSwitch = within(filtersRegion).getByRole('checkbox', { name: 'Favorites only' });

    await click(favoritesSwitch);

    expect(mockUseTVChannelCatalog).toHaveBeenLastCalledWith({ favorites: true });

    await click(favoritesSwitch);

    expect(mockUseTVChannelCatalog).toHaveBeenLastCalledWith(undefined);
  });

  it('toggles a channel favorite from the inventory and confirms the change', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Toggle first favorite' }));

    await waitFor(() => {
      expect(toggleFavoriteMutateAsync).toHaveBeenCalledWith({ id: 7, value: true });
    });
    expect(await screen.findByText('Added Arena TV to favorites.')).toBeInTheDocument();
  });

  it('plays the best stream of a channel from the inventory', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Play first channel' }));

    expect(screen.getByRole('dialog', { name: 'Arena TV' })).toHaveTextContent('ace-1');
  });

  it('resets to the first page immediately when applying filters', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Set page size to 1' }));

    await click(screen.getByRole('button', { name: 'Next page' }));
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:1');

    const filtersRegion = screen.getByRole('region', { name: 'Channels' });
    const searchInput = within(filtersRegion).getByRole('textbox', { name: 'Search' });

    fireEvent.change(searchInput, { target: { value: 'Arena' } });

    await click(within(filtersRegion).getByRole('button', { name: 'Apply Filters' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('total:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:0');
  });

  it('resets to the first page when filters are cleared', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Set page size to 1' }));
    await click(screen.getByRole('button', { name: 'Next page' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');

    const filtersRegion = screen.getByRole('region', { name: 'Channels' });
    const searchInput = within(filtersRegion).getByRole('textbox', { name: 'Search' });

    fireEvent.change(searchInput, { target: { value: 'Arena' } });
    await click(within(filtersRegion).getByRole('button', { name: 'Apply Filters' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:0');

    await click(within(filtersRegion).getByRole('button', { name: 'Reset Filters' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:0');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('total:2');
  });

  it('trims search input before applying filters', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    const filtersRegion = screen.getByRole('region', { name: 'Channels' });
    const searchInput = within(filtersRegion).getByRole('textbox', { name: 'Search' });

    fireEvent.change(searchInput, { target: { value: '   Arena   ' } });
    await click(within(filtersRegion).getByRole('button', { name: 'Apply Filters' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('total:1');
  });

  it('shows recovery guidance when filters produce no matches and reset clears them', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    const filtersRegion = screen.getByRole('region', { name: 'Channels' });
    const searchInput = within(filtersRegion).getByRole('textbox', { name: 'Search' });

    fireEvent.change(searchInput, { target: { value: 'Missing channel' } });
    await click(within(filtersRegion).getByRole('button', { name: 'Apply Filters' }));

    expect(screen.getByText('No TV channels match the current filters')).toBeInTheDocument();
    expect(screen.getByText('Reset the filters or broaden your search to see the full list.')).toBeInTheDocument();

    await click(within(filtersRegion).getByRole('button', { name: 'Reset Filters' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:2');
    expect(screen.queryByText('No TV channels match the current filters')).not.toBeInTheDocument();
  });

  it('shows retry guidance when loading the catalog fails', async () => {
    mockUseTVChannelCatalog.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: mockCatalogRefetch,
    });

    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    expect(screen.getByRole('alert')).toHaveTextContent('We could not load the TV channel inventory. Try refreshing to reconnect.');

    await click(screen.getByRole('button', { name: 'Retry loading TV channels' }));

    expect(mockCatalogRefetch).toHaveBeenCalledTimes(1);
  });

  it('blocks whitespace-only channel names and keeps the create dialog open with guidance', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Add TV Channel' }));

    const createDialog = screen.getByRole('dialog', { name: 'Add TV Channel' });
    const nameInput = within(createDialog).getByRole('textbox', { name: /channel name/i });

    fireEvent.change(nameInput, { target: { value: '   ' } });
    await click(within(createDialog).getByRole('button', { name: 'Create' }));

    expect(createMutateAsync).not.toHaveBeenCalled();
    expect(within(createDialog).getByText('Enter a channel name before saving.')).toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: 'Add TV Channel' })).toBeInTheDocument();
  });

  it('keeps the edit dialog open and preserves input after an update failure', async () => {
    updateMutateAsync.mockRejectedValueOnce(
      new ApiError({
        message: 'Too many requests were sent. Please wait a moment and try again.',
        status: 429,
        kind: 'rate_limit',
        canRetry: true,
      })
    );

    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Open edit dialog' }));

    const editDialog = screen.getByRole('dialog', { name: 'Edit TV Channel' });
    const descriptionInput = within(editDialog).getByRole('textbox', { name: 'Description' });

    fireEvent.change(descriptionInput, { target: { value: 'Updated bilingual details عربى 日本語' } });
    await click(within(editDialog).getByRole('button', { name: 'Update' }));

    expect(updateMutateAsync).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('dialog', { name: 'Edit TV Channel' })).toBeInTheDocument();
    expect(within(screen.getByRole('dialog', { name: 'Edit TV Channel' })).getByDisplayValue('Updated bilingual details عربى 日本語')).toBeInTheDocument();
    expect(within(screen.getByRole('dialog', { name: 'Edit TV Channel' })).getByRole('alert')).toHaveTextContent(
      'Too many requests were sent. Please wait a moment and try again.'
    );
  });
});

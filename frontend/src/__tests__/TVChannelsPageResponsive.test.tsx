import React, { act } from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

import TVChannels from '../pages/TVChannels';
import { createAppTheme } from '../theme';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import { getWidePageSplitLayout } from '../styles/layout';

const mockNavigate = jest.fn();
const mockUseAllTVChannels = jest.fn();
const mockUseTVChannelCatalog = jest.fn();
const mockCatalogRefetch = jest.fn();
const mockUseDeleteTVChannel = jest.fn();
const mockUseCreateTVChannel = jest.fn();
const mockUseUpdateTVChannel = jest.fn();

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
  }: {
    channels: Array<{ id: number; name: string }>;
    totalCount: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
    onEdit: (channel: { id: number; name: string }) => void;
    onDelete: (id: number) => void;
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

const renderPage = ({
  isPhone = false,
  isDesktop = true,
  isWideDesktop = false,
}: {
  isPhone?: boolean;
  isDesktop?: boolean;
  isWideDesktop?: boolean;
} = {}) => {
  const theme = createAppTheme('light');

  mockResponsiveShellQueries(mockUseMediaQuery, theme, {
    isPhone,
    isDesktop,
    isWideDesktop,
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
            acestream_channels: [{ channel_id: 'ace-1' }],
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
          acestream_channels: [{ channel_id: 'ace-1' }],
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
    mockUseDeleteTVChannel.mockReturnValue({ mutateAsync: deleteMutateAsync });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
  });

  it('keeps primary actions visible while collapsing filters on phone', async () => {
    renderPage({ isPhone: true, isDesktop: false, isWideDesktop: false });

    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add TV Channel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /show filters/i })).toBeInTheDocument();
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:2');
    expect(screen.queryByRole('form', { name: /channel filters/i })).not.toBeInTheDocument();

    await click(screen.getByRole('button', { name: /show filters/i }));

    const filtersRegion = screen.getByRole('region', { name: 'Filters' });

    expect(within(filtersRegion).getByRole('form', { name: /channel filters/i })).toBeInTheDocument();
    expect(
      within(filtersRegion).getByText('Narrow the list with names, categories, status, or location details before reviewing the results.')
    ).toBeInTheDocument();
    expect(within(filtersRegion).getByRole('button', { name: 'Apply Filters' })).toBeInTheDocument();
    expect(within(filtersRegion).getByRole('button', { name: 'Reset Filters' })).toBeInTheDocument();
    expect(within(filtersRegion).getByRole('button', { name: 'Apply Filters' })).toHaveAttribute('data-action-priority', 'primary');
    expect(within(filtersRegion).getByRole('button', { name: 'Reset Filters' })).toHaveAttribute('data-action-priority', 'secondary');
    expect(within(filtersRegion).getByTestId('advanced-search-actions')).toHaveAttribute('data-layout', 'stacked');
    expect(within(filtersRegion).getByRole('textbox', { name: 'Search' }).closest('.MuiInputBase-root')).not.toHaveClass('MuiInputBase-sizeSmall');
    expect(within(filtersRegion).getByLabelText('Category').closest('.MuiInputBase-root')).not.toHaveClass('MuiInputBase-sizeSmall');
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

  it('uses a wide desktop two-zone layout with supporting filters beside inventory', () => {
    const theme = createAppTheme('light');

    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      isPhone: false,
      isDesktop: true,
      isWideDesktop: true,
    });

    render(
      <ThemeProvider theme={theme}>
        <TVChannels />
      </ThemeProvider>
    );

    const layout = screen.getByTestId('tv-channels-page-layout');
    const filtersSection = screen.getByRole('region', { name: 'Filters' });
    const inventorySection = screen.getByRole('region', { name: 'TV Channel Inventory' });
    const expectedLayout = getWidePageSplitLayout(theme, true) as Record<string, string>;

    expect(layout).toHaveStyle({
      display: expectedLayout.display,
      gridTemplateColumns: expectedLayout.gridTemplateColumns,
    });
    expect(inventorySection).toHaveStyle({ gridArea: 'primary' });
    expect(filtersSection).toHaveStyle({ gridArea: 'supporting' });
    expect(within(filtersSection).getByText('Use these filters to narrow the inventory before you edit, review, or remove a channel.')).toBeInTheDocument();
  });

  it('opens create and edit dialogs with mobile-safe full-screen sizing on phone', async () => {
    renderPage({ isPhone: true, isDesktop: false, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Add TV Channel' }));

    const createDialog = screen.getByRole('dialog', { name: 'Add TV Channel' });
    expect(within(createDialog).getByRole('textbox', { name: /channel name/i })).toBeInTheDocument();
    expect(within(createDialog).getByText('Channel basics')).toBeInTheDocument();
    expect(within(createDialog).getByText('Optional metadata')).toBeInTheDocument();
    expect(within(createDialog).getByText('Visibility & favorites')).toBeInTheDocument();
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
    expect(within(editDialog).getByText('Channel basics')).toBeInTheDocument();
    expect(within(editDialog).getByText('Optional metadata')).toBeInTheDocument();
    expect(within(editDialog).getByText('Visibility & favorites')).toBeInTheDocument();
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

  it('resets to the first page when applying filters that shrink the result set', async () => {
    renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

    await click(screen.getByRole('button', { name: 'Set page size to 1' }));

    await click(screen.getByRole('button', { name: 'Next page' }));
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:1');

    const filtersRegion = screen.getByRole('region', { name: 'Filters' });
    const searchInput = within(filtersRegion).getByRole('textbox', { name: 'Search' });

    await act(async () => {
      searchInput.dispatchEvent(new Event('focus', { bubbles: true }));
    });
    searchInput.setAttribute('value', 'Arena');
    await act(async () => {
      searchInput.dispatchEvent(new Event('input', { bubbles: true }));
      searchInput.dispatchEvent(new Event('change', { bubbles: true }));
    });

    await click(within(filtersRegion).getByRole('button', { name: 'Apply Filters' }));

    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('rows:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('total:1');
    expect(screen.getByTestId('tv-channels-table')).toHaveTextContent('page:0');
  });
});

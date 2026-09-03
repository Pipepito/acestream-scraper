import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import userEvent from '@testing-library/user-event';

import TVChannelsTable from '../components/TVChannelsTable';
import { createAppTheme } from '../theme';

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

describe('TVChannelsTable', () => {
  const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

  const renderTable = (ui: React.ReactElement, isCompact = false) => {
    mockUseMediaQuery.mockReturnValue(isCompact);

    return render(
      <ThemeProvider theme={createAppTheme('light')}>
        <div style={{ width: 1400, height: 700 }}>{ui}</div>
      </ThemeProvider>
    );
  };

  const tab = async () => {
    await userEvent.tab();
  };

  const tabUntilFocus = async (element: HTMLElement, maxSteps = 20) => {
    let focused = false;
    const handleFocus = () => {
      focused = true;
    };

    element.addEventListener('focus', handleFocus);

    try {
      for (let index = 0; index < maxSteps && !focused; index += 1) {
        await tab();
      }
    } finally {
      element.removeEventListener('focus', handleFocus);
    }
  };

  const channelWithStreams = {
    id: 42,
    name: 'Arena TV',
    logo_url: '',
    category: 'Sports',
    language: 'en',
    country: 'RS',
    channel_number: 7,
    is_active: true,
    created_at: '2024-01-01T00:00:00.000Z',
    updated_at: '2024-01-01T00:00:00.000Z',
    is_favorite: false,
    acestream_channels: [{ id: 'ace-1', name: 'Feed', channel_id: 'ace-1', is_active: true, is_online: true, epg_update_protected: false }],
  } as any;

  const baseProps = {
    loading: false,
    totalCount: 1,
    page: 0,
    pageSize: 25,
    onPageChange: jest.fn(),
    onPageSizeChange: jest.fn(),
    onSortChange: jest.fn(),
    onEdit: jest.fn(),
    onDelete: jest.fn(),
    onOpen: jest.fn(),
    onToggleFavorite: jest.fn(),
  };

  beforeEach(() => {
    mockUseMediaQuery.mockReset();
  });

  it('wraps the desktop grid in a semantic inventory region while keeping action labels explicit', () => {
    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Arena TV',
            logo_url: '',
            category: 'Sports',
            language: 'en',
            country: 'RS',
            channel_number: 7,
            is_active: true,
            acestream_channels: [{ channel_id: 'ace-1' }],
          } as any,
        ]}
        {...baseProps}
      />
    );

    const inventoryRegion = screen.getByRole('region', { name: 'TV channel inventory' });

    expect(within(inventoryRegion).getByRole('grid')).toBeInTheDocument();
    expect(within(inventoryRegion).getByRole('group', { name: 'TV channel actions for Arena TV' })).toBeInTheDocument();
    expect(within(inventoryRegion).getByRole('button', { name: 'edit tv channel Arena TV' })).toBeInTheDocument();
    expect(within(inventoryRegion).getByRole('button', { name: 'delete tv channel Arena TV' })).toBeInTheDocument();
    expect(within(inventoryRegion).getByRole('button', { name: 'open tv channel Arena TV' })).toBeInTheDocument();
  });

  it('keeps the first desktop row action keyboard focusable with its accessible label intact', async () => {
    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Arena TV',
            logo_url: '',
            category: 'Sports',
            language: 'en',
            country: 'RS',
            channel_number: 7,
            is_active: true,
            created_at: '2024-01-01T00:00:00.000Z',
            updated_at: '2024-01-01T00:00:00.000Z',
            is_favorite: false,
            acestream_channels: [{ channel_id: 'ace-1' }],
          } as any,
        ]}
        {...baseProps}
      />
    );

    const editButton = screen.getByRole('button', { name: 'edit tv channel Arena TV' });

    await tabUntilFocus(editButton);

    expect(editButton).toHaveFocus();
    expect(editButton).toHaveAccessibleName('edit tv channel Arena TV');
  });

  it('renders a stacked mobile summary with secondary metadata, explicit status text, and actions in compact mode', () => {
    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Arena TV',
            logo_url: '',
            category: 'Sports',
            language: 'en',
            country: 'RS',
            channel_number: 7,
            is_active: true,
            created_at: '2024-01-01T00:00:00.000Z',
            updated_at: '2024-01-01T00:00:00.000Z',
            is_favorite: false,
            acestream_channels: [{ channel_id: 'ace-1' }, { channel_id: 'ace-2' }],
          } as any,
        ]}
        {...baseProps}
      />,
      true
    );

    const row = screen.getByRole('article', { name: 'Arena TV' });

    expect(within(row).getByText('Arena TV')).toBeInTheDocument();
    expect(within(row).getByText('Channel 7')).toBeInTheDocument();
    expect(within(row).getByText('Active')).toBeInTheDocument();
    expect(within(row).getByText('Sports')).toBeInTheDocument();
    expect(within(row).getByText('Language: en')).toBeInTheDocument();
    expect(within(row).getByText('Country: RS')).toBeInTheDocument();
    expect(within(row).getByText('2 streams')).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: 'edit tv channel Arena TV' })).toHaveTextContent('Edit');
    expect(within(row).getByRole('button', { name: 'delete tv channel Arena TV' })).toHaveTextContent('Delete');
    expect(within(row).getByRole('button', { name: 'open tv channel Arena TV' })).toHaveTextContent('Open');
    expect(screen.queryByRole('grid')).not.toBeInTheDocument();
  });

  it('shows favorite state through the star toggle instead of a chip', () => {
    const favoriteChannel = {
      id: 42,
      name: 'Arena TV',
      logo_url: '',
      category: 'Sports',
      language: 'en',
      country: 'RS',
      channel_number: 7,
      is_active: true,
      created_at: '2024-01-01T00:00:00.000Z',
      updated_at: '2024-01-01T00:00:00.000Z',
      is_favorite: true,
      acestream_channels: [{ channel_id: 'ace-1' }],
    } as any;

    const { unmount } = renderTable(<TVChannelsTable channels={[favoriteChannel]} {...baseProps} />);

    expect(screen.getByRole('grid')).not.toHaveTextContent('Favorite');
    expect(screen.getByRole('button', { name: 'toggle favorite for tv channel Arena TV' })).toHaveAttribute('aria-pressed', 'true');

    unmount();

    renderTable(<TVChannelsTable channels={[favoriteChannel]} {...baseProps} />, true);

    const card = screen.getByRole('article', { name: 'Arena TV' });
    expect(within(card).queryByText('Favorite')).not.toBeInTheDocument();
    expect(within(card).getByRole('button', { name: 'toggle favorite for tv channel Arena TV' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('exposes a favorite star toggle that reports the channel in desktop and compact modes', () => {
    const channel = {
      id: 42,
      name: 'Arena TV',
      logo_url: '',
      category: 'Sports',
      language: 'en',
      country: 'RS',
      channel_number: 7,
      is_active: true,
      created_at: '2024-01-01T00:00:00.000Z',
      updated_at: '2024-01-01T00:00:00.000Z',
      is_favorite: false,
      acestream_channels: [{ channel_id: 'ace-1' }],
    } as any;
    const onToggleFavorite = jest.fn();

    const { unmount } = renderTable(
      <TVChannelsTable channels={[channel]} {...baseProps} onToggleFavorite={onToggleFavorite} />
    );

    const desktopStar = screen.getByRole('button', { name: 'toggle favorite for tv channel Arena TV' });

    expect(desktopStar).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(desktopStar);

    expect(onToggleFavorite).toHaveBeenCalledWith(channel);

    unmount();
    onToggleFavorite.mockClear();

    renderTable(
      <TVChannelsTable channels={[{ ...channel, is_favorite: true }]} {...baseProps} onToggleFavorite={onToggleFavorite} />,
      true
    );

    const compactStar = within(screen.getByRole('article', { name: 'Arena TV' })).getByRole('button', {
      name: 'toggle favorite for tv channel Arena TV',
    });

    expect(compactStar).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(compactStar);

    expect(onToggleFavorite).toHaveBeenCalledWith(expect.objectContaining({ id: 42, is_favorite: true }));
  });

  it('offers Play next to Open and disables it without streams', () => {
    const onPlay = jest.fn();
    const channels = [
      { ...channelWithStreams, name: 'With streams' },
      { ...channelWithStreams, id: 2, name: 'Empty', acestream_channels: [] },
    ];

    const { unmount } = renderTable(
      <TVChannelsTable {...baseProps} totalCount={2} channels={channels} onPlay={onPlay} />
    );

    fireEvent.click(screen.getByRole('button', { name: 'play tv channel With streams' }));
    expect(onPlay).toHaveBeenCalledWith(expect.objectContaining({ name: 'With streams' }));
    expect(screen.getByRole('button', { name: 'play tv channel Empty' })).toBeDisabled();

    unmount();
    onPlay.mockClear();

    renderTable(<TVChannelsTable {...baseProps} totalCount={2} channels={channels} onPlay={onPlay} />, true);

    const card = screen.getByRole('article', { name: 'With streams' });
    fireEvent.click(within(card).getByRole('button', { name: 'play tv channel With streams' }));
    expect(onPlay).toHaveBeenCalledWith(expect.objectContaining({ name: 'With streams' }));
    expect(
      within(screen.getByRole('article', { name: 'Empty' })).getByRole('button', { name: 'play tv channel Empty' })
    ).toBeDisabled();
  });

  it('disables Play when the page does not handle playback', () => {
    renderTable(<TVChannelsTable {...baseProps} channels={[channelWithStreams]} />);

    expect(screen.getByRole('button', { name: 'play tv channel Arena TV' })).toBeDisabled();
  });

  it('renders a clear mobile empty state in compact mode', () => {
    renderTable(<TVChannelsTable channels={[]} {...baseProps} totalCount={0} />, true);

    expect(screen.getByRole('heading', { level: 2, name: 'No TV channels to show' })).toBeInTheDocument();
    expect(
      screen.getByText('Add a TV channel or adjust your filters to start organizing playback sources.')
    ).toBeInTheDocument();
    expect(screen.queryByRole('grid')).not.toBeInTheDocument();
    expect(screen.queryByText('Page 0 of 0')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Go to next page' })).not.toBeInTheDocument();
  });

  it('renders text-explicit loading guidance in compact mode', () => {
    renderTable(<TVChannelsTable channels={[]} {...baseProps} loading totalCount={0} />, true);

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByText('Loading TV channels')).toBeInTheDocument();
    expect(screen.getByText('Preparing the latest results.')).toBeInTheDocument();
  });

  it('renders text-explicit loading guidance in the desktop inventory region', () => {
    renderTable(<TVChannelsTable channels={[]} {...baseProps} loading totalCount={30} />);

    const inventoryRegion = screen.getByRole('region', { name: 'TV channel inventory' });

    expect(within(inventoryRegion).getByRole('progressbar')).toBeInTheDocument();
    expect(within(inventoryRegion).getByText('Loading TV channels')).toBeInTheDocument();
    expect(within(inventoryRegion).getByText('Refreshing the latest results.')).toBeInTheDocument();
    expect(within(inventoryRegion).queryByRole('grid')).not.toBeInTheDocument();
  });

  it('keeps compact mode in a loading state instead of showing the empty state', () => {
    renderTable(<TVChannelsTable channels={[]} {...baseProps} loading totalCount={0} />, true);

    expect(screen.queryByRole('heading', { level: 2, name: 'No TV channels to show' })).not.toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders a desktop no-results-on-this-page message instead of the full empty-state copy', () => {
    renderTable(<TVChannelsTable channels={[]} {...baseProps} totalCount={30} page={1} pageSize={25} />);

    const inventoryRegion = screen.getByRole('region', { name: 'TV channel inventory' });

    expect(within(inventoryRegion).getByText('No TV channels on this page')).toBeInTheDocument();
    expect(within(inventoryRegion).getByText('Move between pages to keep browsing the list.')).toBeInTheDocument();
    expect(within(inventoryRegion).queryByText('No TV channels to show')).not.toBeInTheDocument();
  });

  it('renders compact pagination controls so mobile users can change page and page size', async () => {
    const onPageChange = jest.fn();
    const onPageSizeChange = jest.fn();

    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Arena TV',
            logo_url: '',
            category: 'Sports',
            language: 'en',
            country: 'RS',
            channel_number: 7,
            is_active: true,
            created_at: '2024-01-01T00:00:00.000Z',
            updated_at: '2024-01-01T00:00:00.000Z',
            is_favorite: false,
            acestream_channels: [{ channel_id: 'ace-1' }, { channel_id: 'ace-2' }],
          } as any,
        ]}
        {...baseProps}
        totalCount={30}
        pageSize={25}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />,
      true
    );

    expect(screen.getByText('1-25 of 30')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go to previous page' })).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Go to next page' }));

    expect(onPageChange).toHaveBeenCalledWith(1);

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Rows per page' }));
    fireEvent.click(await screen.findByRole('option', { name: '10' }));
    expect(onPageSizeChange).toHaveBeenCalledWith(10);
    expect(onPageChange).toHaveBeenCalledWith(0);
  });

  it('uses touch-friendly control sizing in compact mode', () => {
    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Arena TV',
            logo_url: '',
            category: 'Sports',
            language: 'en',
            country: 'RS',
            channel_number: 7,
            is_active: true,
            created_at: '2024-01-01T00:00:00.000Z',
            updated_at: '2024-01-01T00:00:00.000Z',
            is_favorite: false,
            acestream_channels: [{ channel_id: 'ace-1' }, { channel_id: 'ace-2' }],
          } as any,
        ]}
        {...baseProps}
        totalCount={30}
        pageSize={25}
      />,
      true
    );

    expect(screen.getByRole('button', { name: 'edit tv channel Arena TV' })).not.toHaveClass('MuiButton-sizeSmall');
    expect(screen.getByRole('button', { name: 'delete tv channel Arena TV' })).not.toHaveClass('MuiButton-sizeSmall');
    expect(screen.getByRole('button', { name: 'open tv channel Arena TV' })).not.toHaveClass('MuiButton-sizeSmall');
    expect(screen.getByRole('button', { name: 'Go to previous page' })).not.toHaveClass('MuiButton-sizeSmall');
    expect(screen.getByRole('button', { name: 'Go to next page' })).not.toHaveClass('MuiButton-sizeSmall');
    expect(screen.getByRole('combobox', { name: 'Rows per page' })).not.toHaveClass('MuiInputBase-inputSizeSmall');
  });

  it('keeps long multilingual mobile content readable without losing actions', () => {
    renderTable(
      <TVChannelsTable
        channels={[
          {
            id: 42,
            name: 'Canal Internacional Extraordinaer Langtitel عربى 日本語 😀 with very long operational suffix',
            logo_url: '',
            category: 'Internationale Live-Uebertragungen Mit Langem Namen',
            language: 'Deutsch / العربية / 日本語',
            country: 'DE / AE / JP',
            channel_number: 7001,
            is_active: true,
            created_at: '2024-01-01T00:00:00.000Z',
            updated_at: '2024-01-01T00:00:00.000Z',
            is_favorite: false,
            acestream_channels: [{ channel_id: 'ace-1' }],
          } as any,
        ]}
        {...baseProps}
      />,
      true
    );

    const row = screen.getByRole('article', {
      name: 'Canal Internacional Extraordinaer Langtitel عربى 日本語 😀 with very long operational suffix',
    });
    const title = within(row).getByText(
      'Canal Internacional Extraordinaer Langtitel عربى 日本語 😀 with very long operational suffix'
    );

    expect(title).toHaveStyle({ overflowWrap: 'break-word' });
    expect(within(row).getByText('Internationale Live-Uebertragungen Mit Langem Namen')).toBeInTheDocument();
    expect(within(row).getByText('Language: Deutsch / العربية / 日本語')).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: /edit tv channel/i })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: /delete tv channel/i })).toBeInTheDocument();
    expect(within(row).getByRole('button', { name: /open tv channel/i })).toBeInTheDocument();
  });

  it('hides the Number, Language and Country columns when no row fills them', () => {
    renderTable(
      <TVChannelsTable
        channels={[
          { id: 1, name: 'Plain', logo_url: '', category: 'News', is_active: true, acestream_channels: [] } as any,
        ]}
        {...baseProps}
      />
    );
    const headers = screen.getAllByRole('columnheader').map((header) => header.textContent);
    expect(headers).toEqual(expect.arrayContaining(['Name', 'Category', 'Streams', 'Status']));
    expect(headers).not.toEqual(expect.arrayContaining(['Number']));
    expect(headers).not.toEqual(expect.arrayContaining(['Language']));
    expect(headers).not.toEqual(expect.arrayContaining(['Country']));
  });

  it('keeps compact pagination available when the current server page has no visible rows', () => {
    renderTable(<TVChannelsTable channels={[]} {...baseProps} totalCount={30} page={1} pageSize={25} />, true);

    expect(screen.getByText('No TV channels on this page')).toBeInTheDocument();
    expect(screen.getByText('26-30 of 30')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go to previous page' })).toBeEnabled();
    expect(screen.getByLabelText('Rows per page')).toBeInTheDocument();
  });
});

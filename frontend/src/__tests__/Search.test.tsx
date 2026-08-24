import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import Search from '../pages/Search';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import { createAppTheme } from '../theme';

const mockUseSearch = jest.fn();
const mockUseAddAcestreamChannel = jest.fn();
const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

jest.mock('../hooks/useSearch', () => ({
  useSearch: (...args: unknown[]) => mockUseSearch(...args),
  useAddAcestreamChannel: (...args: unknown[]) => mockUseAddAcestreamChannel(...args),
}));

describe('Search page', () => {
  const theme = createAppTheme('light');
  const defaultResults = {
    success: true,
    message: 'ok',
    results: [
      { id: 'ace-1', name: 'Arena Premium', categories: ['sports'], bitrate: 1800 },
      { id: 'ace-2', name: 'News Global', categories: ['news'], bitrate: 1200 },
    ],
    pagination: { page: 1, page_size: 10, total_results: 2, total_pages: 1 },
  };

  const configureSearchMock = ({
    results = defaultResults,
    error = null,
  }: {
    results?: typeof defaultResults;
    error?: Error | null;
  } = {}) => {
    mockUseSearch.mockImplementation((query: string, _page: number, _pageSize: number, category?: string, options?: { enabled?: boolean }) => {
      if (!options?.enabled) {
        return {
          data: undefined,
          isLoading: false,
          error: null,
        };
      }

      if (error) {
        return {
          data: undefined,
          isLoading: false,
          error,
        };
      }

      return {
        data: {
          ...results,
          results: results.results,
          pagination: {
            ...results.pagination,
          },
          activeQuery: query,
          activeCategory: category,
        },
        isLoading: false,
        error: null,
      };
    });
  };

  const renderPage = () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    return {
      queryClient,
      ...render(
        <ThemeProvider theme={theme}>
          <QueryClientProvider client={queryClient}>
            <Search />
          </QueryClientProvider>
        </ThemeProvider>
      ),
    };
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseMediaQuery.mockReset();
    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      isPhone: false,
      isDesktop: true,
      isWideDesktop: true,
    });
    configureSearchMock();
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
  });

  it('renders shared header and section-first search hierarchy', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Search Channels' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Search Filters' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 2, name: 'Search Results' })).not.toBeInTheDocument();
  });

  it('surfaces only the supported search inputs', () => {
    renderPage();

    expect(screen.getByRole('textbox', { name: 'Search Query' })).toBeInTheDocument();
    expect(screen.getAllByText('Category').length).toBeGreaterThan(0);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Search' })).toBeInTheDocument();
    expect(screen.queryByText(/^status$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^source$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^language$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/bitrate range/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^sort$/i)).not.toBeInTheDocument();
  });

  it('shows the active query and category only after a search runs', () => {
    renderPage();

    expect(screen.queryByText(/current query:/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/current category:/i)).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.mouseDown(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('option', { name: 'Sports' }));
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByText(/current query:\s*arena/i)).toBeInTheDocument();
    expect(screen.getByText(/current category:\s*sports/i)).toBeInTheDocument();
  });

  it('keeps single-add and batch-add actions distinct with an explicit selection summary', () => {
    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByRole('checkbox', { name: 'select all search results' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Arena Premium' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Add 1 selected channels' })).not.toBeInTheDocument();
    expect(screen.getByText(/no channels selected yet/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));

    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
    expect(screen.getByText(/1 selected channel ready to add/i)).toBeInTheDocument();
  });

  it('adds a single result and invalidates the acestream inventory query', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({});
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync, isPending: false });

    const { queryClient } = renderPage();
    const invalidateQueries = jest.spyOn(queryClient, 'invalidateQueries').mockResolvedValue(undefined);

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add Arena Premium' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: 'ace-1',
        name: 'Arena Premium',
        group: 'sports',
      });
    });

    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['acestream-channels'] });
  });

  it('removes a successfully added single result from the current selection summary', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({});
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync, isPending: false });

    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result News Global' }));

    expect(screen.getByText(/2 selected channels ready to add/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Add Arena Premium' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: 'ace-1',
        name: 'Arena Premium',
        group: 'sports',
      });
    });

    expect(screen.getByText(/1 selected channel ready to add/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).not.toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'select search result News Global' })).toBeChecked();
  });

  it('adds selected results in batch and invalidates the acestream inventory query', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({});
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync, isPending: false });

    const { queryClient } = renderPage();
    const invalidateQueries = jest.spyOn(queryClient, 'invalidateQueries').mockResolvedValue(undefined);

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result News Global' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add 2 selected channels' }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(2));
    expect(mutateAsync).toHaveBeenNthCalledWith(1, {
      id: 'ace-1',
      name: 'Arena Premium',
      group: 'sports',
    });
    expect(mutateAsync).toHaveBeenNthCalledWith(2, {
      id: 'ace-2',
      name: 'News Global',
      group: 'news',
    });

    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['acestream-channels'] });
  });

  it('invalidates the acestream inventory query when a batch partially succeeds before failing', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);
    const mutateAsync = jest
      .fn()
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new Error('Second add failed'));
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync, isPending: false });

    try {
      const { queryClient } = renderPage();
      const invalidateQueries = jest.spyOn(queryClient, 'invalidateQueries').mockResolvedValue(undefined);

      fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
      fireEvent.click(screen.getByRole('button', { name: 'Search' }));
      fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));
      fireEvent.click(screen.getByRole('checkbox', { name: 'select search result News Global' }));
      fireEvent.click(screen.getByRole('button', { name: 'Add 2 selected channels' }));

      await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(2));
      expect(mutateAsync).toHaveBeenNthCalledWith(1, {
        id: 'ace-1',
        name: 'Arena Premium',
        group: 'sports',
      });
      expect(mutateAsync).toHaveBeenNthCalledWith(2, {
        id: 'ace-2',
        name: 'News Global',
        group: 'news',
      });

      expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['acestream-channels'] });
    } finally {
      consoleError.mockRestore();
    }
  });

  it('keeps only failed batch rows selected after earlier successes', async () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);
    const mutateAsync = jest
      .fn()
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new Error('Second add failed'));
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync, isPending: false });

    try {
      renderPage();

      fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
      fireEvent.click(screen.getByRole('button', { name: 'Search' }));
      fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));
      fireEvent.click(screen.getByRole('checkbox', { name: 'select search result News Global' }));

      expect(screen.getByText(/2 selected channels ready to add/i)).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: 'Add 2 selected channels' }));

      await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(2));
      expect(mutateAsync).toHaveBeenNthCalledWith(1, {
        id: 'ace-1',
        name: 'Arena Premium',
        group: 'sports',
      });
      expect(mutateAsync).toHaveBeenNthCalledWith(2, {
        id: 'ace-2',
        name: 'News Global',
        group: 'news',
      });

      expect(screen.getByText(/1 selected channel ready to add/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
      expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).not.toBeChecked();
      expect(screen.getByRole('checkbox', { name: 'select search result News Global' })).toBeChecked();
    } finally {
      consoleError.mockRestore();
    }
  });

  it('keeps empty-state guidance focused on broader query or category changes', () => {
    configureSearchMock({
      results: {
        success: true,
        message: 'ok',
        results: [],
        pagination: { page: 1, page_size: 10, total_results: 0, total_pages: 0 },
      },
    });

    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'zzz' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByText(/try a broader query or adjust the category/i)).toBeInTheDocument();
    expect(screen.queryByText(/status/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/language/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/bitrate range/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sort/i)).not.toBeInTheDocument();
  });

  it('ties the search error state to the current search action', () => {
    configureSearchMock({ error: new Error('Temporary upstream timeout') });

    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByText(/search for "arena" failed/i)).toBeInTheDocument();
    expect(screen.queryByText(/advanced search/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/status/i)).not.toBeInTheDocument();
  });

  it('keeps search context and add actions visible on phone widths', () => {
    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      isPhone: true,
      isDesktop: false,
      isWideDesktop: false,
    });

    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));

    expect(screen.getByRole('textbox', { name: 'Search Query' })).toBeInTheDocument();
    expect(screen.getAllByText('Category').length).toBeGreaterThan(0);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText(/current query:\s*arena/i)).toBeInTheDocument();
    expect(screen.getByText(/current category:\s*all categories/i)).toBeInTheDocument();
    expect(screen.getByText(/1 selected channel ready to add/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Arena Premium' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
  });
});

import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import Search from '../pages/Search';
import { searchService } from '../services/searchService';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import { createAppTheme } from '../theme';

const INFOHASH = '42832fbf9a1d3bdcca043e09951d6769fbbe04e7';
const CONTENT_ID = 'e72d03fb9694164317260f684470be9ab781ed95';
jest.mock('../services/searchService');

const mockUseSearch = jest.fn();
const mockUseAddSearchResult = jest.fn();
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
  useAddSearchResult: (...args: unknown[]) => mockUseAddSearchResult(...args),
}));

jest.mock('../components/player/StreamPlayerDialog', () => ({
  __esModule: true,
  default: ({ open, title, contentId }: { open: boolean; title: string; contentId: string | null }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        {contentId}
      </div>
    ) : null,
}));

describe('Search page', () => {
  const theme = createAppTheme('light');
  const defaultResults = {
    success: true,
    message: 'ok',
    results: [
      { id: INFOHASH, name: 'Arena Premium', categories: ['sports'], bitrate: 1800 },
      { id: 'b'.repeat(40), name: 'News Global', categories: ['news'], bitrate: 1200 },
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
            <MemoryRouter><Search /></MemoryRouter>
          </QueryClientProvider>
        </ThemeProvider>
      ),
    };
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.mocked(searchService.resolveContentId).mockReset().mockResolvedValue(CONTENT_ID);
    mockUseMediaQuery.mockReset();
    mockResponsiveShellQueries(mockUseMediaQuery, theme, {
      isPhone: false,
      isDesktop: true,
      isWideDesktop: true,
    });
    configureSearchMock();
    mockUseAddSearchResult.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
  });

  it('browses all channels on an empty search and keeps pagination', () => {
    configureSearchMock({ results: { ...defaultResults, pagination: { page: 1, page_size: 10, total_results: 25, total_pages: 3 } } });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    expect(mockUseSearch).toHaveBeenLastCalledWith('', 1, 10, '', { enabled: true });
    expect(screen.getByText('25 in all channels')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /go to page 2/i }));
    expect(mockUseSearch).toHaveBeenLastCalledWith('', 2, 10, '', { enabled: true });
  });

  it('renders shared header and section-first search hierarchy', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Search' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Search' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 2, name: 'Results' })).not.toBeInTheDocument();
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

    expect(screen.queryByRole('status', { name: 'Search summary' })).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.mouseDown(screen.getByRole('combobox'));
    fireEvent.click(screen.getByRole('option', { name: 'Sports' }));
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    const summary = screen.getByRole('status', { name: 'Search summary' });
    expect(summary).toHaveTextContent(/for ‘arena’ in sports/);
  });

  it('keeps single-add and batch-add actions distinct with an explicit selection summary', () => {
    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));

    expect(screen.getByRole('checkbox', { name: 'select all search results' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Arena Premium' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Add 1 selected channels' })).not.toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'Search summary' })).toHaveTextContent('Selected0');

    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));

    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'Search summary' })).toHaveTextContent('Selected1');
  });

  it('adds a single result and invalidates the acestream inventory query', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ outcome: 'added', rule_ids: [] });
    mockUseAddSearchResult.mockReturnValue({ mutateAsync, isPending: false });

    const { queryClient } = renderPage();
    const invalidateQueries = jest.spyOn(queryClient, 'invalidateQueries').mockResolvedValue(undefined);

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add Arena Premium' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: INFOHASH,
        name: 'Arena Premium',
        categories: ['sports'],
        bitrate: 1800,
      });
    });

    expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: ['acestream-channels'] });
  });

  it('resolves and plays a result without adding it', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ outcome: 'added', rule_ids: [] });
    mockUseAddSearchResult.mockReturnValue({ mutateAsync, isPending: false });

    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('button', { name: 'play Arena Premium' }));

    expect(await screen.findByRole('dialog', { name: 'Arena Premium' })).toHaveTextContent(CONTENT_ID);
    expect(searchService.resolveContentId).toHaveBeenCalledWith(INFOHASH);
    expect(mutateAsync).not.toHaveBeenCalled();
  });

  it('keeps the player closed and allows retry when resolution fails', async () => {
    jest.mocked(searchService.resolveContentId).mockRejectedValueOnce(new Error('Engine unavailable'));
    renderPage();
    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('button', { name: 'play Arena Premium' }));
    expect(await screen.findByText(/Could not play:/)).toBeInTheDocument();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'play Arena Premium' }));
    expect(await screen.findByRole('dialog', { name: 'Arena Premium' })).toHaveTextContent(CONTENT_ID);
  });

  it('removes a successfully added single result from the current selection summary', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ outcome: 'added', rule_ids: [] });
    mockUseAddSearchResult.mockReturnValue({ mutateAsync, isPending: false });

    renderPage();

    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result News Global' }));

    expect(screen.getByRole('status', { name: 'Search summary' })).toHaveTextContent('Selected2');

    fireEvent.click(screen.getByRole('button', { name: 'Add Arena Premium' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        id: INFOHASH,
        name: 'Arena Premium',
        categories: ['sports'],
        bitrate: 1800,
      });
    });

    expect(screen.getByRole('status', { name: 'Search summary' })).toHaveTextContent('Selected1');
    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).not.toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'select search result News Global' })).toBeChecked();
  });

  it('imports selected rows together and retains excluded/unresolved selections', async () => {
    jest.mocked(searchService.importResults).mockResolvedValueOnce({
      policy_revision: 1, added: 1, existing: 0, excluded: 1, unresolved: 0, deferred: 0,
      items: [{ infohash: INFOHASH, content_id: CONTENT_ID, outcome: 'added', rule_ids: [] }, { infohash: 'b'.repeat(40), outcome: 'excluded', rule_ids: [1] }],
    });
    const { queryClient } = renderPage();
    const invalidate = jest.spyOn(queryClient, 'invalidateQueries');
    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'arena' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'select all search results' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add 2 selected channels' }));
    await waitFor(() => expect(searchService.importResults).toHaveBeenCalledWith(defaultResults.results));
    expect(await screen.findByText(/1 added, 0 existing, 1 excluded/)).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select search result News Global' })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).not.toBeChecked();
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ['acestream-channels'] });
  });

  it('save search uses the submitted query and leaves automatic refresh off', async () => {
    renderPage();
    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'submitted' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search' }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Search Query' }), { target: { value: 'unsubmitted' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save search' }));
    expect(screen.getByRole('textbox', { name: 'Query' })).toHaveValue('submitted');
    expect(screen.getByRole('checkbox', { name: /Import matching results/ })).not.toBeChecked();
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
    expect(screen.getByRole('status', { name: 'Search summary' })).toHaveTextContent(/for ‘arena’/);
    expect(screen.getByRole('status', { name: 'Search summary' })).toHaveTextContent('Selected1');
    expect(screen.getByRole('button', { name: 'Add Arena Premium' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
  });
});

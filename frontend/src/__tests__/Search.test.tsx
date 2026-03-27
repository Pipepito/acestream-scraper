import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen } from '@testing-library/react';

import Search from '../pages/Search';
import { createAppTheme } from '../theme';

const mockUseSearch = jest.fn();
const mockUseAddAcestreamChannel = jest.fn();

jest.mock('../hooks/useSearch', () => ({
  useSearch: (...args: unknown[]) => mockUseSearch(...args),
  useAddAcestreamChannel: (...args: unknown[]) => mockUseAddAcestreamChannel(...args),
}));

describe('Search page', () => {
  const renderPage = () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    return render(
      <ThemeProvider theme={createAppTheme('light')}>
        <QueryClientProvider client={queryClient}>
          <Search />
        </QueryClientProvider>
      </ThemeProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseSearch.mockReturnValue({
      data: {
        results: [
          { id: 'ace-1', name: 'Arena Premium', categories: ['sports'], bitrate: 1800 },
          { id: 'ace-2', name: 'News Global', categories: ['news'], bitrate: 1200 },
        ],
        pagination: { total_results: 2, total_pages: 1 },
      },
      isLoading: false,
      error: null,
    });
    mockUseAddAcestreamChannel.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
  });

  it('renders shared header and section-first search hierarchy', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Search Channels' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Search Filters' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Search Results' })).toBeInTheDocument();
  });

  it('uses accessible selection and add actions in the results table', () => {
    renderPage();

    expect(screen.getByRole('checkbox', { name: 'select all search results' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select search result Arena Premium' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Arena Premium' })).toBeInTheDocument();
  });

  it('shows the bulk add action once a result is selected', () => {
    renderPage();

    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));

    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
  });
});

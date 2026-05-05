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

describe('Search bold layout', () => {
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

  it('renders a guided search action area with selection momentum feedback', () => {
    renderPage();

    expect(screen.getByText('Search pulse')).toBeInTheDocument();
    expect(screen.getByText(/search the upstream catalog, compare likely matches, and add channels/i)).toBeInTheDocument();
    expect(screen.getByText(/selected channels stay ready for batch add/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('checkbox', { name: 'select search result Arena Premium' }));

    expect(screen.getByText(/^Selection momentum$/i)).toBeInTheDocument();
    expect(screen.getByText(/1 selected channel ready to add/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add 1 selected channels' })).toBeInTheDocument();
  });
});

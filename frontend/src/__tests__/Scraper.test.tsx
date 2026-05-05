import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';

import Scraper from '../pages/Scraper';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseURLs = jest.fn();
const mockUseCreateURL = jest.fn();
const mockUseUpdateURL = jest.fn();
const mockUseDeleteURL = jest.fn();
const mockUseScrapeAllURLs = jest.fn();

jest.mock('../hooks/useScrapers', () => ({
  useURLs: (...args: unknown[]) => mockUseURLs(...args),
  useCreateURL: (...args: unknown[]) => mockUseCreateURL(...args),
  useUpdateURL: (...args: unknown[]) => mockUseUpdateURL(...args),
  useDeleteURL: (...args: unknown[]) => mockUseDeleteURL(...args),
  useScrapeAllURLs: (...args: unknown[]) => mockUseScrapeAllURLs(...args),
}));

describe('Scraper', () => {
  const renderPage = () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return render(
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={createAppTheme('light')}>
          <TestMemoryRouter>
            <Scraper />
          </TestMemoryRouter>
        </ThemeProvider>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseURLs.mockReturnValue({
      data: [
        {
          id: 11,
          url: 'https://source-one.test/feed',
          url_type: 'auto',
          enabled: true,
          last_processed: '2026-03-30T10:00:00Z',
          channels_found: 32,
        },
      ],
      isLoading: false,
      refetch: jest.fn(),
    });
    mockUseCreateURL.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseUpdateURL.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseDeleteURL.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseScrapeAllURLs.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
  });

  it('adds explicit accessible labels to row action buttons', () => {
    renderPage();

    expect(screen.getByRole('button', { name: 'Scrape URL https://source-one.test/feed' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit URL https://source-one.test/feed' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete URL https://source-one.test/feed' })).toBeInTheDocument();
  });

  it('opens with a source-intake summary that shows the pipeline and next step', () => {
    renderPage();

    expect(screen.getByText(/^sources$/i)).toBeInTheDocument();
    expect(screen.getByText(/^extracted channels$/i)).toBeInTheDocument();
    expect(screen.getByText(/^tv organization$/i)).toBeInTheDocument();
    expect(screen.getByText(/source intake stage/i)).toBeInTheDocument();
    expect(screen.getByText(/^source readiness$/i)).toBeInTheDocument();
    expect(screen.getByText(/^next step$/i)).toBeInTheDocument();
    expect(screen.getByText(/review extracted channels/i)).toBeInTheDocument();
  });

  it('shows a safe no-enabled-sources branch in the intake summary', () => {
    mockUseURLs.mockReturnValue({
      data: [
        {
          id: 21,
          url: 'https://source-disabled.test/feed',
          url_type: 'auto',
          enabled: false,
          last_processed: null,
          channels_found: 0,
        },
      ],
      isLoading: false,
      refetch: jest.fn(),
    });

    renderPage();

    expect(screen.getByText(/none are enabled for intake/i)).toBeInTheDocument();
    expect(screen.getByText(/enable at least one source, then run a scrape/i)).toBeInTheDocument();
  });

  it('shows a safe no-sources-configured branch in the intake summary', () => {
    mockUseURLs.mockReturnValue({
      data: [],
      isLoading: false,
      refetch: jest.fn(),
    });

    renderPage();

    expect(screen.getByText(/no source urls configured yet/i)).toBeInTheDocument();
    expect(screen.getByText(/add your first source url to start the pipeline/i)).toBeInTheDocument();
  });
});

import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';

import Scraper from '../pages/Scraper';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseURLs = jest.fn();
const mockUseCreateURL = jest.fn();
const mockUseUpdateURL = jest.fn();
const mockUseDeleteURL = jest.fn();
const mockUseScrapeURL = jest.fn();
const mockUseScrapeAllURLs = jest.fn();

jest.mock('../hooks/useScrapers', () => ({
  useURLs: (...args: unknown[]) => mockUseURLs(...args),
  useCreateURL: (...args: unknown[]) => mockUseCreateURL(...args),
  useUpdateURL: (...args: unknown[]) => mockUseUpdateURL(...args),
  useDeleteURL: (...args: unknown[]) => mockUseDeleteURL(...args),
  useScrapeURL: (...args: unknown[]) => mockUseScrapeURL(...args),
  useScrapeAllURLs: (...args: unknown[]) => mockUseScrapeAllURLs(...args),
}));

describe('Scraper', () => {
  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter>
          <Scraper />
        </TestMemoryRouter>
      </ThemeProvider>
    );

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
    mockUseScrapeURL.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseScrapeAllURLs.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
  });

  it('adds explicit accessible labels to row action buttons', () => {
    renderPage();

    expect(screen.getByRole('button', { name: 'Scrape URL https://source-one.test/feed' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit URL https://source-one.test/feed' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete URL https://source-one.test/feed' })).toBeInTheDocument();
  });
});

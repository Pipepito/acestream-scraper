import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import Scraper from '../pages/Scraper';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseURLs = jest.fn();
const mockUseCreateURL = jest.fn();
const mockUseUpdateURL = jest.fn();
const mockUsePatchURL = jest.fn();
const mockUseDeleteURL = jest.fn();
const mockUseScrapeAllURLs = jest.fn();

jest.mock('../hooks/useScrapers', () => ({
  useURLs: (...args: unknown[]) => mockUseURLs(...args),
  useCreateURL: (...args: unknown[]) => mockUseCreateURL(...args),
  useUpdateURL: (...args: unknown[]) => mockUseUpdateURL(...args),
  usePatchURL: (...args: unknown[]) => mockUsePatchURL(...args),
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
    mockUseCreateURL.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUseUpdateURL.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUsePatchURL.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue({}), isPending: false });
    mockUseDeleteURL.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseScrapeAllURLs.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
  });

  it('shows the outcome of the last scrape so failing sources are visible', () => {
    mockUseURLs.mockReturnValue({
      data: [
        { id: 11, url: 'https://source-one.test/feed', url_type: 'auto', enabled: true, status: 'OK', last_processed: '2026-03-30T10:00:00Z', channels_found: 32 },
        { id: 12, url: 'https://broken.test/feed', url_type: 'regular', enabled: true, status: "Error: 404, message='Not Found'", last_processed: '2026-03-30T10:05:00Z', channels_found: 0 },
        { id: 13, url: 'https://new.test/feed', url_type: 'regular', enabled: true, status: 'active', last_processed: null, channels_found: 0 },
      ],
      isLoading: false,
      refetch: jest.fn(),
    });

    renderPage();

    expect(screen.getByRole('columnheader', { name: 'Last result' })).toBeInTheDocument();
    expect(screen.getByText('OK')).toBeInTheDocument();
    const failed = screen.getByLabelText("Last scrape failed: Error: 404, message='Not Found'");
    expect(failed).toHaveTextContent('Error');
    expect(screen.getByText('Not scraped yet')).toBeInTheDocument();
  });






  it('summarises sources in one status line and labels the row actions', () => {
    renderPage();

    const status = screen.getByRole('status', { name: 'Source status' });
    expect(status).toHaveTextContent('1 of 1 enabled');
    expect(status).toHaveTextContent('32');
    expect(status).toHaveTextContent(/ago/);
    expect(screen.queryByText(/source intake stage/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Scrape URL https://source-one.test/feed' })).toHaveTextContent('Scrape');
    expect(screen.getByText('Auto-detect')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'More actions for https://source-one.test/feed' }));
    expect(screen.getByRole('menuitem', { name: 'Edit' })).toBeInTheDocument();
    expect(screen.getByRole('menuitemcheckbox', { name: 'Harvest bare IDs' })).toHaveAttribute('aria-checked', 'false');
    expect(screen.getByRole('menuitem', { name: 'Delete' })).toBeInTheDocument();
  });

  it('toggles bare content ID harvesting from the row menu', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({});
    mockUsePatchURL.mockReturnValue({ mutateAsync, isPending: false });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'More actions for https://source-one.test/feed' }));
    fireEvent.click(screen.getByRole('menuitemcheckbox', { name: 'Harvest bare IDs' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({ id: 11, data: { scrape_bare_ids: true } });
    });
  });

  it('enables and disables a source from the table switch', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({});
    mockUsePatchURL.mockReturnValue({ mutateAsync, isPending: false });

    renderPage();

    const toggle = screen.getByRole('checkbox', { name: 'Enable https://source-one.test/feed' });
    expect(toggle).toBeChecked();
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({ id: 11, data: { enabled: false } });
    });
    expect(await screen.findByText(/Source disabled/)).toBeInTheDocument();
  });

  it('asks for confirmation in the app dialog before deleting', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseDeleteURL.mockReturnValue({ mutateAsync });
    const confirmSpy = jest.spyOn(window, 'confirm');

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'More actions for https://source-one.test/feed' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete this source?' });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(11));
    expect(confirmSpy).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('shows an empty state instead of an empty table', () => {
    mockUseURLs.mockReturnValue({ data: [], isLoading: false, refetch: jest.fn() });
    renderPage();
    expect(screen.getByText('No source URLs yet. Add one to start scraping.')).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'Source status' })).toHaveTextContent('0 of 0 enabled');
  });
});


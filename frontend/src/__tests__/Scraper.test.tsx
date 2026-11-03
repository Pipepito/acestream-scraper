import { scraperService } from '../services/scraperService';
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

jest.mock('../services/catalogueService', () => ({ catalogueService: { list: jest.fn().mockResolvedValue([]), get: jest.fn(), preview: jest.fn(), save: jest.fn(), previewEvent: jest.fn(), remove: jest.fn(), assignFolder: jest.fn(), folderMatches: jest.fn(), applyFolderMatches: jest.fn() } }));
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => ({ data: [], isLoading: false, isError: false, refetch: jest.fn() }) }));
jest.mock('../hooks/useScrapers', () => ({
  useURLs: (...args: unknown[]) => mockUseURLs(...args),
  useCreateURL: (...args: unknown[]) => mockUseCreateURL(...args),
  useUpdateURL: (...args: unknown[]) => mockUseUpdateURL(...args),
  usePatchURL: (...args: unknown[]) => mockUsePatchURL(...args),
  useDeleteURL: (...args: unknown[]) => mockUseDeleteURL(...args),
  useScrapeAllURLs: (...args: unknown[]) => mockUseScrapeAllURLs(...args),
}));

describe('Scraper', () => {
  const renderPage = (path = '/scraper') => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return render(
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={createAppTheme('light')}>
          <TestMemoryRouter initialEntries={[path]}>
            <Scraper />
          </TestMemoryRouter>
        </ThemeProvider>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(scraperService, 'getProviders').mockResolvedValue([{ id: 'atresplayer', name: 'Atresmedia', url: 'https://www.atresplayer.com' }, { id: 'mediaset', name: 'Mediaset', url: 'https://www.mediasetinfinity.es' }]);

    mockUseURLs.mockReturnValue({
      data: [
        {
          id: 11,
          url: 'https://source-one.test/feed',
          url_type: 'auto',
          enabled: true,
          last_processed: '2026-03-30T10:00:00Z',
          channels_found: 32,
          assigned_count: 1,
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

  it('selects a built-in broadcaster and saves its friendly name without scraping', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Add URL' }));
    await waitFor(() => expect(scraperService.getProviders).toHaveBeenCalled());
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Built-in provider' }));
    fireEvent.click(await screen.findByRole('option', { name: 'Atresmedia' }));
    expect(screen.getByLabelText('URL')).toHaveValue('https://www.atresplayer.com');
    expect(screen.getByLabelText('Friendly name (optional)')).toHaveValue('Atresmedia');
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Built-in provider' }));
    fireEvent.click(screen.getByRole('option', { name: 'Mediaset' }));
    expect(screen.getByLabelText('Friendly name (optional)')).toHaveValue('Mediaset');
    fireEvent.change(screen.getByLabelText('Friendly name (optional)'), { target: { value: 'My broadcaster' } });
    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Built-in provider' }));
    fireEvent.click(screen.getByRole('option', { name: 'Atresmedia' }));
    expect(screen.getByLabelText('Friendly name (optional)')).toHaveValue('My broadcaster');
    fireEvent.click(screen.getByRole('button', { name: 'Add' }));
    await waitFor(() => expect(mockUseCreateURL().mutateAsync).toHaveBeenCalledWith(expect.objectContaining({ name: 'My broadcaster', url_type: 'broadcaster', url: 'https://www.atresplayer.com' })));
    expect(mockUseScrapeAllURLs().mutateAsync).not.toHaveBeenCalled();
  });

  it('shows the outcome of the last scrape so failing sources are visible', () => {
    mockUseURLs.mockReturnValue({
      data: [
        { id: 11, url: 'https://source-one.test/feed', url_type: 'auto', enabled: true, status: 'OK', last_processed: '2026-03-30T10:00:00Z', channels_found: 32, assigned_count: 1 },
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

  it('offers to remove a source\'s streams and defaults to removing them', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ deleted_streams: 32 });
    mockUseDeleteURL.mockReturnValue({ mutateAsync });
    const confirmSpy = jest.spyOn(window, 'confirm');

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'More actions for https://source-one.test/feed' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete this source?' });
    const checkbox = within(dialog).getByRole('checkbox', { name: 'Also remove its 32 streams (1 linked to TV channels)' });
    expect(checkbox).toBeChecked();
    expect(dialog).toHaveTextContent('TV channels are kept.');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete source' }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ id: 11, deleteStreams: true }));
    expect(await screen.findByText('Source deleted with 32 streams.')).toBeInTheDocument();
    expect(confirmSpy).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('keeps streams when the checkbox is unticked', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ deleted_streams: 0 });
    mockUseDeleteURL.mockReturnValue({ mutateAsync });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'More actions for https://source-one.test/feed' }));
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete this source?' });
    fireEvent.click(within(dialog).getByRole('checkbox', { name: /Also remove its 32 streams/ }));
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete source' }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ id: 11, deleteStreams: false }));
    expect(await screen.findByText('Source deleted. Its streams stay in the inventory.')).toBeInTheDocument();
  });

  it('cleans up streams from removed sources after confirmation', async () => {
    jest.spyOn(scraperService, 'orphanedSources').mockResolvedValue([{ source_url: 'https://gone.example/', count: 10, assigned_count: 2 }]);
    const cleanup = jest.spyOn(scraperService, 'cleanupOrphanedSources').mockResolvedValue({ deleted: { 'https://gone.example/': 10 } });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Clean up removed sources…' }));
    const dialog = await screen.findByRole('dialog', { name: 'Clean up removed sources' });
    expect(await within(dialog).findByText('https://gone.example/')).toBeInTheDocument();
    expect(within(dialog).getByRole('checkbox', { name: /https:\/\/gone\.example\// })).toBeChecked();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Remove selected' }));
    const confirmDialog = await screen.findByRole('dialog', { name: 'Remove streams from removed sources?' });
    fireEvent.click(within(confirmDialog).getByRole('button', { name: 'Remove streams' }));
    await waitFor(() => expect(cleanup).toHaveBeenCalledWith(['https://gone.example/']));
    expect(await screen.findByText('Removed 10 streams from 1 source.')).toBeInTheDocument();
  });

  it('shows an empty state instead of an empty table', () => {
    mockUseURLs.mockReturnValue({ data: [], isLoading: false, refetch: jest.fn() });
    renderPage();
    expect(screen.getByText('No source URLs yet. Add one to start scraping.')).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'Source status' })).toHaveTextContent('0 of 0 enabled');
  });

  it('previews a catalogue inside the W3U tab', async () => {
    const { catalogueService } = jest.requireMock('../services/catalogueService') as { catalogueService: { preview: jest.Mock } };
    catalogueService.preview.mockResolvedValue({ name: 'Example catalogue', origin: 'example.test', revision: 0, can_refresh: true, preview_token: 'test-preview',
      counts: { accepted: 1, duplicates: 0, invalid: 0, unsupported: 0, failed_fetches: 0 }, selected_branches: ['root'], mode: 'compatible',
      entries: [{ id: 'root', parent_id: null, name: 'Example catalogue', kind: 'folder' }, { id: 'live', parent_id: 'root', name: 'Live channels', kind: 'folder' }] });
    renderPage('/scraper?tab=w3u');
    fireEvent.click(await screen.findByRole('button', { name: 'Add catalogue' }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Catalogue URL' }), { target: { value: 'https://example.test/list.w3u' } });
    fireEvent.click(screen.getByRole('button', { name: 'Preview URL' }));
    expect(await screen.findByRole('heading', { name: 'Review import' })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'Include Live channels' })).toBeInTheDocument();
  });

  it('hosts W3U catalogues as a tab under the Scraper heading', async () => {
    renderPage('/scraper?tab=w3u');
    expect(screen.getByRole('tab', { name: 'W3U catalogues', selected: true })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Scraper' })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: 'Add catalogue' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { level: 1, name: 'Catalogues' })).not.toBeInTheDocument();
    expect(screen.queryByRole('menuitem', { name: 'W3U catalogues' })).not.toBeInTheDocument();
  });
});


// Provider selection only saves a definition; importing remains a separate action.

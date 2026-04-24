import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from 'react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import EPG from '../pages/EPG';
import EPGMappings from '../pages/EPGMappings';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  },
}));

const mockUseEPGSources = jest.fn();
const mockUseEPGChannels = jest.fn();
const mockUseCreateEPGSource = jest.fn();
const mockUseUpdateEPGSource = jest.fn();
const mockUseDeleteEPGSource = jest.fn();
const mockUseRefreshAllEPGSources = jest.fn();
const mockUseDownloadEPGXML = jest.fn();
const mockUseAllEPGStringMappings = jest.fn();
const mockUseDeleteGlobalEPGStringMapping = jest.fn();
const mockUseTVChannelCatalog = jest.fn();

jest.mock('../hooks/useEPG', () => ({
  useEPGSources: (...args: unknown[]) => mockUseEPGSources(...args),
  useEPGChannels: (...args: unknown[]) => mockUseEPGChannels(...args),
  useCreateEPGSource: (...args: unknown[]) => mockUseCreateEPGSource(...args),
  useUpdateEPGSource: (...args: unknown[]) => mockUseUpdateEPGSource(...args),
  useDeleteEPGSource: (...args: unknown[]) => mockUseDeleteEPGSource(...args),
  useRefreshAllEPGSources: (...args: unknown[]) => mockUseRefreshAllEPGSources(...args),
  useDownloadEPGXML: (...args: unknown[]) => mockUseDownloadEPGXML(...args),
  useAllEPGStringMappings: (...args: unknown[]) => mockUseAllEPGStringMappings(...args),
  useDeleteGlobalEPGStringMapping: (...args: unknown[]) => mockUseDeleteGlobalEPGStringMapping(...args),
}));

jest.mock('../hooks/useTVChannels', () => ({
  useTVChannelCatalog: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
  useAllTVChannels: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
}));

jest.mock('../services/tvChannelService', () => ({
  tvChannelService: {
    createFromEpg: jest.fn().mockResolvedValue({ created_count: 0, skipped_count: 0, associated_count: 0 }),
  },
}));

describe('EPG page pagination', () => {
  const renderPage = () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    return render(
      <ThemeProvider theme={createAppTheme('light')}>
        <QueryClientProvider client={queryClient}>
          <TestMemoryRouter>
            <EPG />
          </TestMemoryRouter>
        </QueryClientProvider>
      </ThemeProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseEPGSources.mockReturnValue({
      data: [
        { id: 1, name: 'Source One', url: 'https://one.test', enabled: true, error_count: 0 },
        { id: 2, name: 'Source Two', url: 'https://two.test', enabled: true, error_count: 0 },
      ],
      isLoading: false,
    });

    mockUseEPGChannels.mockImplementation((sourceId?: number, page = 1, pageSize = 50) => ({
      data: {
        items: sourceId === 2 ? [] : [
          { id: page * 10, epg_source_id: 1, channel_xml_id: `alpha-${page}`, name: `Alpha ${page}`, language: 'en', created_at: '', updated_at: '' },
          { id: page * 10 + 1, epg_source_id: 1, channel_xml_id: `beta-${page}`, name: `Beta ${page}`, language: 'en', created_at: '', updated_at: '' },
        ],
        total: sourceId === 2 ? 0 : 250,
      },
      isLoading: false,
      isPreviousData: false,
    }));

    mockUseCreateEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseRefreshAllEPGSources.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseDownloadEPGXML.mockReturnValue({ mutateAsync: jest.fn(), isLoading: false });
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        { id: 1001, name: 'Mapped Alpha', epg_id: 'alpha-1' },
        { id: 2002, name: 'Mapped Zeta', epg_id: 'zeta-9999' },
      ],
    });
  });

  it('requests paginated channels with global defaults', () => {
    renderPage();

    expect(mockUseEPGChannels).toHaveBeenCalledWith(undefined, 1, 50);
    expect(screen.getByText('Alpha 1')).toBeInTheDocument();
    expect(screen.getByText('Showing 1-50 of 250 channels')).toBeInTheDocument();
  });

  it('renders section-first hierarchy without tab-led composition', () => {
    renderPage();

    const sourceOperations = screen.getByRole('heading', { level: 2, name: 'Source Operations' });
    const channelMatching = screen.getByRole('heading', { level: 2, name: 'Channel Matching' });
    const channelInventory = screen.getByRole('heading', { level: 2, name: 'Channel Inventory' });
    const xmlOutput = screen.getByRole('heading', { level: 2, name: 'XML Output' });

    expect(screen.getByRole('heading', { level: 1, name: 'EPG Management' })).toBeInTheDocument();
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument();
    expect(sourceOperations.compareDocumentPosition(channelMatching) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(channelMatching.compareDocumentPosition(channelInventory) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(channelInventory.compareDocumentPosition(xmlOutput) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('opens with an operational EPG summary that explains readiness and next steps', () => {
    renderPage();

    expect(screen.getByText('EPG pulse')).toBeInTheDocument();
    expect(screen.getByText(/source inventory is ready for matching and xml output/i)).toBeInTheDocument();
    expect(screen.getByText(/^Source count$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Matching status$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Next step$/i)).toBeInTheDocument();
    expect(screen.getByText(/review unmapped channels or generate xml when source coverage looks right/i)).toBeInTheDocument();
  });

  it('exposes accessible names for key row actions', () => {
    renderPage();

    expect(screen.getByRole('button', { name: 'Refresh source Source One' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit source Source One' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete source Source One' })).toBeInTheDocument();

    expect(screen.getByRole('button', { name: 'View programs for Alpha 1' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Link Alpha 1 to a TV channel' })).not.toBeInTheDocument();
  });

  it('uses the full TV channel catalog for mapped-state checks', () => {
    renderPage();

    expect(mockUseTVChannelCatalog).toHaveBeenCalled();
    expect(screen.getByRole('checkbox', { name: 'select EPG channel Alpha 1' })).toBeDisabled();
  });

  it('keeps mapping-dependent inventory controls disabled while the TV catalog is loading', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderPage();

    expect(screen.getByRole('checkbox', { name: 'select all EPG channels' })).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: 'select EPG channel Beta 1' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create TV Channels (0)' })).toBeDisabled();
  });

  it('resets to page 1 when the source filter changes', () => {
    renderPage();

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'EPG Source' }));
    fireEvent.click(screen.getByRole('option', { name: 'Source Two' }));

    expect(mockUseEPGChannels).toHaveBeenLastCalledWith(2, 1, 50);
    expect(screen.getByText('No EPG channels found')).toBeInTheDocument();
  });

  it('does not snap back to page 1 while the next page is loading', () => {
    mockUseEPGChannels
      .mockImplementationOnce(() => ({
        data: {
          items: [
            { id: 10, epg_source_id: 1, channel_xml_id: 'alpha-1', name: 'Alpha 1', language: 'en', created_at: '', updated_at: '' },
          ],
          total: 250,
        },
        isLoading: false,
        isPreviousData: false,
      }))
      .mockImplementationOnce((_sourceId?: number, page = 1, pageSize = 50) => ({
        data: undefined,
        isLoading: true,
        isPreviousData: true,
      }));

    renderPage();
    fireEvent.mouseDown(screen.getByLabelText('Rows per page:'));
    fireEvent.click(screen.getByRole('option', { name: '100' }));
    fireEvent.click(screen.getByLabelText('Go to next page'));

    expect(mockUseEPGChannels).toHaveBeenLastCalledWith(undefined, 2, 100);
  });
});

describe('EPG mappings page', () => {
  const renderMappingsPage = () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    return render(
      <ThemeProvider theme={createAppTheme('light')}>
        <QueryClientProvider client={queryClient}>
          <TestMemoryRouter>
            <EPGMappings />
          </TestMemoryRouter>
        </QueryClientProvider>
      </ThemeProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseAllEPGStringMappings.mockReturnValue({
      data: [
        { id: 11, epg_channel_id: 101, search_pattern: 'Sport TV', is_exclusion: false },
        { id: 12, epg_channel_id: 202, search_pattern: 'Regional Feed', is_exclusion: true },
      ],
      isLoading: false,
      error: undefined,
      refetch: jest.fn(),
    });

    mockUseDeleteGlobalEPGStringMapping.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue(undefined),
      isLoading: false,
    });
  });

  it('renders global mappings in a dense operational table', () => {
    renderMappingsPage();

    expect(screen.getByRole('heading', { level: 1, name: 'EPG Mappings' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Global mapping rules' })).toBeInTheDocument();
    expect(screen.getByText('Sport TV')).toBeInTheDocument();
    expect(screen.getByText('Regional Feed')).toBeInTheDocument();
    expect(screen.getByText('Include')).toBeInTheDocument();
    expect(screen.getByText('Exclude')).toBeInTheDocument();
    expect(screen.getByText('101')).toBeInTheDocument();
    expect(screen.getByText('202')).toBeInTheDocument();
  });

  it('deletes a selected global mapping from the page', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseDeleteGlobalEPGStringMapping.mockReturnValue({
      mutateAsync,
      isLoading: false,
    });

    renderMappingsPage();

    fireEvent.click(screen.getByRole('button', { name: 'Delete mapping Sport TV' }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(11));
  });
});

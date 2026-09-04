import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, within } from '@testing-library/react';
import EPG from '../pages/EPG';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

jest.mock('../services/apiClient', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn(), patch: jest.fn(), delete: jest.fn() },
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

const lastCallOfListQuery = () =>
  mockUseEPGChannels.mock.calls.filter((call) => call[2] !== 1).at(-1);

describe('EPG page', () => {
  const renderPage = (entry = '/epg') => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return render(
      <ThemeProvider theme={createAppTheme('light')}>
        <QueryClientProvider client={queryClient}>
          <TestMemoryRouter initialEntries={[entry]}>
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
        { id: 1, name: 'Source One', url: 'https://one.test', enabled: true, error_count: 0, last_updated: '2026-09-02T09:00:00Z' },
        { id: 2, name: 'Source Two', url: 'https://two.test', enabled: false, error_count: 0, last_updated: null },
      ],
      isLoading: false,
    });
    mockUseEPGChannels.mockImplementation((sourceId?: number, page = 1, pageSize = 50) => ({
      data: {
        items:
          pageSize === 1
            ? []
            : sourceId === 2
              ? []
              : [
                  { id: page * 10, epg_source_id: 1, channel_xml_id: `alpha-${page}`, name: `Alpha ${page}`, language: 'en', created_at: '', updated_at: '' },
                  { id: page * 10 + 1, epg_source_id: 1, channel_xml_id: `beta-${page}`, name: `Beta ${page}`, language: '', created_at: '', updated_at: '' },
                ],
        total: pageSize === 1 ? 638 : sourceId === 2 ? 0 : 250,
      },
      isLoading: false,
      isPreviousData: false,
    }));
    mockUseCreateEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseRefreshAllEPGSources.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUseDownloadEPGXML.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUseAllEPGStringMappings.mockReturnValue({ data: [], isLoading: false });
    mockUseDeleteGlobalEPGStringMapping.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        { id: 1001, name: 'Mapped Alpha', epg_id: 'alpha-1' },
        { id: 2002, name: 'Mapped Zeta', epg_id: 'zeta-9999' },
        { id: 3003, name: 'Unlinked', epg_id: '' },
      ],
    });
  });

  it('opens on the Sources tab with real numbers in the summary line', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'EPG' })).toBeInTheDocument();
    const summary = screen.getByRole('status', { name: 'EPG summary' });
    expect(summary).toHaveTextContent('Sources2 (1 enabled)');
    expect(summary).toHaveTextContent('Guide channels638');
    expect(summary).toHaveTextContent('Linked to a TV channel2');
    expect(summary).toHaveTextContent(/Last refresh.*ago/);
    expect(screen.queryByText('EPG pulse')).not.toBeInTheDocument();

    const tabs = screen.getAllByRole('tab').map((tab) => tab.textContent);
    expect(tabs).toEqual(['Sources', 'Channels', 'Matching', 'Rules', 'Export']);
    expect(screen.getByRole('tab', { name: 'Sources', selected: true })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh source Source One' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit source Source One' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete source Source One' })).toBeInTheDocument();
    expect(screen.queryByText('Alpha 1')).not.toBeInTheDocument();
  });

  it('shows source refresh failures as plain text under the status', () => {
    mockUseEPGSources.mockReturnValue({
      data: [{ id: 1, name: 'Broken', url: 'https://one.test', enabled: true, error_count: 2, last_error: 'HTTP 503 from upstream', last_updated: null }],
      isLoading: false,
    });
    renderPage();
    expect(screen.getByText('2 failed refreshes · HTTP 503 from upstream')).toBeInTheDocument();
    expect(screen.getByRole('status', { name: 'EPG summary' })).toHaveTextContent('Failing1');
  });

  it('binds the active tab to ?tab= and the Export XML header action', () => {
    renderPage('/epg?tab=channels');
    expect(screen.getByRole('tab', { name: 'Channels', selected: true })).toBeInTheDocument();
    expect(screen.getByText('Alpha 1')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Export XML' }));
    expect(screen.getByRole('tab', { name: 'Export', selected: true })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Export XML' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Rules' }));
    expect(screen.getByRole('heading', { level: 2, name: 'Matching rules' })).toBeInTheDocument();
    expect(mockUseAllEPGStringMappings).toHaveBeenCalled();
  });

  it('lists guide channels with links, link state and only informative columns', () => {
    renderPage('/epg?tab=channels');

    expect(mockUseEPGChannels).toHaveBeenLastCalledWith(undefined, 1, 50);
    expect(screen.getByText('Showing 1-50 of 250 channels')).toBeInTheDocument();
    const table = screen.getByRole('table', { name: 'Guide channels' });
    expect(within(table).getByRole('link', { name: 'Alpha 1' })).toHaveAttribute('href', '/epg/channels/10');
    expect(within(table).getByRole('columnheader', { name: 'Source' })).toBeInTheDocument();
    expect(within(table).getByRole('columnheader', { name: 'Language' })).toBeInTheDocument();
    expect(within(table).getByText('Linked')).toBeInTheDocument();
    expect(within(table).getByText('Not linked')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'select EPG channel Alpha 1' })).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: 'select EPG channel Beta 1' })).toBeEnabled();
  });

  it('hides the Source column with one source and Language when no channel has one', () => {
    mockUseEPGSources.mockReturnValue({ data: [{ id: 1, name: 'Only', url: 'https://one.test', enabled: true, error_count: 0 }], isLoading: false });
    mockUseEPGChannels.mockImplementation((_sourceId?: number, _page = 1, pageSize = 50) => ({
      data: { items: pageSize === 1 ? [] : [{ id: 10, epg_source_id: 1, channel_xml_id: 'alpha-1', name: 'Alpha 1', language: '', created_at: '', updated_at: '' }], total: 1 },
      isLoading: false,
      isPreviousData: false,
    }));
    renderPage('/epg?tab=channels');

    const table = screen.getByRole('table', { name: 'Guide channels' });
    expect(within(table).queryByRole('columnheader', { name: 'Source' })).not.toBeInTheDocument();
    expect(within(table).queryByRole('columnheader', { name: 'Language' })).not.toBeInTheDocument();
  });

  it('keeps mapping-dependent inventory controls disabled while the TV catalog is loading', () => {
    mockUseTVChannelCatalog.mockReturnValue({ data: undefined, isLoading: true, error: null });
    renderPage('/epg?tab=channels');

    expect(screen.getByRole('checkbox', { name: 'select all EPG channels' })).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: 'select EPG channel Beta 1' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create TV Channels (0)' })).toBeDisabled();
  });

  it('resets to page 1 when the source filter changes', () => {
    renderPage('/epg?tab=channels');

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'EPG Source' }));
    fireEvent.click(screen.getByRole('option', { name: 'Source Two' }));

    expect(lastCallOfListQuery()).toEqual([2, 1, 50]);
    expect(screen.getByText('No EPG channels found')).toBeInTheDocument();
  });

  it('does not snap back to page 1 while the next page is loading', () => {
    const loaded = mockUseEPGChannels.getMockImplementation() as (sourceId?: number, page?: number, pageSize?: number) => unknown;
    mockUseEPGChannels.mockImplementation((sourceId?: number, page = 1, pageSize = 50) =>
      page === 2 && pageSize !== 1 ? { data: undefined, isLoading: true, isPreviousData: true } : loaded(sourceId, page, pageSize)
    );
    renderPage('/epg?tab=channels');

    fireEvent.mouseDown(screen.getByLabelText('Rows per page:'));
    fireEvent.click(screen.getByRole('option', { name: '100' }));
    fireEvent.click(screen.getByLabelText('Go to next page'));

    expect(lastCallOfListQuery()).toEqual([undefined, 2, 100]);
  });

  it('shows the matching controls only on the Matching tab', () => {
    renderPage('/epg?tab=matching');
    expect(screen.getByRole('combobox', { name: 'Match Strictness' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze Matches' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Create Matched TV Channels' })).toBeDisabled();
    expect(screen.queryByRole('table', { name: 'Guide channels' })).not.toBeInTheDocument();
  });
});

import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { MemoryRouter } from 'react-router-dom';
import { fireEvent, render, screen } from '@testing-library/react';

import EPG from '../pages/EPG';

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
const mockUseAllTVChannels = jest.fn();

jest.mock('../components/layout/PageHeader', () => ({
  __esModule: true,
  default: ({ title }: { title: string }) => <div>{title}</div>,
}));

jest.mock('../hooks/useEPG', () => ({
  useEPGSources: (...args: unknown[]) => mockUseEPGSources(...args),
  useEPGChannels: (...args: unknown[]) => mockUseEPGChannels(...args),
  useCreateEPGSource: (...args: unknown[]) => mockUseCreateEPGSource(...args),
  useUpdateEPGSource: (...args: unknown[]) => mockUseUpdateEPGSource(...args),
  useDeleteEPGSource: (...args: unknown[]) => mockUseDeleteEPGSource(...args),
  useRefreshAllEPGSources: (...args: unknown[]) => mockUseRefreshAllEPGSources(...args),
  useDownloadEPGXML: (...args: unknown[]) => mockUseDownloadEPGXML(...args),
}));

jest.mock('../hooks/useTVChannels', () => ({
  useAllTVChannels: (...args: unknown[]) => mockUseAllTVChannels(...args),
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
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <EPG />
        </MemoryRouter>
      </QueryClientProvider>
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
    mockUseAllTVChannels.mockReturnValue({ data: { items: [], total: 0 } });
  });

  it('requests paginated channels with global defaults', () => {
    renderPage();

    fireEvent.click(screen.getByRole('tab', { name: 'Channels' }));

    expect(mockUseEPGChannels).toHaveBeenCalledWith(undefined, 1, 50);
    expect(screen.getByText('Alpha 1')).toBeInTheDocument();
    expect(screen.getByText('Showing 1-50 of 250 channels')).toBeInTheDocument();
  });

  it('resets to page 1 when the source filter changes', () => {
    renderPage();

    fireEvent.click(screen.getByRole('tab', { name: 'Channels' }));

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'EPG Source' }));
    fireEvent.click(screen.getByText('Source Two'));

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
    fireEvent.click(screen.getByRole('tab', { name: 'Channels' }));
    fireEvent.mouseDown(screen.getByLabelText('Rows per page:'));
    fireEvent.click(screen.getByRole('option', { name: '100' }));
    fireEvent.click(screen.getByLabelText('Go to next page'));

    expect(mockUseEPGChannels).toHaveBeenLastCalledWith(undefined, 2, 100);
  });
});

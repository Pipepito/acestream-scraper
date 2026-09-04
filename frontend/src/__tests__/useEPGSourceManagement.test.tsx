import React from 'react';
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEPGSourceManagement } from '../hooks/useEPGSourceManagement';
import { epgService } from '../services/epgService';

jest.mock('../services/epgService', () => ({
  epgService: {
    getSource: jest.fn(),
    getSources: jest.fn(),
    refreshSource: jest.fn(),
    refreshAllSources: jest.fn(),
    getChannels: jest.fn(),
    createSource: jest.fn(),
    updateSource: jest.fn(),
    deleteSource: jest.fn(),
  },
}));

const mockedService = epgService as jest.Mocked<typeof epgService>;

const baseSource = {
  id: 7,
  url: 'https://guide.test/epg.xml',
  name: 'Guide',
  enabled: true,
  last_updated: '2026-09-01T10:00:00Z',
  error_count: 0,
  last_error: null,
};

const startedResponse = {
  source_id: 7,
  success: true,
  message: 'EPG refresh started for source: Guide',
  status: 'success',
  channels_found: null,
  programs_found: null,
  duration_seconds: null,
  error: null,
};

function renderManagement(showSnackbar: jest.Mock) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(() => useEPGSourceManagement(showSnackbar, { pollIntervalMs: 5, timeoutMs: 2000 }), { wrapper });
}

describe('useEPGSourceManagement refresh feedback', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedService.refreshSource.mockResolvedValue(startedResponse);
    mockedService.refreshAllSources.mockResolvedValue([startedResponse]);
    mockedService.getChannels.mockResolvedValue({ items: [], total: 638 });
  });

  it('reports the refresh as started, keeps the row busy, then reports the loaded channel count', async () => {
    const showSnackbar = jest.fn();
    mockedService.getSource
      .mockResolvedValueOnce(baseSource) // baseline
      .mockResolvedValueOnce(baseSource) // still running
      .mockResolvedValue({ ...baseSource, last_updated: '2026-09-02T12:00:00Z' });

    const { result } = renderManagement(showSnackbar);
    let pending: Promise<void> = Promise.resolve();
    act(() => {
      pending = result.current.handleRefreshSourceClick(7);
    });
    await waitFor(() => expect(result.current.refreshingSourceId).toBe(7));
    await act(async () => {
      await pending;
    });

    expect(showSnackbar).toHaveBeenNthCalledWith(1, expect.stringMatching(/refresh started for Guide/), 'info');
    expect(showSnackbar).toHaveBeenLastCalledWith('EPG source Guide refreshed: 638 channels loaded.', 'success');
    expect(showSnackbar.mock.calls.flat().join(' ')).not.toMatch(/undefined|null/);
    expect(mockedService.getChannels).toHaveBeenCalledWith(7, 0, 1);
    expect(result.current.refreshingSourceId).toBeNull();
  });

  it('surfaces the backend error recorded on the source when the refresh fails', async () => {
    const showSnackbar = jest.fn();
    mockedService.getSource
      .mockResolvedValueOnce(baseSource)
      .mockResolvedValue({ ...baseSource, last_updated: '2026-09-02T12:00:00Z', error_count: 1, last_error: 'HTTP error: 404' });

    const { result } = renderManagement(showSnackbar);
    await act(async () => {
      await result.current.handleRefreshSourceClick(7);
    });

    expect(showSnackbar).toHaveBeenLastCalledWith('EPG refresh failed for Guide: HTTP error: 404', 'error');
    expect(mockedService.getChannels).not.toHaveBeenCalled();
  });

  it('refresh all waits for every enabled source before summarising', async () => {
    const showSnackbar = jest.fn();
    const second = { ...baseSource, id: 8, name: 'Other', last_updated: null };
    mockedService.getSources.mockResolvedValue([baseSource, { ...second, enabled: false }, second]);
    mockedService.getSource.mockImplementation(async (id: number) =>
      id === 7 ? { ...baseSource, last_updated: '2026-09-02T12:00:00Z' } : { ...second, last_updated: '2026-09-02T12:00:01Z' }
    );

    const { result } = renderManagement(showSnackbar);
    await act(async () => {
      await result.current.handleRefreshAllClick();
    });

    expect(showSnackbar).toHaveBeenNthCalledWith(1, expect.stringMatching(/started for 2 sources/), 'info');
    expect(showSnackbar).toHaveBeenLastCalledWith('All 2 EPG sources refreshed successfully', 'success');
    expect(result.current.isRefreshingAll).toBe(false);
  });
});

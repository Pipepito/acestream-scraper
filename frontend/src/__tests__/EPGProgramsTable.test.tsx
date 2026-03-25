import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { render, screen } from '@testing-library/react';

import EPGProgramsTable from '../components/EPGProgramsTable';

const mockUseResolveEPGChannel = jest.fn();
const mockUseEPGPrograms = jest.fn();

jest.mock('../hooks/useEPG', () => ({
  useResolveEPGChannel: (...args: unknown[]) => mockUseResolveEPGChannel(...args),
  useEPGPrograms: (...args: unknown[]) => mockUseEPGPrograms(...args),
}));

describe('EPGProgramsTable', () => {
  const renderTable = () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    return render(
      <QueryClientProvider client={queryClient}>
        <EPGProgramsTable epgId="late-channel" epgSourceId={7} />
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseResolveEPGChannel.mockReturnValue({
      data: { id: 42, epg_source_id: 7, channel_xml_id: 'late-channel', name: 'Late Channel' },
      isLoading: false,
    });
    mockUseEPGPrograms.mockReturnValue({
      data: [
        { id: 1, title: 'Late Match', start_time: '2026-03-25T12:00:00Z', end_time: '2026-03-25T14:00:00Z' },
      ],
      isLoading: false,
    });
  });

  it('resolves the channel by source and xml id before loading programs', () => {
    renderTable();

    expect(mockUseResolveEPGChannel).toHaveBeenCalledWith(7, 'late-channel');
    expect(mockUseEPGPrograms).toHaveBeenCalledWith(42, expect.any(String), expect.any(String));
    expect(screen.getByText('Late Match')).toBeInTheDocument();
  });
});

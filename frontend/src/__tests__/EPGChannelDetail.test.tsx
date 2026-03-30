import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import EPGChannelDetail from '../pages/EPGChannelDetail';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseEPGChannel = jest.fn();
const mockUseEPGPrograms = jest.fn();
const mockUseEPGStringMappings = jest.fn();
const mockUseAddEPGStringMapping = jest.fn();
const mockUseDeleteEPGStringMapping = jest.fn();
const mockUseMapEPGChannel = jest.fn();
const mockUseUnmapEPGChannel = jest.fn();
const mockUseTVChannelCatalog = jest.fn();
const mockUseCreateTVChannel = jest.fn();

jest.mock('../hooks/useEPG', () => ({
  useEPGChannel: (...args: unknown[]) => mockUseEPGChannel(...args),
  useEPGPrograms: (...args: unknown[]) => mockUseEPGPrograms(...args),
  useEPGStringMappings: (...args: unknown[]) => mockUseEPGStringMappings(...args),
  useAddEPGStringMapping: (...args: unknown[]) => mockUseAddEPGStringMapping(...args),
  useDeleteEPGStringMapping: (...args: unknown[]) => mockUseDeleteEPGStringMapping(...args),
  useMapEPGChannel: (...args: unknown[]) => mockUseMapEPGChannel(...args),
  useUnmapEPGChannel: (...args: unknown[]) => mockUseUnmapEPGChannel(...args),
}));

jest.mock('../hooks/useTVChannels', () => ({
  useTVChannelCatalog: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
  useCreateTVChannel: (...args: unknown[]) => mockUseCreateTVChannel(...args),
  useAllTVChannels: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
}));

describe('EPGChannelDetail', () => {
  const renderPage = () => render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter initialEntries={['/epg/channels/42']}>
        <Routes>
          <Route path="/epg/channels/:id" element={<EPGChannelDetail />} />
        </Routes>
      </TestMemoryRouter>
    </ThemeProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseEPGChannel.mockReturnValue({
      data: {
        id: 42,
        name: 'Late Channel',
        channel_xml_id: 'late-channel',
        language: 'en',
        icon_url: 'https://img.test/late.png',
      },
      isLoading: false,
    });
    mockUseEPGPrograms.mockReturnValue({
      data: [
        {
          id: 1,
          title: 'Late Match',
          subtitle: 'Quarterfinal',
          category: 'Sports',
          description: 'Knockout match',
          start_time: '2026-03-25T12:00:00Z',
          end_time: '2026-03-25T14:00:00Z',
        },
      ],
      isLoading: false,
    });
    mockUseEPGStringMappings.mockReturnValue({
      data: [
        { id: 5, search_pattern: 'Late', is_exclusion: false },
      ],
      isLoading: false,
    });
    mockUseAddEPGStringMapping.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteEPGStringMapping.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseMapEPGChannel.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUnmapEPGChannel.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        { id: 7, name: 'Late Sports', category: 'Sports' },
        { id: 8, name: 'Night News', category: 'News' },
      ],
    });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue({ id: 55 }) });
  });

  it('renders top-down operational sections without a primary tab layout', () => {
    renderPage();

    const channelSummary = screen.getByRole('heading', { level: 2, name: 'Channel Summary' });
    const programSchedule = screen.getByRole('heading', { level: 2, name: 'Program Schedule' });
    const mappingRules = screen.getByRole('heading', { level: 2, name: 'String Mapping Rules' });

    expect(screen.getByRole('heading', { level: 1, name: 'Late Channel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back to EPG management' })).toBeInTheDocument();
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument();
    expect(channelSummary.compareDocumentPosition(programSchedule) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(programSchedule.compareDocumentPosition(mappingRules) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Delete string mapping Late' })).toBeInTheDocument();
  });

  it('uses explicit radio controls for TV channel selection', () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));

    expect(screen.getByRole('radiogroup', { name: 'Available TV channels' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Late Sports/ })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Night News/ })).toBeInTheDocument();
    expect(mockUseTVChannelCatalog).toHaveBeenCalled();
  });

  it('shows the selected TV channel clearly before confirming the mapping', () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));
    fireEvent.click(screen.getByRole('radio', { name: /Late Sports/ }));

    expect(screen.getByText('Selected TV channel: Late Sports')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeEnabled();
  });

  it('shows an explicit loading state while TV channels are still being fetched for mapping', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));

    expect(screen.getByText('Loading TV channels...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeDisabled();
  });

  it('shows an explicit error state when TV channels fail to load for mapping', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('catalog failed'),
    });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));

    expect(screen.getByText('Unable to load TV channels right now.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeDisabled();
  });

  it('shows an explicit empty state when no TV channels are available for mapping', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));

    expect(screen.getByText('No TV channels are available to map yet.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeDisabled();
  });

  it('adds contextual loading copy for schedule and string mapping sections', () => {
    mockUseEPGPrograms.mockReturnValue({
      data: undefined,
      isLoading: true,
    });
    mockUseEPGStringMappings.mockReturnValue({
      data: undefined,
      isLoading: true,
    });

    renderPage();

    expect(screen.getByText('Loading schedule for the selected date range...')).toBeInTheDocument();
    expect(screen.getByText('Loading string mapping rules...')).toBeInTheDocument();
  });

  it('creates TV channels through the shared mutation layer', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ id: 55 });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync, isLoading: false });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Create TV Channel' }));
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Late Channel',
        epg_id: 'late-channel',
        language: 'en',
      }));
    });

    await waitFor(() => {
      expect(screen.getByText('TV channel created successfully')).toBeInTheDocument();
    });
  });
});

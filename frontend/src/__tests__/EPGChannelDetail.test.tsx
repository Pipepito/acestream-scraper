import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';

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

const expectToAppearBefore = (earlier: HTMLElement, later: HTMLElement) => {
  expect(earlier.compareDocumentPosition(later) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
};

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

  it('distinguishes channel-load failure from a missing channel', () => {
    mockUseEPGChannel.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('channel failed'),
    });

    renderPage();

    expect(screen.getByText('Unable to load the EPG channel right now.')).toBeInTheDocument();
    expect(screen.queryByText('EPG channel not found')).not.toBeInTheDocument();
  });

  it('shows a not-found state when the channel data is missing without a load error', () => {
    mockUseEPGChannel.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    renderPage();

    expect(screen.getByText('EPG channel not found')).toBeInTheDocument();
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

  it('shows a relationship summary with shared label-to-support order and mapping-first guidance when candidates exist', () => {
    renderPage();

    const summaryLabel = screen.getByText(/^Relationship summary$/i);
    const identity = screen.getByText('EPG source: Late Channel');
    const relationshipState = screen.getByText(/^Relationship state$/i);
    const relationshipStateValue = screen.getByText(/No linked TV channel found in the loaded catalog yet/i);
    const nextStep = screen.getByText(/^Next step$/i);
    const nextStepValue = screen.getByText(/map this source to an existing TV channel.*tuning schedule rules|tuning schedule rules.*map this source to an existing TV channel/i);
    const supportCopy = screen.getByText(/XML ID late-channel/i);
    const channelSummary = screen.getByRole('heading', { level: 2, name: 'Channel Summary' });

    expect(summaryLabel).toBeInTheDocument();
    expect(identity).toBeInTheDocument();
    expect(supportCopy).toBeInTheDocument();
    expect(relationshipState).toBeInTheDocument();
    expect(nextStep).toBeInTheDocument();
    expectToAppearBefore(summaryLabel, identity);
    expectToAppearBefore(identity, relationshipState);
    expectToAppearBefore(relationshipState, relationshipStateValue);
    expectToAppearBefore(relationshipStateValue, nextStep);
    expectToAppearBefore(nextStep, nextStepValue);
    expectToAppearBefore(nextStepValue, supportCopy);
    expectToAppearBefore(supportCopy, channelSummary);
  });

  it('prioritizes create guidance when no inferred link or mapping choices exist', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });

    renderPage();

    expect(screen.getByText(/No linked TV channel found in the loaded catalog yet/i)).toBeInTheDocument();
    expect(screen.getByText(/create a TV channel first.*destination for mapping|destination for mapping.*create a TV channel first/i)).toBeInTheDocument();
  });

  it('treats a catalog epg_id match as an inferred link and prioritizes schedule review when no programs are visible', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        { id: 7, name: 'Late Sports', category: 'Sports', epg_id: 'late-channel' },
        { id: 8, name: 'Night News', category: 'News' },
      ],
      isLoading: false,
      error: null,
    });
    mockUseEPGPrograms.mockReturnValue({
      data: [],
      isLoading: false,
    });

    renderPage();

    expect(screen.getByText(/Linked TV channel found in the loaded catalog: Late Sports/i)).toBeInTheDocument();
    expect(screen.getByText(/selected date range.*schedule ingestion.*adjusting mapping rules|adjusting mapping rules.*selected date range.*schedule ingestion/i)).toBeInTheDocument();
  });

  it('describes inferred linked channels as review-ready without claiming confirmed mapping', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        { id: 7, name: 'Late Sports', category: 'Sports', epg_id: 'late-channel' },
        { id: 8, name: 'Night News', category: 'News' },
      ],
      isLoading: false,
      error: null,
    });

    renderPage();

    expect(screen.getByText(/An inferred linked TV channel is available for review and tuning/i)).toBeInTheDocument();
    expect(screen.getByText(/schedule evidence.*string rules.*pairing as final|string rules.*schedule evidence.*pairing as final/i)).toBeInTheDocument();
    expect(screen.queryByText(/mapped/i)).not.toBeInTheDocument();
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

  it('shows an explicit schedule-section error state when schedule loading fails', () => {
    mockUseEPGPrograms.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('schedule failed'),
    });

    renderPage();

    expect(screen.getByText('Unable to load the schedule for this date range right now.')).toBeInTheDocument();
    expect(screen.queryByText('No programs found for the selected date range')).not.toBeInTheDocument();
  });

  it('does not render stale schedule rows when the schedule query errors', () => {
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
      error: new Error('schedule failed'),
    });

    renderPage();

    expect(screen.getByText('Unable to load the schedule for this date range right now.')).toBeInTheDocument();
    expect(screen.queryByText('Late Match')).not.toBeInTheDocument();
  });

  it('shows an explicit string-mapping-section error state when mapping rules fail to load', () => {
    mockUseEPGStringMappings.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('mappings failed'),
    });

    renderPage();

    expect(screen.getByText('Unable to load string mapping rules right now.')).toBeInTheDocument();
    expect(screen.queryByText('No string mappings found')).not.toBeInTheDocument();
  });

  it('does not render stale string mapping rows when the mapping query errors', () => {
    mockUseEPGStringMappings.mockReturnValue({
      data: [{ id: 5, search_pattern: 'Late', is_exclusion: false }],
      isLoading: false,
      error: new Error('mappings failed'),
    });

    renderPage();

    expect(screen.getByText('Unable to load string mapping rules right now.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Delete string mapping Late' })).not.toBeInTheDocument();
  });

  it('keeps the relationship summary loading-aware while TV catalog and schedule data are unresolved', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    mockUseEPGPrograms.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderPage();

    expect(screen.getByText(/Checking loaded TV channel relationships/i)).toBeInTheDocument();
    expect(screen.getByText(/Wait for the TV catalog and schedule window to finish loading before choosing the next relationship action/i)).toBeInTheDocument();
    expect(screen.queryByText(/No linked TV channel found in the loaded catalog yet/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/No programs are visible in the selected date range/i)).not.toBeInTheDocument();
  });

  it('keeps string-mapping support text loading-aware while mapping rules are unresolved', () => {
    mockUseEPGStringMappings.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderPage();

    expect(screen.getByText(/String mapping rules are still loading for this source/i)).toBeInTheDocument();
    expect(screen.queryByText(/No string mapping rules are set yet/i)).not.toBeInTheDocument();
  });

  it('keeps the relationship summary error-aware when TV catalog or schedule queries fail', () => {
    mockUseTVChannelCatalog.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('catalog failed'),
    });
    mockUseEPGPrograms.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('schedule failed'),
    });

    renderPage();

    expect(screen.getByText(/Relationship evidence is incomplete right now/i)).toBeInTheDocument();
    expect(screen.getByText(/Resolve the TV catalog or schedule loading error before deciding whether to map, create, or tune this source/i)).toBeInTheDocument();
    expect(screen.queryByText(/No linked TV channel found in the loaded catalog yet/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/No programs are visible in the selected date range/i)).not.toBeInTheDocument();
  });

  it('keeps string-mapping support text error-aware when mapping rules fail to load', () => {
    mockUseEPGStringMappings.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('mappings failed'),
    });

    renderPage();

    expect(screen.getByText(/String mapping rules need attention before this summary can suggest tuning cleanup/i)).toBeInTheDocument();
    expect(screen.queryByText(/No string mapping rules are set yet/i)).not.toBeInTheDocument();
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

  it('keeps success feedback visible until the user dismisses it', async () => {
    jest.useFakeTimers();

    try {
      const mutateAsync = jest.fn().mockResolvedValue({ id: 55 });
      mockUseCreateTVChannel.mockReturnValue({ mutateAsync, isLoading: false });

      renderPage();

      fireEvent.click(screen.getByRole('button', { name: 'Create TV Channel' }));
      fireEvent.click(screen.getByRole('button', { name: 'Create' }));

      await waitFor(() => {
        expect(screen.getByText('TV channel created successfully')).toBeInTheDocument();
      });

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(screen.getByText('TV channel created successfully')).toBeInTheDocument();
      fireEvent.click(screen.getByRole('button', { name: /close/i }));
      await waitFor(() => {
        expect(screen.queryByText('TV channel created successfully')).not.toBeInTheDocument();
      });
    } finally {
      jest.useRealTimers();
    }
  });

  it('trims string-mapping patterns before submitting them', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ id: 99 });
    mockUseAddEPGStringMapping.mockReturnValue({ mutateAsync });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Add String Mapping' }));
    fireEvent.change(screen.getByLabelText('Search Pattern'), { target: { value: '  Late Pattern  ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Mapping' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        pattern: 'Late Pattern',
        isExclusion: false,
      });
    });
  });
});

import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import EPGChannelDetail from '../pages/EPGChannelDetail';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseEPGChannel = jest.fn();
const mockUseEPGStringMappings = jest.fn();
const mockUseAddEPGStringMapping = jest.fn();
const mockUseDeleteEPGStringMapping = jest.fn();
const mockUseMapEPGChannel = jest.fn();
const mockUseTVChannelCatalog = jest.fn();
const mockUseCreateTVChannel = jest.fn();

jest.mock('../components/epg/ScheduleView', () => ({
  __esModule: true,
  default: ({ epgChannelId }: { epgChannelId: number }) => <div data-testid="schedule-view">schedule for {epgChannelId}</div>,
}));
jest.mock('../hooks/useEPG', () => ({
  useEPGChannel: (...args: unknown[]) => mockUseEPGChannel(...args),
  useEPGStringMappings: (...args: unknown[]) => mockUseEPGStringMappings(...args),
  useAddEPGStringMapping: (...args: unknown[]) => mockUseAddEPGStringMapping(...args),
  useDeleteEPGStringMapping: (...args: unknown[]) => mockUseDeleteEPGStringMapping(...args),
  useMapEPGChannel: (...args: unknown[]) => mockUseMapEPGChannel(...args),
}));
jest.mock('../hooks/useTVChannels', () => ({
  useTVChannelCatalog: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
  useCreateTVChannel: (...args: unknown[]) => mockUseCreateTVChannel(...args),
}));

describe('EPGChannelDetail', () => {
  const renderPage = () =>
    render(
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
      data: { id: 42, name: 'Late Channel', channel_xml_id: 'late-channel', language: 'en', icon_url: 'https://img.test/late.png' },
      isLoading: false,
    });
    mockUseEPGStringMappings.mockReturnValue({ data: [{ id: 5, search_pattern: 'Late', is_exclusion: false }], isLoading: false });
    mockUseAddEPGStringMapping.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteEPGStringMapping.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseMapEPGChannel.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseTVChannelCatalog.mockReturnValue({
      data: [
        { id: 7, name: 'Late Sports', category: 'Sports' },
        { id: 8, name: 'Night News', category: 'News' },
      ],
    });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync: jest.fn().mockResolvedValue({ id: 55 }) });
  });

  it('distinguishes channel-load failure from a missing channel', () => {
    mockUseEPGChannel.mockReturnValue({ data: undefined, isLoading: false, error: new Error('boom') });
    const { unmount } = renderPage();
    expect(screen.getByRole('alert')).toHaveTextContent('Unable to load the EPG channel right now.');
    unmount();

    mockUseEPGChannel.mockReturnValue({ data: undefined, isLoading: false, error: null });
    renderPage();
    expect(screen.getByRole('alert')).toHaveTextContent('EPG channel not found');
  });

  it('shows the xml id, language and link state as chips with mapping actions when unlinked', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Late Channel' })).toBeInTheDocument();
    const summary = screen.getByRole('group', { name: 'Guide channel summary' });
    expect(within(summary).getByText('XML ID: late-channel')).toBeInTheDocument();
    expect(within(summary).getByText('Language: en')).toBeInTheDocument();
    expect(within(summary).getByText('Not linked to a TV channel')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map to TV Channel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create TV Channel' })).toBeInTheDocument();
    expect(screen.getByTestId('schedule-view')).toHaveTextContent('schedule for 42');
    expect(screen.getByRole('table', { name: 'String mapping rules table' })).toBeInTheDocument();
    expect(screen.queryByText(/relationship/i)).not.toBeInTheDocument();

    const schedule = screen.getByRole('heading', { level: 2, name: 'Schedule' });
    const rules = screen.getByRole('heading', { level: 2, name: 'String mapping rules' });
    expect(schedule.compareDocumentPosition(rules) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('links to the TV channel whose epg id matches and hides the mapping actions', () => {
    mockUseTVChannelCatalog.mockReturnValue({ data: [{ id: 7, name: 'Late Sports', category: 'Sports', epg_id: 'late-channel' }] });
    renderPage();

    const summary = screen.getByRole('group', { name: 'Guide channel summary' });
    expect(within(summary).getByRole('link', { name: 'TV channel: Late Sports' })).toHaveAttribute('href', '/tv-channels/7');
    expect(screen.queryByRole('button', { name: 'Map to TV Channel' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Create TV Channel' })).not.toBeInTheDocument();
  });

  it('uses explicit radio controls for TV channel selection', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));
    expect(screen.getByRole('radiogroup', { name: 'Available TV channels' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Late Sports/ })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Night News/ })).toBeInTheDocument();
  });

  it('shows the selected TV channel clearly before confirming the mapping', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));
    fireEvent.click(screen.getByRole('radio', { name: /Late Sports/ }));
    expect(screen.getByText('Selected TV channel: Late Sports')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeEnabled();
  });

  it('shows loading, error and empty states inside the mapping dialog', () => {
    mockUseTVChannelCatalog.mockReturnValue({ data: undefined, isLoading: true, error: null });
    const { unmount: unmountFirst } = renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));
    expect(screen.getByText('Loading TV channels...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeDisabled();
    unmountFirst();

    mockUseTVChannelCatalog.mockReturnValue({ data: undefined, isLoading: false, error: new Error('catalog failed') });
    const { unmount: unmountSecond } = renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));
    expect(screen.getByText('Unable to load TV channels right now.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeDisabled();
    unmountSecond();

    mockUseTVChannelCatalog.mockReturnValue({ data: [], isLoading: false, error: null });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Map to TV Channel' }));
    expect(screen.getByText('No TV channels are available to map yet.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Map Channel' })).toBeDisabled();
  });

  it('shows loading and error states for the string mapping rules without stale rows', () => {
    mockUseEPGStringMappings.mockReturnValue({ data: undefined, isLoading: true });
    const { unmount: unmountFirst } = renderPage();
    expect(screen.getByText('Loading string mapping rules...')).toBeInTheDocument();
    unmountFirst();

    mockUseEPGStringMappings.mockReturnValue({ data: [{ id: 5, search_pattern: 'Late', is_exclusion: false }], isLoading: false, error: new Error('rules failed') });
    renderPage();
    expect(screen.getByText('Unable to load string mapping rules right now.')).toBeInTheDocument();
    expect(screen.queryByRole('table', { name: 'String mapping rules table' })).not.toBeInTheDocument();
  });

  it('creates TV channels through the shared mutation layer, prefilled from the guide channel', async () => {
    const mutateAsync = jest.fn().mockResolvedValue({ id: 55 });
    mockUseCreateTVChannel.mockReturnValue({ mutateAsync, isPending: false });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Create TV Channel' }));
    expect(screen.getByLabelText(/Channel Name/)).toHaveValue('Late Channel');
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith(expect.objectContaining({ name: 'Late Channel', epg_id: 'late-channel', language: 'en', logo_url: 'https://img.test/late.png' }));
    });
    expect(await screen.findByText('TV channel created successfully')).toBeInTheDocument();
  });

  it('keeps success feedback visible until the user dismisses it', async () => {
    jest.useFakeTimers();
    try {
      const mutateAsync = jest.fn().mockResolvedValue({ id: 55 });
      mockUseCreateTVChannel.mockReturnValue({ mutateAsync, isPending: false });
      renderPage();

      fireEvent.click(screen.getByRole('button', { name: 'Create TV Channel' }));
      fireEvent.click(screen.getByRole('button', { name: 'Create' }));
      expect(await screen.findByText('TV channel created successfully')).toBeInTheDocument();

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
      expect(mutateAsync).toHaveBeenCalledWith({ pattern: 'Late Pattern', isExclusion: false });
    });
  });

  it('confirms before deleting a string mapping rule', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseDeleteEPGStringMapping.mockReturnValue({ mutateAsync });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Delete string mapping Late' }));
    const dialog = await screen.findByRole('dialog', { name: 'Delete the rule “Late”?' });
    expect(mutateAsync).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }));

    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(5));
    expect(await screen.findByText('String mapping deleted successfully')).toBeInTheDocument();
  });
});

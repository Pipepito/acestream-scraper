import React from 'react';
import { Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, within } from '@testing-library/react';
import TVChannelDetail from '../pages/TVChannelDetail';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

const mockUseTVChannel = jest.fn();
const mockUseTVChannelAcestreams = jest.fn();
const mockUseAssociateAcestream = jest.fn();
const mockUseRemoveAcestreamAssociation = jest.fn();
const mockUseUpdateTVChannel = jest.fn();
const mockUseAcestreamChannels = jest.fn();
const mockUseResolveEPGChannel = jest.fn();

jest.mock('../components/BatchAcestreamAssignment', () => {
  const MockBatchAssignment = () => <div data-testid="batch-assignment-dialog" />;
  MockBatchAssignment.displayName = 'MockBatchAssignment';
  return MockBatchAssignment;
});
jest.mock('../components/epg/ScheduleView', () => ({
  __esModule: true,
  default: ({ epgChannelId }: { epgChannelId: number }) => <div data-testid="schedule-view">schedule for {epgChannelId}</div>,
}));
jest.mock('../components/player/StreamPlayerDialog', () => ({
  __esModule: true,
  default: ({ open, title, contentId }: { open: boolean; title: string; contentId: string | null }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        {contentId}
      </div>
    ) : null,
}));
jest.mock('../hooks/useEPG', () => ({
  useResolveEPGChannel: (...args: unknown[]) => mockUseResolveEPGChannel(...args),
}));
jest.mock('../hooks/useTVChannels', () => ({
  useTVChannel: (...args: unknown[]) => mockUseTVChannel(...args),
  useTVChannelAcestreams: (...args: unknown[]) => mockUseTVChannelAcestreams(...args),
  useAssociateAcestream: (...args: unknown[]) => mockUseAssociateAcestream(...args),
  useRemoveAcestreamAssociation: (...args: unknown[]) => mockUseRemoveAcestreamAssociation(...args),
  useUpdateTVChannel: (...args: unknown[]) => mockUseUpdateTVChannel(...args),
}));
jest.mock('../hooks/useChannels', () => ({
  useAcestreamChannels: (...args: unknown[]) => mockUseAcestreamChannels(...args),
}));

describe('TVChannelDetail', () => {
  const baseChannel = {
    id: 7,
    name: 'Arena TV',
    logo_url: '',
    description: 'Primary sports feed',
    category: 'Sports',
    country: 'RS',
    language: 'en',
    website: 'https://arena.test',
    epg_id: 'arena-tv',
    epg_source_id: 4,
    channel_number: 7,
    is_active: true,
    is_favorite: true,
    acestream_channels: [{ id: 'ace-1', name: 'Arena Feed 1', group: 'Sports', is_online: true }],
  };

  const renderPage = () =>
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter initialEntries={['/tv-channels/7']}>
          <Routes>
            <Route path="/tv-channels/:id" element={<TVChannelDetail />} />
          </Routes>
        </TestMemoryRouter>
      </ThemeProvider>
    );

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTVChannel.mockReturnValue({ data: baseChannel, isLoading: false, isError: false });
    mockUseTVChannelAcestreams.mockReturnValue({ data: [] });
    mockUseAssociateAcestream.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseRemoveAcestreamAssociation.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseAcestreamChannels.mockReturnValue({ data: { items: [] }, isLoading: false });
    mockUseResolveEPGChannel.mockReturnValue({ data: { id: 99, name: 'Arena Guide' }, isLoading: false, isError: false });
  });

  it('summarises the channel as chips and orders Streams before Schedule', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Arena TV' })).toBeInTheDocument();
    expect(screen.getByText('Sports · Channel 7')).toBeInTheDocument();
    const summary = screen.getByRole('group', { name: 'Channel summary' });
    expect(within(summary).getByText('Active')).toBeInTheDocument();
    expect(within(summary).getByText('Favorite')).toBeInTheDocument();
    expect(within(summary).getByText('1 stream')).toBeInTheDocument();
    expect(within(summary).getByText('EPG: arena-tv')).toBeInTheDocument();
    expect(within(summary).getByRole('link', { name: 'Guide channel: Arena Guide' })).toHaveAttribute('href', '/epg/channels/99');
    expect(screen.queryByText(/relationship/i)).not.toBeInTheDocument();

    const streams = screen.getByRole('heading', { level: 2, name: 'Streams' });
    const schedule = screen.getByRole('heading', { level: 2, name: 'Schedule' });
    expect(streams.compareDocumentPosition(schedule) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(mockUseResolveEPGChannel).toHaveBeenCalledWith(4, 'arena-tv');
    expect(screen.getByTestId('schedule-view')).toHaveTextContent('schedule for 99');
  });

  it('explains when the EPG id is missing or not found in the sources', () => {
    mockUseTVChannel.mockReturnValue({ data: { ...baseChannel, epg_id: '', is_active: false, is_favorite: false, acestream_channels: [] }, isLoading: false, isError: false });
    mockUseResolveEPGChannel.mockReturnValue({ data: undefined, isLoading: false, isError: false });
    const { unmount } = renderPage();
    expect(screen.getByText('No EPG ID yet. Edit the channel and set one to see the schedule here.')).toBeInTheDocument();
    const summary = screen.getByRole('group', { name: 'Channel summary' });
    expect(within(summary).getByText('Hidden')).toBeInTheDocument();
    expect(within(summary).getByText('0 streams')).toBeInTheDocument();
    expect(within(summary).getByText('EPG: not mapped')).toBeInTheDocument();
    expect(screen.getByText('No streams yet. Add one so this channel can play.')).toBeInTheDocument();
    unmount();

    mockUseTVChannel.mockReturnValue({ data: baseChannel, isLoading: false, isError: false });
    renderPage();
    expect(screen.getByText(/No guide channel with id “arena-tv” was found/)).toBeInTheDocument();
    expect(screen.queryByTestId('schedule-view')).not.toBeInTheDocument();
  });

  it('only enables acestream candidate fetching while the add stream dialog is open', () => {
    renderPage();
    expect(mockUseAcestreamChannels).toHaveBeenLastCalledWith({}, expect.objectContaining({ staleTime: 1000 * 60, enabled: false }));
    fireEvent.click(screen.getByRole('button', { name: 'Add stream' }));
    expect(mockUseAcestreamChannels).toHaveBeenLastCalledWith({}, expect.objectContaining({ staleTime: 1000 * 60, enabled: true }));
  });

  it('lists each stream with its state, group and id plus play and remove actions', () => {
    renderPage();
    expect(screen.getByRole('button', { name: 'play stream Arena Feed 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove acestream Arena Feed 1' })).toBeInTheDocument();
    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('ace-1')).toBeInTheDocument();
  });

  it('plays a single stream and the best stream from the header', () => {
    mockUseTVChannel.mockReturnValue({
      data: {
        ...baseChannel,
        acestream_channels: [
          { id: 'ace-best', name: 'Arena Feed 1', group: 'Sports', is_online: true },
          { id: 'ace-2', name: 'Arena Feed 2', group: 'Sports', is_online: false },
        ],
      },
      isLoading: false,
      isError: false,
    });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'play stream Arena Feed 2' }));
    expect(screen.getByRole('dialog', { name: 'Arena Feed 2' })).toHaveTextContent('ace-2');

    fireEvent.click(screen.getByRole('button', { name: 'Play best stream' }));
    expect(screen.getByRole('dialog', { name: 'Arena TV' })).toHaveTextContent('ace-best');
  });

  it('disables Play best stream when the channel has no streams', () => {
    mockUseTVChannel.mockReturnValue({ data: { ...baseChannel, acestream_channels: [] }, isLoading: false, isError: false });
    renderPage();

    expect(screen.getByRole('button', { name: 'Play best stream' })).toBeDisabled();
  });

  it('announces TV channel detail loading through a contextual status region', () => {
    mockUseTVChannel.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    renderPage();
    expect(screen.getByRole('status')).toHaveTextContent('Loading TV channel details...');
  });

  it('uses explicit selection controls when choosing acestream candidates to associate', () => {
    mockUseAcestreamChannels.mockReturnValue({
      data: { items: [{ id: 'ace-2', name: 'Arena Feed 2', group: 'Sports' }, { id: 'ace-3', name: 'Arena Feed 3', group: 'Sports' }] },
      isLoading: false,
    });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Add stream' }));
    const firstCheckbox = screen.getByRole('checkbox', { name: 'Select acestream Arena Feed 2' });
    expect(screen.getByRole('button', { name: 'Assign Selected' })).toBeDisabled();
    fireEvent.click(firstCheckbox);
    expect(firstCheckbox).toBeChecked();
    expect(screen.getByText('1 acestream selected for assignment.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Assign Selected' })).toBeEnabled();
  });

  it('shows an explicit error state when acestream candidate loading fails', () => {
    mockUseAcestreamChannels.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: 'Add stream' }));
    expect(screen.getByText('Unable to load Acestream candidates. Try searching again in a moment.')).toBeInTheDocument();
  });

  it('edits the main fields first and keeps the rest behind More fields', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync });
    mockUseTVChannel.mockReturnValue({ data: { ...baseChannel, description: '', logo_url: '', website: '', language: '', country: '' }, isLoading: false, isError: false });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    expect(screen.getByLabelText(/^Name/)).toHaveValue('Arena TV');
    expect(screen.getByLabelText(/^EPG ID/)).toHaveValue('arena-tv');
    expect(screen.getByLabelText(/^Channel number/)).toHaveValue(7);
    expect(screen.queryByLabelText(/^Description/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'More fields' }));
    expect(screen.getByLabelText(/^Description/)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Website/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(mutateAsync).toHaveBeenCalledWith({
      id: 7,
      updates: expect.objectContaining({ name: 'Arena TV', epg_id: 'arena-tv', channel_number: 7, is_active: true, is_favorite: true }),
    });
    expect(await screen.findByText(/updated successfully/i)).toBeInTheDocument();
  });

  it('shows explicit success feedback after assigning selected acestream sources', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseAssociateAcestream.mockReturnValue({ mutateAsync });
    mockUseAcestreamChannels.mockReturnValue({ data: { items: [{ id: 'ace-2', name: 'Arena Feed 2', group: 'Sports' }] }, isLoading: false });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Add stream' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'Select acestream Arena Feed 2' }));
    fireEvent.click(screen.getByRole('button', { name: 'Assign Selected' }));

    expect(mutateAsync).toHaveBeenCalledWith({ tvChannelId: 7, aceStreamId: 'ace-2' });
    expect(await screen.findByText(/assigned 1 acestream source successfully/i)).toBeInTheDocument();
  });

  it('confirms before removing a stream and reports success', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseRemoveAcestreamAssociation.mockReturnValue({ mutateAsync });
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Remove acestream Arena Feed 1' }));
    const dialog = await screen.findByRole('dialog', { name: 'Remove Arena Feed 1 from this channel?' });
    expect(mutateAsync).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Remove' }));

    expect(await screen.findByText(/removed acestream arena feed 1 successfully/i)).toBeInTheDocument();
    expect(mutateAsync).toHaveBeenCalledWith({ tvChannelId: 7, aceStreamId: 'ace-1' });
  });
});

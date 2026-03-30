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

jest.mock('../components/BatchAcestreamAssignment', () => () => <div data-testid="batch-assignment-dialog" />);
jest.mock('../components/EPGProgramsTable', () => () => <div data-testid="epg-programs-table" />);

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
    acestream_channels: [
      {
        channel_id: 'ace-1',
        id: 'ace-1',
        name: 'Arena Feed 1',
        group: 'Sports',
        is_online: true,
      },
    ],
  };

  const renderPage = () => render(
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
    mockUseTVChannel.mockReturnValue({
      data: baseChannel,
      isLoading: false,
      isError: false,
    });
    mockUseTVChannelAcestreams.mockReturnValue({ data: [] });
    mockUseAssociateAcestream.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseRemoveAcestreamAssociation.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseAcestreamChannels.mockReturnValue({ data: { items: [] }, isLoading: false });
  });

  it('renders a shared header with top-down operational sections', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Arena TV' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Back to TV channels' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Channel Summary' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Acestream Coverage' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'EPG Schedule' })).toBeInTheDocument();
  });

  it('only enables acestream candidate fetching while the add single dialog is open', () => {
    renderPage();

    expect(mockUseAcestreamChannels).toHaveBeenLastCalledWith(
      {},
      expect.objectContaining({ staleTime: 1000 * 60, enabled: false })
    );

    fireEvent.click(screen.getByRole('button', { name: 'Add Single' }));

    expect(mockUseAcestreamChannels).toHaveBeenLastCalledWith(
      {},
      expect.objectContaining({ staleTime: 1000 * 60, enabled: true })
    );
  });

  it('renders a relationship summary region with identity, status, next step, and support in order', () => {
    renderPage();

    const relationshipSummary = screen.getByRole('region', { name: 'Relationship summary' });
    const channelSummaryHeading = screen.getByRole('heading', { level: 2, name: 'Channel Summary' });
    const identitySummary = within(relationshipSummary).getByText(/Arena TV is active, marked favorite/i);
    const relationshipStatus = within(relationshipSummary).getByText(/^Relationship status$/i);
    const nextStep = within(relationshipSummary).getByText(/^Next step$/i);
    const supportCopy = within(relationshipSummary).getByText(/Linked source coverage and guide linkage are both present/i);

    expect(within(relationshipSummary).getByText('Operational relationship in place')).toBeInTheDocument();
    expect(identitySummary.compareDocumentPosition(channelSummaryHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(identitySummary.compareDocumentPosition(relationshipStatus) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(relationshipStatus.compareDocumentPosition(nextStep) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(nextStep.compareDocumentPosition(supportCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('prioritizes missing acestream coverage ahead of missing guide linkage', () => {
    mockUseTVChannel.mockReturnValue({
      data: {
        ...baseChannel,
        epg_id: '',
        acestream_channels: [],
      },
      isLoading: false,
      isError: false,
    });

    renderPage();

    expect(screen.getByText('Playback coverage incomplete')).toBeInTheDocument();
    expect(screen.getByText(/at least one acestream source.*ready for playback|ready for playback.*at least one acestream source/i)).toBeInTheDocument();
  });

  it('uses guide linkage as the primary next step when coverage exists but epg is missing', () => {
    mockUseTVChannel.mockReturnValue({
      data: {
        ...baseChannel,
        epg_id: '',
      },
      isLoading: false,
      isError: false,
    });

    renderPage();

    expect(screen.getByText('Guide linkage still missing')).toBeInTheDocument();
    expect(within(screen.getByText(/^Next step$/i).parentElement as HTMLElement).getByText(/correct EPG ID.*schedule review|schedule review.*correct EPG ID/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'EPG Schedule' })).toBeInTheDocument();
    expect(screen.getByText(/Guide linkage is still incomplete, so schedule review will appear here after you add the correct EPG ID\./i)).toBeInTheDocument();
  });

  it('uses only explicit functional actions for each associated acestream row', () => {
    renderPage();

    expect(screen.getByRole('button', { name: 'Remove acestream Arena Feed 1' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Play acestream Arena Feed 1' })).not.toBeInTheDocument();
  });

  it('announces TV channel detail loading through a contextual status region', () => {
    mockUseTVChannel.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    renderPage();

    expect(screen.getByRole('status')).toHaveTextContent('Loading TV channel details...');
  });

  it('uses explicit selection controls when choosing acestream candidates to associate', () => {
    mockUseAcestreamChannels.mockReturnValue({
      data: {
        items: [
          { id: 'ace-2', name: 'Arena Feed 2', group: 'Sports' },
          { id: 'ace-3', name: 'Arena Feed 3', group: 'Sports' },
        ],
      },
      isLoading: false,
    });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Add Single' }));

    const firstCheckbox = screen.getByRole('checkbox', { name: 'Select acestream Arena Feed 2' });

    expect(screen.getByRole('button', { name: 'Assign Selected' })).toBeDisabled();

    fireEvent.click(firstCheckbox);

    expect(firstCheckbox).toBeChecked();
    expect(screen.getByText('1 acestream selected for assignment.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Assign Selected' })).toBeEnabled();
  });

  it('shows an explicit error state when acestream candidate loading fails', () => {
    mockUseAcestreamChannels.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Add Single' }));

    expect(screen.getByText('Unable to load Acestream candidates. Try searching again in a moment.')).toBeInTheDocument();
  });

  it('shows explicit success feedback after saving the main edit path', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseUpdateTVChannel.mockReturnValue({ mutateAsync });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    expect(mutateAsync).toHaveBeenCalledWith({
      id: 7,
      updates: expect.objectContaining({
        name: 'Arena TV',
        epg_id: 'arena-tv',
        channel_number: 7,
        is_active: true,
        is_favorite: true,
      }),
    });
    expect(await screen.findByText(/updated successfully/i)).toBeInTheDocument();
  });

  it('shows explicit success feedback after assigning selected acestream sources', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseAssociateAcestream.mockReturnValue({ mutateAsync });
    mockUseAcestreamChannels.mockReturnValue({
      data: {
        items: [
          { id: 'ace-2', name: 'Arena Feed 2', group: 'Sports' },
        ],
      },
      isLoading: false,
    });

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Add Single' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'Select acestream Arena Feed 2' }));
    fireEvent.click(screen.getByRole('button', { name: 'Assign Selected' }));

    expect(mutateAsync).toHaveBeenCalledWith({
      tvChannelId: 7,
      aceStreamId: 'ace-2',
    });
    expect(await screen.findByText(/assigned 1 acestream source successfully/i)).toBeInTheDocument();
  });

  it('shows explicit success feedback after removing a linked acestream source', async () => {
    const mutateAsync = jest.fn().mockResolvedValue(undefined);
    mockUseRemoveAcestreamAssociation.mockReturnValue({ mutateAsync });
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    renderPage();

    fireEvent.click(screen.getByRole('button', { name: 'Remove acestream Arena Feed 1' }));

    expect(mutateAsync).toHaveBeenCalledWith({
      tvChannelId: 7,
      aceStreamId: 'ace-1',
    });
    expect(await screen.findByText(/removed acestream arena feed 1 successfully/i)).toBeInTheDocument();

    confirmSpy.mockRestore();
  });
});

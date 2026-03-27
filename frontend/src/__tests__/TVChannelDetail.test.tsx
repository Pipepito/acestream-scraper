import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';

import TVChannelDetail from '../pages/TVChannelDetail';
import { createAppTheme } from '../theme';

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
  const renderPage = () => render(
    <ThemeProvider theme={createAppTheme('light')}>
      <MemoryRouter initialEntries={['/tv-channels/7']}>
        <Routes>
          <Route path="/tv-channels/:id" element={<TVChannelDetail />} />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseTVChannel.mockReturnValue({
      data: {
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
      },
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

  it('uses explicit accessible actions for each associated acestream row', () => {
    renderPage();

    expect(screen.getByRole('button', { name: 'Play acestream Arena Feed 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove acestream Arena Feed 1' })).toBeInTheDocument();
  });
});

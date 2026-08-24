import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import EPG from '../pages/EPG';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';

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
const mockUseTVChannelCatalog = jest.fn();
const mockAnalyzeEPGMatches = jest.fn();
const mockCreateFromEPGAnalysis = jest.fn();

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
  useTVChannelCatalog: (...args: unknown[]) => mockUseTVChannelCatalog(...args),
}));

jest.mock('../services/tvChannelService', () => ({
  tvChannelService: {
    createFromEpg: jest.fn().mockResolvedValue({ created_count: 0, skipped_count: 0, associated_count: 0 }),
    analyzeEPGMatches: (...args: unknown[]) => mockAnalyzeEPGMatches(...args),
    createFromEPGAnalysis: (...args: unknown[]) => mockCreateFromEPGAnalysis(...args),
  },
}));

const analysisResponse = {
  summary: {
    epg_channels_analyzed: 4,
    matched_epg_channels: 3,
    matched_acestream_channels: 4,
    creatable_rows: 2,
    skipped_existing_tv_channels: 2,
  },
  rows: [
    {
      epg_channel_id: 101,
      epg_channel_xml_id: 'alpha-arena',
      epg_channel_name: 'Alpha Arena',
      epg_source_id: 2,
      epg_source_name: 'Source Two',
      existing_tv_channel_id: null,
      existing_tv_channel_count: 0,
      has_duplicate_existing_conflict: false,
      candidate_count: 1,
      candidates: [
        {
          acestream_channel_id: 'ace-alpha',
          name: 'Alpha Arena HD',
          tvg_id: 'alpha-arena',
          tvg_name: 'Alpha Arena HD',
          score: 1,
          match_stage: 'xml_id_exact',
        },
      ],
      best_match_type: 'xml_id_exact',
      best_match_confidence: 'high',
      is_creatable: true,
    },
    {
      epg_channel_id: 102,
      epg_channel_xml_id: 'existing-sports',
      epg_channel_name: 'Existing Sports',
      epg_source_id: 2,
      epg_source_name: 'Source Two',
      existing_tv_channel_id: 77,
      existing_tv_channel_count: 1,
      has_duplicate_existing_conflict: false,
      candidate_count: 1,
      candidates: [
        {
          acestream_channel_id: 'ace-existing',
          name: 'Existing Sports',
          tvg_id: 'existing-sports',
          tvg_name: 'Existing Sports',
          score: 1,
          match_stage: 'name_exact',
        },
      ],
      best_match_type: 'name_exact',
      best_match_confidence: 'high',
      is_creatable: false,
    },
    {
      epg_channel_id: 103,
      epg_channel_xml_id: 'no-match',
      epg_channel_name: 'No Match News',
      epg_source_id: 2,
      epg_source_name: 'Source Two',
      existing_tv_channel_id: null,
      existing_tv_channel_count: 0,
      has_duplicate_existing_conflict: false,
      candidate_count: 0,
      candidates: [],
      best_match_type: null,
      best_match_confidence: null,
      is_creatable: false,
    },
    {
      epg_channel_id: 104,
      epg_channel_xml_id: 'loose-fuzz',
      epg_channel_name: 'Loose Fuzz Sports',
      epg_source_id: 2,
      epg_source_name: 'Source Two',
      existing_tv_channel_id: null,
      existing_tv_channel_count: 0,
      has_duplicate_existing_conflict: false,
      candidate_count: 2,
      candidates: [
        {
          acestream_channel_id: 'ace-fuzz-1',
          name: 'Loose Fuzz Sport',
          tvg_id: null,
          tvg_name: 'Loose Fuzz Sport',
          score: 0.87,
          match_stage: 'name_similarity',
        },
        {
          acestream_channel_id: 'ace-fuzz-2',
          name: 'Loose Fuzz Sports 2',
          tvg_id: null,
          tvg_name: 'Loose Fuzz Sports 2',
          score: 0.84,
          match_stage: 'name_similarity',
        },
      ],
      best_match_type: 'name_similarity',
      best_match_confidence: 'medium',
      is_creatable: true,
    },
  ],
};

const zeroMatchResponse = {
  summary: {
    epg_channels_analyzed: 2,
    matched_epg_channels: 0,
    matched_acestream_channels: 0,
    creatable_rows: 0,
    skipped_existing_tv_channels: 0,
  },
  rows: [
    {
      epg_channel_id: 201,
      epg_channel_xml_id: 'zero-one',
      epg_channel_name: 'Zero One',
      epg_source_id: 1,
      epg_source_name: 'Source One',
      existing_tv_channel_id: null,
      existing_tv_channel_count: 0,
      has_duplicate_existing_conflict: false,
      candidate_count: 0,
      candidates: [],
      best_match_type: null,
      best_match_confidence: null,
      is_creatable: false,
    },
    {
      epg_channel_id: 202,
      epg_channel_xml_id: 'zero-two',
      epg_channel_name: 'Zero Two',
      epg_source_id: 1,
      epg_source_name: 'Source One',
      existing_tv_channel_id: null,
      existing_tv_channel_count: 0,
      has_duplicate_existing_conflict: false,
      candidate_count: 0,
      candidates: [],
      best_match_type: null,
      best_match_confidence: null,
      is_creatable: false,
    },
  ],
};

const renderPage = () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <ThemeProvider theme={createAppTheme('light')}>
      <QueryClientProvider client={queryClient}>
        <TestMemoryRouter>
          <EPG />
        </TestMemoryRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

describe('EPG bulk match workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockUseEPGSources.mockReturnValue({
      data: [
        { id: 1, name: 'Source One', url: 'https://one.test', enabled: true, error_count: 0 },
        { id: 2, name: 'Source Two', url: 'https://two.test', enabled: true, error_count: 0 },
      ],
      isLoading: false,
    });

    mockUseEPGChannels.mockReturnValue({
      data: {
        items: [
          { id: 11, epg_source_id: 1, channel_xml_id: 'raw-alpha', name: 'Raw Alpha', language: 'en', created_at: '', updated_at: '' },
          { id: 12, epg_source_id: 1, channel_xml_id: 'raw-beta', name: 'Raw Beta', language: 'en', created_at: '', updated_at: '' },
        ],
        total: 2,
      },
      isLoading: false,
      isPreviousData: false,
    });

    mockUseCreateEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseUpdateEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseDeleteEPGSource.mockReturnValue({ mutateAsync: jest.fn() });
    mockUseRefreshAllEPGSources.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUseDownloadEPGXML.mockReturnValue({ mutateAsync: jest.fn(), isPending: false });
    mockUseAllTVChannels.mockReturnValue({ data: { items: [], total: 0 } });
    mockUseTVChannelCatalog.mockReturnValue({ data: [], isLoading: false, error: null });
    mockAnalyzeEPGMatches.mockResolvedValue(analysisResponse);
    mockCreateFromEPGAnalysis.mockResolvedValue({
      created_count: 1,
      skipped_count: 1,
      associated_count: 2,
      failure_count: 0,
      row_outcomes: [],
    });
  });

  it('shows strictness controls, disables create before analysis, and sends source-filtered analyze requests', async () => {
    renderPage();

    expect(screen.getByRole('button', { name: /create matched tv channels/i })).toBeDisabled();

    fireEvent.mouseDown(screen.getByRole('combobox', { name: /match strictness/i }));
    expect(screen.getByRole('option', { name: 'Loose' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Balanced' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Strict' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('option', { name: 'Balanced' }));

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'EPG Source' }));
    fireEvent.click(screen.getByRole('option', { name: 'Source Two' }));

    fireEvent.click(screen.getByRole('button', { name: /analyze matches/i }));

    await waitFor(() => {
      expect(mockAnalyzeEPGMatches).toHaveBeenCalledWith({ strictness: 'balanced', source_id: 2 });
    });

    expect(screen.getByText(/4 analyzed/i)).toBeInTheDocument();
    expect(screen.getByText(/3 matched/i)).toBeInTheDocument();
    expect(screen.getByText(/2 creatable/i)).toBeInTheDocument();
  });

  it('renders result states, confidence text, default creatable selection, and filter views', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /analyze matches/i }));

    await screen.findByText('Alpha Arena');

    expect(screen.getByText('XML ID exact')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Name similarity')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Already exists')).toBeInTheDocument();
    expect(screen.getByText('Unmatched')).toBeInTheDocument();

    expect(screen.getByLabelText('select match row Alpha Arena')).toBeChecked();
    expect(screen.getByLabelText('select match row Loose Fuzz Sports')).toBeChecked();
    expect(screen.getByLabelText('select match row Existing Sports')).not.toBeChecked();
    expect(screen.getByLabelText('select match row Existing Sports')).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Unmatched' }));
    expect(screen.getByText('No Match News')).toBeInTheDocument();
    expect(screen.queryByText('Alpha Arena')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Creatable' }));
    expect(screen.getByText('Alpha Arena')).toBeInTheDocument();
    expect(screen.getByText('Loose Fuzz Sports')).toBeInTheDocument();
    expect(screen.queryByText('Existing Sports')).not.toBeInTheDocument();
  });

  it('renders a clean zero-match analysis state', async () => {
    mockAnalyzeEPGMatches.mockResolvedValueOnce(zeroMatchResponse);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /analyze matches/i }));

    await screen.findByText(/2 analyzed/i);

    expect(screen.getByText(/0 matched/i)).toBeInTheDocument();
    expect(screen.getByText(/0 creatable/i)).toBeInTheDocument();
    expect(screen.getByText(/no matches met the current strictness/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create matched tv channels/i })).toBeDisabled();
  });

  it('allows row deselection and creates only selected creatable rows', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /analyze matches/i }));

    await screen.findByText('Alpha Arena');

    fireEvent.click(screen.getByLabelText('select match row Alpha Arena'));
    expect(screen.getByLabelText('select match row Alpha Arena')).not.toBeChecked();
    expect(screen.getByLabelText('select match row Loose Fuzz Sports')).toBeChecked();

    fireEvent.click(screen.getByRole('button', { name: /create matched tv channels/i }));

    await waitFor(() => {
      expect(mockCreateFromEPGAnalysis).toHaveBeenCalledWith({ strictness: 'balanced', epg_channel_ids: [104] });
    });

    expect(screen.getByText(/created 1 tv channels, skipped 1, associated 2 acestream channels/i)).toBeInTheDocument();
  });
});

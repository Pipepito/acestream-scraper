import { TVChannel, TVChannelCreate, TVChannelUpdate, BatchAssignmentRequest, BatchAssignmentResult } from '../types/tvChannelTypes';
import apiClient from './apiClient';

const BASE_URL = '/v1/tv-channels';

export interface CreateTVChannelsFromEPGResult {
  created_count: number;
  skipped_count: number;
  associated_count: number;
  items: TVChannel[];
}

export type EPGMatchStrictness = 'loose' | 'balanced' | 'strict';

export interface EPGMatchCandidate {
  acestream_channel_id: string;
  name: string;
  tvg_id?: string | null;
  tvg_name?: string | null;
  score: number;
  match_stage: string;
}

export interface EPGMatchAnalysisRow {
  epg_channel_id: number;
  epg_channel_xml_id: string;
  epg_channel_name: string;
  epg_source_id: number;
  epg_source_name?: string | null;
  existing_tv_channel_id?: number | null;
  existing_tv_channel_count: number;
  has_duplicate_existing_conflict: boolean;
  candidate_count: number;
  candidates: EPGMatchCandidate[];
  best_match_type?: string | null;
  best_match_confidence?: string | null;
  is_creatable: boolean;
}

export interface EPGMatchAnalysisSummary {
  epg_channels_analyzed: number;
  matched_epg_channels: number;
  matched_acestream_channels: number;
  creatable_rows: number;
  skipped_existing_tv_channels: number;
}

export interface EPGMatchAnalysisResponse {
  summary: EPGMatchAnalysisSummary;
  rows: EPGMatchAnalysisRow[];
}

export interface CreateFromEPGAnalysisRequest {
  strictness: EPGMatchStrictness;
  epg_channel_ids: number[];
}

export interface CreateFromEPGAnalysisResult {
  created_count: number;
  skipped_count: number;
  associated_count: number;
  failure_count: number;
  row_outcomes: Array<{
    epg_channel_id: number;
    status: string;
    reason?: string | null;
    tv_channel_id?: number | null;
    associated_count: number;
  }>;
}

export interface TVChannelListFilters {
  favorites?: boolean;
  search?: string;
}

export const tvChannelService = {
  /**
   * Get all TV channels
   */
  getAll: async (skip = 0, limit = 100, filters?: TVChannelListFilters): Promise<{ items: TVChannel[]; total: number }> => {
    const response = await apiClient.get(BASE_URL, {
      params: {
        skip,
        limit,
        ...(filters?.favorites ? { favorites: true } : {}),
        ...(filters?.search ? { search: filters.search } : {}),
      }
    });
    return response.data;
  },

  getCatalog: async (pageSize = 500, filters?: TVChannelListFilters): Promise<TVChannel[]> => {
    const items: TVChannel[] = [];
    let skip = 0;
    let total = 0;

    do {
      const response = await tvChannelService.getAll(skip, pageSize, filters);
      items.push(...response.items);
      total = response.total;
      skip += response.items.length;

      if (response.items.length === 0) {
        break;
      }
    } while (skip < total);

    return items;
  },

  /**
   * Get a TV channel by ID
   */
  getById: async (id: number): Promise<TVChannel> => {
    const response = await apiClient.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  /**
   * Create a new TV channel
   */
  create: async (tvChannel: TVChannelCreate): Promise<TVChannel> => {
    const response = await apiClient.post(BASE_URL, tvChannel);
    return response.data;
  },

  createFromEpg: async (epgChannelIds: number[]): Promise<CreateTVChannelsFromEPGResult> => {
    const response = await apiClient.post(`${BASE_URL}/from-epg`, { epg_channel_ids: epgChannelIds });
    return response.data;
  },

  analyzeEPGMatches: async (params: { strictness: EPGMatchStrictness; source_id?: number }): Promise<EPGMatchAnalysisResponse> => {
    const response = await apiClient.post(`${BASE_URL}/analyze-epg-matches`, {
      strictness: params.strictness,
      ...(params.source_id !== undefined ? { source_id: params.source_id } : {}),
    });
    return response.data;
  },

  createFromEPGAnalysis: async (payload: CreateFromEPGAnalysisRequest): Promise<CreateFromEPGAnalysisResult> => {
    const response = await apiClient.post(`${BASE_URL}/create-from-epg-analysis`, payload);
    return response.data;
  },

  /**
   * Update a TV channel
   */
  update: async (id: number, updates: TVChannelUpdate): Promise<TVChannel> => {
    const response = await apiClient.put(`${BASE_URL}/${id}`, updates);
    return response.data;
  },

  /**
   * Toggle (or explicitly set, via value) a TV channel's favorite flag
   */
  toggleFavorite: async (id: number, value?: boolean): Promise<TVChannel> => {
    const response = await apiClient.post(`${BASE_URL}/${id}/favorite`, null, {
      params: value === undefined ? {} : { value },
    });
    return response.data;
  },

  /**
   * Delete a TV channel
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${id}`);
  },

  /**
   * Get all acestream channels associated with a TV channel
   */
  getAcestreams: async (id: number): Promise<any[]> => {
    const response = await apiClient.get(`${BASE_URL}/${id}/acestreams`);
    return response.data;
  },

  /**
   * Associate an acestream channel with a TV channel
   */
  associateAcestream: async (tvChannelId: number, aceStreamId: string): Promise<any> => {
    // Use POST body for acestream_channel_id for backend compatibility
    const response = await apiClient.post(`${BASE_URL}/${tvChannelId}/acestreams`, {
      acestream_channel_id: aceStreamId
    });
    return response.data;
  },

  /**
   * Remove an acestream association from a TV channel
   */
  removeAcestreamAssociation: async (tvChannelId: number, aceStreamId: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${tvChannelId}/acestreams/${aceStreamId}`);
  },

  /**
   * Batch assign acestream channels to TV channels
   */
  batchAssignAcestreams: async (assignments: BatchAssignmentRequest): Promise<BatchAssignmentResult> => {
    const response = await apiClient.post(`${BASE_URL}/batch-assign`, assignments);
    return response.data;
  },

  /**
   * Associate acestream channels with TV channels based on EPG IDs
   */
  associateByEpg: async (): Promise<any> => {
    const response = await apiClient.post(`${BASE_URL}/associate-by-epg`);
    return response.data;
  },

  /**
   * Update EPG IDs for all TV channels
   */
  bulkUpdateEpg: async (): Promise<any> => {
    const response = await apiClient.post(`${BASE_URL}/bulk-update-epg`);
    return response.data;
  }
};

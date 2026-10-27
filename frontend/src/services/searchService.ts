import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type SearchResultItem = components['schemas']['SearchResultItem'];
export type BroadcastStatus = components['schemas']['ChannelStatusResponse'];

export interface SearchPagination {
  page: number;
  page_size: number;
  total_results: number;
  total_pages: number;
}

export interface SearchResponse {
  success: boolean;
  message: string;
  results: SearchResultItem[];
  pagination: SearchPagination;
}

export type SearchImportResponse = components['schemas']['SearchImportResponse'];
export type SearchImportOutcome = components['schemas']['SearchImportOutcome'];

const BASE_URL = '/v1/search';

export const searchService = {
  resolveContentId: async (infohash: string): Promise<string> => {
    const response = await apiClient.post<components['schemas']['ResolvedSearchResult']>(
      `${BASE_URL}/${encodeURIComponent(infohash)}/resolve`, {}
    );
    return response.data.content_id;
  },
  checkBroadcast: async (id: string): Promise<BroadcastStatus> => {
    // Allow the configured 120s maximum, one doubled startup retry, an
    // observation window, and cleanup. Normal checks use 10s windows.
    const response = await apiClient.post<BroadcastStatus>(
      `${BASE_URL}/${encodeURIComponent(id)}/check_status`, {}, { timeout: 500000 }
    );
    return response.data;
  },
  /**
   * Search for Acestream channels
   */
  search: async (
    query: string = '',
    page: number = 1,
    pageSize: number = 10,
    category?: string
  ): Promise<SearchResponse> => {
    const params: Record<string, string | number> = {
      query,
      page,
      // The backend declares this query parameter as `per_page`.
      per_page: pageSize
    };

    if (category) {
      params.category = category;
    }

    const response = await apiClient.get(BASE_URL, { params });
    return response.data;
  },

  importResults: async (channels: SearchResultItem[]): Promise<SearchImportResponse> => {
    const response = await apiClient.post<SearchImportResponse>(`${BASE_URL}/import`, {
      items: channels.map(channel => ({ infohash: channel.id, name: channel.name, category: channel.categories?.[0] || '' })),
    }, { timeout: 135000 });
    return response.data;
  },
};

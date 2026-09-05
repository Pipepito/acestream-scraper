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

export interface AddChannelRequest {
  id: string;
  name: string;
}

export interface AddChannelResponse {
  success: boolean;
  message: string;
  channel: any; // Using 'any' for now, should be replaced with proper type
}

export interface AddMultipleRequest {
  channels: AddChannelRequest[];
}

export interface AddMultipleResponse {
  success: boolean;
  message: string;
  added_channels: any[]; // Using 'any' for now, should be replaced with proper type
  existing_channels: any[]; // Using 'any' for now, should be replaced with proper type
}

const BASE_URL = '/v1/search';

export const searchService = {
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
    const params: Record<string, any> = {
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

  /**
   * Add a channel from search results
   */
  addChannel: async (channel: AddChannelRequest): Promise<AddChannelResponse> => {
    const response = await apiClient.post(`${BASE_URL}/add`, channel);
    return response.data;
  },

  /**
   * Add multiple channels from search results
   */
  addMultipleChannels: async (channels: AddChannelRequest[]): Promise<AddMultipleResponse> => {
    const response = await apiClient.post(`${BASE_URL}/add_multiple`, { channels });
    return response.data;
  }
};

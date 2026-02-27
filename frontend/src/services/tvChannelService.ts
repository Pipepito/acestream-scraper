import { TVChannel, TVChannelCreate, TVChannelUpdate, BatchAssignmentRequest, BatchAssignmentResult } from '../types/tvChannelTypes';
import apiClient from './apiClient';

const BASE_URL = '/v1/tv-channels';

export const tvChannelService = {
  /**
   * Get all TV channels
   */
  getAll: async (skip = 0, limit = 100): Promise<{ items: TVChannel[]; total: number }> => {
    const response = await apiClient.get(BASE_URL, {
      params: { skip, limit }
    });
    return response.data;
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

  /**
   * Update a TV channel
   */
  update: async (id: number, updates: TVChannelUpdate): Promise<TVChannel> => {
    const response = await apiClient.put(`${BASE_URL}/${id}`, updates);
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

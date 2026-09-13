/**
 * Named stream base URL API service (issue #62)
 *
 * Manages the named base URL entries used when generating playlist links.
 * A pattern containing `{channel_id}` (and optionally `{pid}`) is treated as
 * a mask; a pattern without placeholders is a plain prefix (like the legacy
 * `acestream://`).
 */
import apiClient from './apiClient';
import type { components } from '../types/api-generated';

/**
 * Stream base URL entry model
 */
export type StreamBaseUrl = components['schemas']['BaseUrlResponse'];

/**
 * Base URL creation DTO
 */
export type CreateBaseUrlDTO = components['schemas']['BaseUrlCreate'];

/**
 * Base URL update DTO
 */
export type UpdateBaseUrlDTO = components['schemas']['app__schemas__base_url__BaseUrlUpdate'];

/**
 * Stream base URL API service
 */
export const baseUrlService = {
  /**
   * Get all named base URL entries
   */
  getBaseUrls: async (): Promise<StreamBaseUrl[]> => {
    const { data } = await apiClient.get('/v1/base-urls');
    return data;
  },

  /**
   * Create a new named base URL entry (409 on duplicate name)
   */
  createBaseUrl: async (baseUrlData: CreateBaseUrlDTO): Promise<StreamBaseUrl> => {
    const { data } = await apiClient.post('/v1/base-urls', baseUrlData);
    return data;
  },

  /**
   * Update a named base URL entry. Setting is_default=true clears the
   * previous default on the backend.
   */
  updateBaseUrl: async (id: number, baseUrlData: UpdateBaseUrlDTO): Promise<StreamBaseUrl> => {
    const { data } = await apiClient.patch(`/v1/base-urls/${id}`, baseUrlData);
    return data;
  },

  /**
   * Delete a named base URL entry
   */
  deleteBaseUrl: async (id: number): Promise<void> => {
    await apiClient.delete(`/v1/base-urls/${id}`);
  }
};

export default baseUrlService;

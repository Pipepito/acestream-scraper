/**
 * Acestream Channel API service
 */
import apiClient from './apiClient';

/**
 * Channel model interface
 */
export interface AcestreamChannel {
  id: string;
  name: string;
  last_seen: string;
  last_processed?: string;
  status: string;
  source_url?: string;
  scraped_url_id?: number;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  m3u_source?: string;
  original_url?: string;
  is_online: boolean;
  last_checked?: string;
  check_error?: string;
  epg_update_protected: boolean;
  tv_channel_id?: number;
  is_active?: boolean; // Added for inline edit/quick actions
}

/**
 * Acestream Channel creation DTO
 */
export interface CreateAcestreamChannelDTO {
  id: string;
  name: string;
  source_url?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  original_url?: string;
  epg_update_protected?: boolean;
  tv_channel_id?: number;
}

/**
 * Acestream Channel update DTO
 */
export interface UpdateAcestreamChannelDTO {
  name?: string;
  source_url?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  original_url?: string;
  epg_update_protected?: boolean;
  tv_channel_id?: number;
  is_online?: boolean; // For online/offline status
  is_active?: boolean; // For activation/deactivation (matches backend)
}

/**
 * Acestream Channel filter parameters
 */
export interface AcestreamChannelFilters {
  search?: string;
  group?: string;
  is_active?: boolean;
  is_online?: boolean;
  id?: string; // Acestream ID filter
  country?: string;
  language?: string;
  page?: number;
  page_size?: number;
  active_only?: boolean; // Added to support backend override
}

export interface PaginatedAcestreamChannels {
  items: AcestreamChannel[];
  total: number;
}

/**
 * Channel API service
 */
const acestreamChannelService = {
  /**
   * Get all channels with optional filtering
   */
  getAcestreamChannels: async (filters?: AcestreamChannelFilters): Promise<PaginatedAcestreamChannels> => {
    // Convert string values for is_online and is_active to booleans if present
    const params = { ...filters };
    if (typeof params.is_online === 'string') {
      params.is_online = params.is_online === 'true';
    }
    if (typeof params.is_active === 'string') {
      params.is_active = params.is_active === 'true';
    }
    // Only set active_only if is_active is explicitly true or false
    if (params.is_active === true || params.is_active === false) {
      params.active_only = false;
    } else {
      delete params.is_active;
      delete params.active_only;
    }
    const { data } = await apiClient.get('/v1/acestream-channels', { params });
    return data;
  },

  /**
   * Get a channel by ID
   */
  getAcestreamChannel: async (id: string): Promise<AcestreamChannel> => {
    const { data } = await apiClient.get(`/v1/acestream-channels/${id}`);
    return data;
  },

  /**
   * Create a new channel
   */
  createAcestreamChannel: async (channelData: CreateAcestreamChannelDTO): Promise<AcestreamChannel> => {
    const { data } = await apiClient.post('/v1/acestream-channels', channelData);
    return data;
  },

  /**
   * Update a channel
   */
  updateAcestreamChannel: async (id: string, channelData: UpdateAcestreamChannelDTO): Promise<AcestreamChannel> => {
    const { data } = await apiClient.put(`/v1/acestream-channels/${id}`, channelData);
    return data;
  },

  /**
   * Delete a channel
   */
  deleteAcestreamChannel: async (id: string): Promise<void> => {
    await apiClient.delete(`/v1/acestream-channels/${id}`);
  },

  /**
   * Check channel status
   */
  checkAcestreamChannelStatus: async (id: string): Promise<AcestreamChannel> => {
    const { data } = await apiClient.post(`/v1/acestream-channels/${id}/check_status`);
    return data;
  },

  /**
   * Get all unique channel categories
   */
  // No categories endpoint for acestream channels

  /**
   * Get all unique channel groups
   */
  getGroups: async (): Promise<string[]> => {
    const { data } = await apiClient.get('/v1/acestream-channels/groups');
    return data;
  },

  /**
   * Bulk delete channels
   */
  bulkDeleteAcestreamChannels: async (ids: string[]): Promise<void> => {
    await apiClient.post('/v1/acestream-channels/bulk_delete', { acestreamchannel_ids: ids });
  },

  /**
   * Bulk edit channels
   */
  bulkEditAcestreamChannels: async (
    ids: string[],
    fields: Partial<UpdateAcestreamChannelDTO>
  ): Promise<AcestreamChannel[]> => {
    const { data } = await apiClient.put('/v1/acestream-channels/bulk_edit', { acestreamchannel_ids: ids, fields });
    return data;
  },

  /**
   * Bulk activate/deactivate channels
   */
  bulkActivateAcestreamChannels: async (ids: string[], active: boolean): Promise<AcestreamChannel[]> => {
    const { data } = await apiClient.post('/v1/acestream-channels/bulk_activate', { acestreamchannel_ids: ids, active });
    return data;
  },

  /**
   * Export all channels as CSV
   */
  exportAcestreamChannelsCSV: async (): Promise<Blob> => {
    const response = await apiClient.get('/v1/acestream-channels/export_csv', { responseType: 'blob' });
    return response.data;
  },

  /**
   * Get activity log for a specific channel
   */
  getAcestreamChannelActivityLog: async (
    acestreamChannelId: string,
    params?: { days?: number; type?: string; page?: number; page_size?: number }
  ): Promise<any> => {
    const { data } = await apiClient.get(`/v1/activity/acestream-channels/${acestreamChannelId}/activity_log`, { params });
    return data;
  },

  /**
   * Assign an Acestream channel to a TV channel
   */
  assignToTVChannel: async (acestreamChannelId: string, tvChannelId: number) => {
    return apiClient.post(`/tv-channels/${tvChannelId}/acestreams`, {
      acestream_channel_id: acestreamChannelId
    });
  },
};

export { acestreamChannelService };
export default acestreamChannelService;

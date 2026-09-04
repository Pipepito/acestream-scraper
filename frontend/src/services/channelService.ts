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
  is_online: boolean | null;
  last_checked?: string;
  check_error?: string;
  epg_update_protected: boolean;
  tv_channel_id?: number;
  tv_channel_name?: string;
  tv_channel_is_favorite?: boolean;
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
  is_online?: boolean | null; // For online/offline status
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

export interface ChannelStatusSummary {
  total_channels: number;
  active_channels: number;
  online: number;
  offline: number;
  unknown: number;
  recent_checks: number;
}

export interface PaginatedAcestreamChannels {
  items: AcestreamChannel[];
  total: number;
}

interface ActivityLogResponse {
  items?: Array<{
    id: number;
    timestamp: string;
    type: string;
    message: string;
    details?: string;
    user?: string;
  }>;
  total?: number;
}

interface CheckAllStatusesResponse {
  message?: string;
}

function parseBooleanFilter(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') {
    return value;
  }

  if (typeof value === 'string') {
    if (value === 'true') {
      return true;
    }
    if (value === 'false') {
      return false;
    }
  }

  return undefined;
}

/**
 * Channel API service
 */
const acestreamChannelService = {
  /** Online/offline/unknown counts across all channels. */
  getStatusSummary: async (): Promise<ChannelStatusSummary> => {
    const { data } = await apiClient.get<ChannelStatusSummary>('/v1/channels/status_summary');
    return data;
  },

  /**
   * Get all channels with optional filtering
   */
  getAcestreamChannels: async (filters?: AcestreamChannelFilters): Promise<PaginatedAcestreamChannels> => {
    const params = { ...filters };

    const parsedOnline = parseBooleanFilter(params.is_online);
    if (parsedOnline !== undefined) {
      params.is_online = parsedOnline;
    } else {
      delete params.is_online;
    }

    const parsedActive = parseBooleanFilter(params.is_active);
    if (parsedActive !== undefined) {
      params.is_active = parsedActive;
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
   * Trigger a bulk status check for all channels
   */
  checkAllStatuses: async (): Promise<CheckAllStatusesResponse> => {
    const { data } = await apiClient.post('/v1/channels/check_status_all', {});
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
  ): Promise<ActivityLogResponse> => {
    const { data } = await apiClient.get(`/v1/activity/acestream-channels/${acestreamChannelId}/activity_log`, { params });
    return data;
  },

  /**
   * Assign an Acestream channel to a TV channel
   */
  assignToTVChannel: async (acestreamChannelId: string, tvChannelId: number) => {
    return apiClient.post(`/v1/tv-channels/${tvChannelId}/acestreams`, {
      acestream_channel_id: acestreamChannelId
    });
  },
};

export { acestreamChannelService };
export default acestreamChannelService;

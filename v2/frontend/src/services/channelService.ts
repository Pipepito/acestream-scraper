/**
 * Channel API service
 */
import apiClient from './apiClient';

/**
 * Channel model interface
 */
export interface Channel {
  id: string;
  name: string;
  added_at: string;
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
}

/**
 * Channel creation DTO
 */
export interface CreateChannelDTO {
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
 * Channel update DTO
 */
export interface UpdateChannelDTO {
  name?: string;
  source_url?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  original_url?: string;
  epg_update_protected?: boolean;
  tv_channel_id?: number;
  is_online?: boolean;
}

/**
 * Channel filter parameters
 */
export interface ChannelFilters {
  group?: string;
  status?: string;
  search?: string;
  is_online?: boolean;
  page?: number;
  page_size?: number;
}

/**
 * Channel API service
 */
export const channelService = {
  /**
   * Get all channels with optional filtering
   */
  getChannels: async (filters?: ChannelFilters): Promise<Channel[]> => {
    const { data } = await apiClient.get('/v1/channels', { params: filters });
    return data;
  },

  /**
   * Get a channel by ID
   */
  getChannel: async (id: string): Promise<Channel> => {
    const { data } = await apiClient.get(`/v1/channels/${id}`);
    return data;
  },

  /**
   * Create a new channel
   */
  createChannel: async (channelData: CreateChannelDTO): Promise<Channel> => {
    const { data } = await apiClient.post('/v1/channels', channelData);
    return data;
  },

  /**
   * Update a channel
   */
  updateChannel: async (id: string, channelData: UpdateChannelDTO): Promise<Channel> => {
    const { data } = await apiClient.patch(`/v1/channels/${id}`, channelData);
    return data;
  },

  /**
   * Delete a channel
   */
  deleteChannel: async (id: string): Promise<void> => {
    await apiClient.delete(`/v1/channels/${id}`);
  },

  /**
   * Check channel status
   */
  checkChannelStatus: async (id: string): Promise<Channel> => {
    const { data } = await apiClient.post(`/v1/channels/${id}/check_status`);
    return data;
  },
};

export default channelService;

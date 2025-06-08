/**
 * EPG API service
 */
import apiClient from './apiClient';

/**
 * EPG Source model interface
 */
export interface EPGSource {
  id: number;
  url: string;
  name: string;
  enabled: boolean;
  last_updated?: string;
  error_count: number;
  last_error?: string;
}

/**
 * EPG Channel model interface
 */
export interface EPGChannel {
  id: number;
  epg_source_id: number;
  channel_xml_id: string;
  name: string;
  icon_url?: string;
  language?: string;
  created_at: string;
  updated_at: string;
}

/**
 * EPG Program model interface
 */
export interface EPGProgram {
  id: number;
  epg_channel_id: number;
  program_xml_id?: string;
  start_time: string;
  end_time: string;
  title: string;
  subtitle?: string;
  description?: string;
  category?: string;
  image_url?: string;
}

/**
 * EPG String Mapping model interface
 */
export interface EPGStringMapping {
  id: number;
  epg_channel_id: number;
  search_pattern: string;
  is_exclusion: boolean;
}

/**
 * EPG Source creation DTO
 */
export interface CreateEPGSourceDTO {
  url: string;
  name: string;
  enabled?: boolean;
}

/**
 * EPG Source update DTO
 */
export interface UpdateEPGSourceDTO {
  url?: string;
  name?: string;
  enabled?: boolean;
}

/**
 * EPG Channel Mapping DTO
 */
export interface EPGChannelMappingDTO {
  epg_channel_id: number;
  tv_channel_id: number;
}

/**
 * EPG Refresh Result interface
 */
export interface EPGRefreshResult {
  source_id: number;
  channels_found: number;
  programs_found: number;
  duration_seconds: number;
  success: boolean;
  error?: string;
}

/**
 * EPG API service
 */
export const epgService = {
  /**
   * Get all EPG sources
   */
  getSources: async (): Promise<EPGSource[]> => {
    const { data } = await apiClient.get('/v1/epg/sources');
    return data;
  },

  /**
   * Get a specific EPG source
   */
  getSource: async (id: number): Promise<EPGSource> => {
    const { data } = await apiClient.get(`/v1/epg/sources/${id}`);
    return data;
  },

  /**
   * Create a new EPG source
   */
  createSource: async (sourceData: CreateEPGSourceDTO): Promise<EPGSource> => {
    const { data } = await apiClient.post('/v1/epg/sources', sourceData);
    return data;
  },

  /**
   * Update an EPG source
   */
  updateSource: async (id: number, sourceData: UpdateEPGSourceDTO): Promise<EPGSource> => {
    const { data } = await apiClient.patch(`/v1/epg/sources/${id}`, sourceData);
    return data;
  },

  /**
   * Delete an EPG source
   */
  deleteSource: async (id: number): Promise<void> => {
    await apiClient.delete(`/v1/epg/sources/${id}`);
  },

  /**
   * Refresh an EPG source
   */
  refreshSource: async (id: number): Promise<EPGRefreshResult> => {
    const { data } = await apiClient.post(`/v1/epg/sources/${id}/refresh`);
    return data;
  },

  /**
   * Refresh all EPG sources
   */
  refreshAllSources: async (): Promise<EPGRefreshResult[]> => {
    const { data } = await apiClient.post('/v1/epg/sources/refresh_all');
    return data;
  },

  /**
   * Get EPG channels for a source
   */
  getChannels: async (sourceId?: number): Promise<EPGChannel[]> => {
    const params = sourceId ? { source_id: sourceId } : {};
    const { data } = await apiClient.get('/v1/epg/channels', { params });
    return data;
  },

  /**
   * Get a specific EPG channel
   */
  getChannel: async (id: number): Promise<EPGChannel> => {
    const { data } = await apiClient.get(`/v1/epg/channels/${id}`);
    return data;
  },

  /**
   * Map an EPG channel to a TV channel
   */
  mapChannelToTV: async (mapping: EPGChannelMappingDTO): Promise<void> => {
    await apiClient.post('/v1/epg/channels/map', mapping);
  },

  /**
   * Remove a mapping between EPG channel and TV channel
   */
  unmapChannel: async (epgChannelId: number, tvChannelId: number): Promise<void> => {
    await apiClient.delete(`/v1/epg/channels/map`, {
      data: { epg_channel_id: epgChannelId, tv_channel_id: tvChannelId }
    });
  },

  /**
   * Get EPG programs for a channel
   */
  getPrograms: async (channelId: number, startDate?: string, endDate?: string): Promise<EPGProgram[]> => {
    const params = { start_date: startDate, end_date: endDate };
    const { data } = await apiClient.get(`/v1/epg/channels/${channelId}/programs`, { params });
    return data;
  },
  
  /**
   * Get EPG string mappings for a channel
   */
  getStringMappings: async (channelId: number): Promise<EPGStringMapping[]> => {
    const { data } = await apiClient.get(`/v1/epg/channels/${channelId}/mappings`);
    return data;
  },

  /**
   * Add a string mapping
   */
  addStringMapping: async (channelId: number, pattern: string, isExclusion: boolean): Promise<EPGStringMapping> => {
    const { data } = await apiClient.post(`/v1/epg/channels/${channelId}/mappings`, {
      search_pattern: pattern,
      is_exclusion: isExclusion
    });
    return data;
  },

  /**
   * Delete a string mapping
   */
  deleteStringMapping: async (id: number): Promise<void> => {
    await apiClient.delete(`/v1/epg/mappings/${id}`);
  }
};

export default epgService;

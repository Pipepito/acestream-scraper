/**
 * Playlist API service
 */
import apiClient from './apiClient';

/**
 * Playlist filter parameters
 */
export interface PlaylistFilters {
  group?: string;
  search?: string;
  only_online?: boolean;
  include_groups?: string[];
  exclude_groups?: string[];
}

/**
 * Playlist API service
 */
export const playlistService = {
  /**
   * Get M3U playlist with optional filters
   */
  getM3UPlaylist: async (filters?: PlaylistFilters): Promise<string> => {
    const { data } = await apiClient.get('/v1/playlists/m3u', { 
      params: filters,
      responseType: 'text'
    });
    return data;
  },

  /**
   * Get the playlist download URL with filters
   */
  getPlaylistDownloadUrl: (filters?: PlaylistFilters): string => {
    const params = new URLSearchParams();
    
    if (filters) {
      if (filters.group) params.append('group', filters.group);
      if (filters.search) params.append('search', filters.search);
      if (filters.only_online !== undefined) params.append('only_online', String(filters.only_online));
      if (filters.include_groups) {
        filters.include_groups.forEach(g => params.append('include_groups', g));
      }
      if (filters.exclude_groups) {
        filters.exclude_groups.forEach(g => params.append('exclude_groups', g));
      }
    }
    
    return `/api/v1/playlists/m3u?${params.toString()}`;
  },

  /**
   * Get available channel groups
   */
  getChannelGroups: async (): Promise<string[]> => {
    const { data } = await apiClient.get('/v1/playlists/groups');
    return data;
  }
};

export default playlistService;

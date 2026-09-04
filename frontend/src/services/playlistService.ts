/**
 * Playlist API service
 */
import apiClient from './apiClient';
import { getPlaylistDownloadBaseUrl } from '../config/runtime';
import { getApiToken } from './apiToken';

/**
 * Playlist filter parameters
 */
export interface PlaylistFilters {
  group?: string;
  search?: string;
  only_online?: boolean;
  favorites_only?: boolean;
  include_groups?: string[];
  exclude_groups?: string[];
  /** ID of a named stream base URL entry (see baseUrlService) */
  base_url_id?: number;
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
      if (filters.favorites_only !== undefined) params.append('favorites_only', String(filters.favorites_only));
      if (filters.include_groups) {
        filters.include_groups.forEach(g => params.append('include_groups', g));
      }
      if (filters.exclude_groups) {
        filters.exclude_groups.forEach(g => params.append('exclude_groups', g));
      }
      if (filters.base_url_id !== undefined) params.append('base_url_id', String(filters.base_url_id));
    }
    const base = getPlaylistDownloadBaseUrl({
      dev: process.env.NODE_ENV === 'development',
    });
    return `${base}/api/v1/playlists/m3u?${params.toString()}`;
  },

  /**
   * Get available channel groups
   */
  getChannelGroups: async (): Promise<string[]> => {
    const { data } = await apiClient.get('/v1/playlists/groups');
    return data;
  }
};

/** Absolute URL for a backend path, resolved against the public base URL when known. */
export const buildPublicUrl = (pathWithQuery: string, publicBaseUrl?: string): string => {
  const fallbackOrigin = typeof window === 'undefined' ? '' : window.location.origin;
  const origin = publicBaseUrl && publicBaseUrl.trim() !== '' ? publicBaseUrl.trim() : fallbackOrigin;
  if (!origin) return pathWithQuery;
  return new URL(pathWithQuery, origin.endsWith('/') ? origin : `${origin}/`).toString();
};

/** Absolute playlist URL for players on other devices (QR codes, copy button). */
export const getAbsolutePlaylistUrl = (filters?: PlaylistFilters, publicBaseUrl?: string): string => {
  const params = new URLSearchParams(playlistService.getPlaylistDownloadUrl(filters).split('?')[1] ?? '');
  const token = getApiToken();
  if (token) params.set('token', token);
  const query = params.toString();
  return buildPublicUrl(`/api/v1/playlists/m3u${query ? `?${query}` : ''}`, publicBaseUrl);
};

export default playlistService;

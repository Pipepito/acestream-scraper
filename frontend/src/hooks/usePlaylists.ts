/**
 * React Query hooks for playlists
 */
import { useQuery, UseQueryOptions } from 'react-query';
import { playlistService, PlaylistFilters } from '../services/playlistService';

/**
 * Hook for fetching M3U playlist
 */
export const useM3UPlaylist = (filters?: PlaylistFilters, options?: UseQueryOptions<string>) => {
  return useQuery<string>(
    ['m3u', filters], 
    () => playlistService.getM3UPlaylist(filters),
    {
      ...options,
      refetchOnWindowFocus: false // Don't refetch on window focus as this is a large string
    }
  );
};

/**
 * Hook for getting available channel groups
 */
export const useChannelGroups = (options?: UseQueryOptions<string[]>) => {
  return useQuery<string[]>(
    'channelGroups', 
    () => playlistService.getChannelGroups(),
    options
  );
};

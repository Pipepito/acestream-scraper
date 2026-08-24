/**
 * React Query hooks for playlists
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { playlistService, PlaylistFilters } from '../services/playlistService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

/**
 * Hook for fetching M3U playlist
 */
export const useM3UPlaylist = (filters?: PlaylistFilters, options?: QueryOpts<string>) => {
  return useQuery<string>({
    queryKey: ['m3u', filters],
    queryFn: () => playlistService.getM3UPlaylist(filters),
    ...options,
    refetchOnWindowFocus: false, // Don't refetch on window focus as this is a large string
  });
};

/**
 * Hook for getting available channel groups
 */
export const useChannelGroups = (options?: QueryOpts<string[]>) => {
  return useQuery<string[]>({
    queryKey: ['channelGroups'],
    queryFn: () => playlistService.getChannelGroups(),
    ...options,
  });
};

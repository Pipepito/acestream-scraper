
import { useMutation, useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import { tvChannelService, TVChannelListFilters } from '../services/tvChannelService';

export interface PaginatedTVChannels {
  items: TVChannel[];
  total: number;
}

const QUERY_KEYS = {
  ALL_TV_CHANNELS: 'tvChannels',
  TV_CHANNEL_DETAIL: 'tvChannel',
  TV_CHANNEL_ACESTREAMS: 'tvChannelAcestreams',
};

/**
 * Hook for fetching all TV channels
 */
export const useAllTVChannels = (skip = 0, limit = 100) => {
  return useQuery<PaginatedTVChannels>({
    queryKey: [QUERY_KEYS.ALL_TV_CHANNELS, skip, limit],
    queryFn: () => tvChannelService.getAll(skip, limit),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
};

export const useTVChannelCatalog = (filters?: TVChannelListFilters) => {
  return useQuery<TVChannel[]>({
    queryKey: [QUERY_KEYS.ALL_TV_CHANNELS, 'catalog', { favorites: filters?.favorites ?? false, search: filters?.search ?? '' }],
    queryFn: () => tvChannelService.getCatalog(undefined, filters),
    staleTime: 1000 * 60 * 5,
    // Keep the previous list rendered while a filter change refetches, so
    // toggling the favorites switch doesn't unmount the whole page.
    placeholderData: keepPreviousData,
  });
};

/**
 * Hook for fetching a single TV channel by ID
 */
export const useTVChannel = (id: number) => {
  return useQuery({
    queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL, id],
    queryFn: () => tvChannelService.getById(id),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!id,
  });
};

/**
 * Hook for fetching acestreams associated with a TV channel
 */
export const useTVChannelAcestreams = (id: number) => {
  return useQuery({
    queryKey: [QUERY_KEYS.TV_CHANNEL_ACESTREAMS, id],
    queryFn: () => tvChannelService.getAcestreams(id),
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: !!id,
  });
};

/**
 * Hook for creating a new TV channel
 */
export const useCreateTVChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tvChannel: TVChannelCreate) => tvChannelService.create(tvChannel),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
    },
  });
};

/**
 * Hook for updating a TV channel
 */
export const useUpdateTVChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: TVChannelUpdate }) =>
      tvChannelService.update(id, updates),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL, id] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
    },
  });
};

/**
 * Hook for toggling a TV channel's favorite flag
 */
export const useToggleTVChannelFavorite = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, value }: { id: number; value?: boolean }) => tvChannelService.toggleFavorite(id, value),
    onSuccess: (data, { id }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL, id] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
    },
  });
};

/**
 * Hook for deleting a TV channel
 */
export const useDeleteTVChannel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => tvChannelService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
    },
  });
};

/**
 * Hook for associating an acestream with a TV channel
 */
export const useAssociateAcestream = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tvChannelId, aceStreamId }: { tvChannelId: number; aceStreamId: string }) =>
      tvChannelService.associateAcestream(tvChannelId, aceStreamId),
    onSuccess: (_, { tvChannelId }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL, tvChannelId] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_ACESTREAMS, tvChannelId] });
    },
  });
};

/**
 * Hook for removing an acestream association from a TV channel
 */
export const useRemoveAcestreamAssociation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ tvChannelId, aceStreamId }: { tvChannelId: number; aceStreamId: string }) =>
      tvChannelService.removeAcestreamAssociation(tvChannelId, aceStreamId),
    onSuccess: (_, { tvChannelId }) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL, tvChannelId] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_ACESTREAMS, tvChannelId] });
    },
  });
};

/**
 * Hook for batch assigning acestreams to TV channels
 */
export const useBatchAssignAcestreams = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assignments: Record<string, string[]>) => tvChannelService.batchAssignAcestreams(assignments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_ACESTREAMS] });
    },
  });
};

/**
 * Hook for associating acestreams with TV channels based on EPG IDs
 */
export const useAssociateByEpg = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => tvChannelService.associateByEpg(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_ACESTREAMS] });
    },
  });
};

/**
 * Hook for updating EPG IDs for all TV channels
 */
export const useBulkUpdateEpg = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => tvChannelService.bulkUpdateEpg(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.ALL_TV_CHANNELS] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.TV_CHANNEL_DETAIL] });
    },
  });
};

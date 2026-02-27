
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import { tvChannelService } from '../services/tvChannelService';

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
  return useQuery<PaginatedTVChannels>(
    [QUERY_KEYS.ALL_TV_CHANNELS, skip, limit],
    () => tvChannelService.getAll(skip, limit),
    {
      staleTime: 1000 * 60 * 5, // 5 minutes
    }
  );
};

/**
 * Hook for fetching a single TV channel by ID
 */
export const useTVChannel = (id: number) => {
  return useQuery(
    [QUERY_KEYS.TV_CHANNEL_DETAIL, id],
    () => tvChannelService.getById(id),
    {
      staleTime: 1000 * 60 * 5, // 5 minutes
      enabled: !!id,
    }
  );
};

/**
 * Hook for fetching acestreams associated with a TV channel
 */
export const useTVChannelAcestreams = (id: number) => {
  return useQuery(
    [QUERY_KEYS.TV_CHANNEL_ACESTREAMS, id],
    () => tvChannelService.getAcestreams(id),
    {
      staleTime: 1000 * 60 * 5, // 5 minutes
      enabled: !!id,
    }
  );
};

/**
 * Hook for creating a new TV channel
 */
export const useCreateTVChannel = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (tvChannel: TVChannelCreate) => tvChannelService.create(tvChannel),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.ALL_TV_CHANNELS);
      },
    }
  );
};

/**
 * Hook for updating a TV channel
 */
export const useUpdateTVChannel = () => {
  const queryClient = useQueryClient();

  return useMutation(
    ({ id, updates }: { id: number; updates: TVChannelUpdate }) =>
      tvChannelService.update(id, updates),
    {
      onSuccess: (data, { id }) => {
        queryClient.invalidateQueries([QUERY_KEYS.TV_CHANNEL_DETAIL, id]);
        queryClient.invalidateQueries(QUERY_KEYS.ALL_TV_CHANNELS);
      },
    }
  );
};

/**
 * Hook for deleting a TV channel
 */
export const useDeleteTVChannel = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (id: number) => tvChannelService.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.ALL_TV_CHANNELS);
      },
    }
  );
};

/**
 * Hook for associating an acestream with a TV channel
 */
export const useAssociateAcestream = () => {
  const queryClient = useQueryClient();

  return useMutation(
    ({ tvChannelId, aceStreamId }: { tvChannelId: number; aceStreamId: string }) =>
      tvChannelService.associateAcestream(tvChannelId, aceStreamId),
    {
      onSuccess: (_, { tvChannelId }) => {
        queryClient.invalidateQueries([QUERY_KEYS.TV_CHANNEL_DETAIL, tvChannelId]);
        queryClient.invalidateQueries([QUERY_KEYS.TV_CHANNEL_ACESTREAMS, tvChannelId]);
      },
    }
  );
};

/**
 * Hook for removing an acestream association from a TV channel
 */
export const useRemoveAcestreamAssociation = () => {
  const queryClient = useQueryClient();

  return useMutation(
    ({ tvChannelId, aceStreamId }: { tvChannelId: number; aceStreamId: string }) =>
      tvChannelService.removeAcestreamAssociation(tvChannelId, aceStreamId),
    {
      onSuccess: (_, { tvChannelId }) => {
        queryClient.invalidateQueries([QUERY_KEYS.TV_CHANNEL_DETAIL, tvChannelId]);
        queryClient.invalidateQueries([QUERY_KEYS.TV_CHANNEL_ACESTREAMS, tvChannelId]);
      },
    }
  );
};

/**
 * Hook for batch assigning acestreams to TV channels
 */
export const useBatchAssignAcestreams = () => {
  const queryClient = useQueryClient();

  return useMutation(
    (assignments: Record<string, string[]>) => tvChannelService.batchAssignAcestreams(assignments),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.ALL_TV_CHANNELS);
        queryClient.invalidateQueries(QUERY_KEYS.TV_CHANNEL_DETAIL);
        queryClient.invalidateQueries(QUERY_KEYS.TV_CHANNEL_ACESTREAMS);
      },
    }
  );
};

/**
 * Hook for associating acestreams with TV channels based on EPG IDs
 */
export const useAssociateByEpg = () => {
  const queryClient = useQueryClient();

  return useMutation(
    () => tvChannelService.associateByEpg(),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.ALL_TV_CHANNELS);
        queryClient.invalidateQueries(QUERY_KEYS.TV_CHANNEL_DETAIL);
        queryClient.invalidateQueries(QUERY_KEYS.TV_CHANNEL_ACESTREAMS);
      },
    }
  );
};

/**
 * Hook for updating EPG IDs for all TV channels
 */
export const useBulkUpdateEpg = () => {
  const queryClient = useQueryClient();

  return useMutation(
    () => tvChannelService.bulkUpdateEpg(),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(QUERY_KEYS.ALL_TV_CHANNELS);
        queryClient.invalidateQueries(QUERY_KEYS.TV_CHANNEL_DETAIL);
      },
    }
  );
};

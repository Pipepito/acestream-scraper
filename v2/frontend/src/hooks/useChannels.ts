/**
 * React Query hooks for channels
 */
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import { channelService, Channel, CreateChannelDTO, UpdateChannelDTO, ChannelFilters } from '../services/channelService';

/**
 * Hook for fetching channels list
 */
export const useChannels = (filters?: ChannelFilters, options?: UseQueryOptions<Channel[]>) => {
  return useQuery<Channel[]>(
    ['channels', filters], 
    () => channelService.getChannels(filters),
    options
  );
};

/**
 * Hook for fetching a single channel
 */
export const useChannel = (id: string, options?: UseQueryOptions<Channel>) => {
  return useQuery<Channel>(
    ['channel', id],
    () => channelService.getChannel(id),
    {
      enabled: !!id,
      ...options
    }
  );
};

/**
 * Hook for creating a channel
 */
export const useCreateChannel = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (channelData: CreateChannelDTO) => channelService.createChannel(channelData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('channels');
      }
    }
  );
};

/**
 * Hook for updating a channel
 */
export const useUpdateChannel = (id: string) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (channelData: UpdateChannelDTO) => channelService.updateChannel(id, channelData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['channel', id]);
        queryClient.invalidateQueries('channels');
      }
    }
  );
};

/**
 * Hook for deleting a channel
 */
export const useDeleteChannel = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (id: string) => channelService.deleteChannel(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('channels');
      }
    }
  );
};

/**
 * Hook for checking channel status
 */
export const useCheckChannelStatus = (id: string) => {
  const queryClient = useQueryClient();
  
  return useMutation(
    () => channelService.checkChannelStatus(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['channel', id]);
        queryClient.invalidateQueries('channels');
      }
    }
  );
};

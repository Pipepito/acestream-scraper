
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import {
  AcestreamChannel,
  AcestreamChannelFilters,
  CreateAcestreamChannelDTO,
  PaginatedAcestreamChannels,
  UpdateAcestreamChannelDTO,
  acestreamChannelService,
} from '../services/channelService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

// Fetch all Acestream channels
export const useAcestreamChannels = (
  filters?: AcestreamChannelFilters,
  options?: QueryOpts<PaginatedAcestreamChannels>
) => {
  return useQuery<PaginatedAcestreamChannels>({
    queryKey: ['acestream-channels', filters],
    queryFn: () => acestreamChannelService.getAcestreamChannels(filters),
    ...options,
  });
};

// Fetch a single Acestream channel
export const useAcestreamChannel = (id: string, options?: QueryOpts<AcestreamChannel>) => {
  return useQuery<AcestreamChannel>({
    queryKey: ['acestream-channel', id],
    queryFn: () => acestreamChannelService.getAcestreamChannel(id),
    enabled: !!id,
    ...options,
  });
};

// Create Acestream channel
export const useCreateAcestreamChannel = () => {
  const queryClient = useQueryClient();
  return useMutation<AcestreamChannel, Error, CreateAcestreamChannelDTO>({
    mutationFn: (channelData: CreateAcestreamChannelDTO) =>
      acestreamChannelService.createAcestreamChannel(channelData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
    },
  });
};

// Update Acestream channel
export const useUpdateAcestreamChannel = (id: string) => {
  const queryClient = useQueryClient();
  return useMutation<AcestreamChannel, Error, UpdateAcestreamChannelDTO>({
    mutationFn: (channelData: UpdateAcestreamChannelDTO) =>
      acestreamChannelService.updateAcestreamChannel(id, channelData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acestream-channel', id] });
      queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
    },
  });
};

// Delete Acestream channel
export const useDeleteAcestreamChannel = () => {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (id: string) => acestreamChannelService.deleteAcestreamChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acestream-channels'] });
    },
  });
};

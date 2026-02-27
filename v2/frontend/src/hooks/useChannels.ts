
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from 'react-query';
import {
  AcestreamChannel,
  AcestreamChannelFilters,
  CreateAcestreamChannelDTO,
  PaginatedAcestreamChannels,
  UpdateAcestreamChannelDTO,
  acestreamChannelService,
} from '../services/channelService';

// Fetch all Acestream channels
export const useAcestreamChannels = (
  filters?: AcestreamChannelFilters,
  options?: UseQueryOptions<PaginatedAcestreamChannels>
) => {
  return useQuery<PaginatedAcestreamChannels>(
    ['acestream-channels', filters],
    () => acestreamChannelService.getAcestreamChannels(filters),
    options
  );
};

// Fetch a single Acestream channel
export const useAcestreamChannel = (id: string, options?: UseQueryOptions<AcestreamChannel>) => {
  return useQuery<AcestreamChannel>(
    ['acestream-channel', id],
    () => acestreamChannelService.getAcestreamChannel(id),
    {
      enabled: !!id,
      ...options
    }
  );
};

// Create Acestream channel
export const useCreateAcestreamChannel = () => {
  const queryClient = useQueryClient();
  return useMutation<AcestreamChannel, Error, CreateAcestreamChannelDTO>(
    (channelData: CreateAcestreamChannelDTO) => acestreamChannelService.createAcestreamChannel(channelData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('acestream-channels');
      }
    }
  );
};

// Update Acestream channel
export const useUpdateAcestreamChannel = (id: string) => {
  const queryClient = useQueryClient();
  return useMutation<AcestreamChannel, Error, UpdateAcestreamChannelDTO>(
    (channelData: UpdateAcestreamChannelDTO) => acestreamChannelService.updateAcestreamChannel(id, channelData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['acestream-channel', id]);
        queryClient.invalidateQueries('acestream-channels');
      }
    }
  );
};

// Delete Acestream channel
export const useDeleteAcestreamChannel = () => {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>(
    (id: string) => acestreamChannelService.deleteAcestreamChannel(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('acestream-channels');
      }
    }
  );
};

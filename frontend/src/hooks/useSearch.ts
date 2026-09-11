
import { useMutation, useQuery, keepPreviousData, UseQueryOptions } from '@tanstack/react-query';
import { searchService, SearchResponse } from '../services/searchService';
import { acestreamChannelService, CreateAcestreamChannelDTO, AcestreamChannel } from '../services/channelService';

type QueryOpts<T> = Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;

export const useSearch = (
  query: string = '',
  page: number = 1,
  pageSize: number = 10,
  category?: string,
  options?: QueryOpts<SearchResponse>
) => {
  return useQuery<SearchResponse>({
    queryKey: ['search', query, page, pageSize, category],
    queryFn: () => searchService.search(query, page, pageSize, category),
    placeholderData: keepPreviousData,
    ...options,
  });
};


// Mutation to add an Acestream channel
export const useAddAcestreamChannel = () => {
  return useMutation<AcestreamChannel, Error, CreateAcestreamChannelDTO>({
    mutationFn: (channel: CreateAcestreamChannelDTO) => acestreamChannelService.createAcestreamChannel(channel),
  });
};

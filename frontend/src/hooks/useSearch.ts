
import { useMutation, useQuery, UseQueryOptions } from 'react-query';
import { searchService, SearchResponse } from '../services/searchService';
import { acestreamChannelService, CreateAcestreamChannelDTO, AcestreamChannel } from '../services/channelService';

export const useSearch = (
  query: string = '',
  page: number = 1,
  pageSize: number = 10,
  category?: string,
  options?: UseQueryOptions<SearchResponse>
) => {
  return useQuery<SearchResponse>(
    ['search', query, page, pageSize, category],
    () => searchService.search(query, page, pageSize, category),
    {
      keepPreviousData: true,
      ...options
    }
  );
};


// Mutation to add an Acestream channel
export const useAddAcestreamChannel = () => {
  return useMutation<AcestreamChannel, Error, CreateAcestreamChannelDTO>(
    (channel: CreateAcestreamChannelDTO) => acestreamChannelService.createAcestreamChannel(channel)
  );
};

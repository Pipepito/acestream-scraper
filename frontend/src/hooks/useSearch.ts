
import { useMutation, useQuery, keepPreviousData, UseQueryOptions } from '@tanstack/react-query';
import { searchService, SearchResponse, SearchResultItem } from '../services/searchService';
import { acestreamChannelService, AcestreamChannel } from '../services/channelService';

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


export const useAddSearchResult = () => {
  return useMutation<AcestreamChannel, Error, SearchResultItem>({
    mutationFn: async (channel) => {
      const contentId = await searchService.resolveContentId(channel.id);
      return acestreamChannelService.createAcestreamChannel({
        id: contentId,
        name: channel.name,
        group: channel.categories?.[0],
      });
    },
  });
};

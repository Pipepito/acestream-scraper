
import { useMutation, useQuery, keepPreviousData, UseQueryOptions } from '@tanstack/react-query';
import { searchService, SearchResponse, SearchResultItem, SearchImportOutcome } from '../services/searchService';

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
  return useMutation<SearchImportOutcome, Error, SearchResultItem>({
    mutationFn: async (channel) => {
      const result = await searchService.importResults([channel]);
      return result.items[0];
    },
  });
};

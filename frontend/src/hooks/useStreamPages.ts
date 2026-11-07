import { useInfiniteQuery } from '@tanstack/react-query';
import channelService, { type PaginatedAcestreamChannels } from '../services/channelService';

export const STREAM_PAGE_SIZE = 50;

export interface StreamPageFilters {
  search: string;
  onlineOnly: boolean;
}

/** Live TV streams mode: pages of 50, loaded on request or when the end of the list comes into view. */
export const useStreamPages = ({ search, onlineOnly }: StreamPageFilters) => useInfiniteQuery<PaginatedAcestreamChannels, Error, { pages: PaginatedAcestreamChannels[]; pageParams: unknown[] }, unknown[], number>({
  queryKey: ['acestream-channels', 'browse', { search, onlineOnly }],
  queryFn: ({ pageParam }) => channelService.getAcestreamChannels({
    search: search || undefined, page: pageParam, page_size: STREAM_PAGE_SIZE, is_active: true, ...(onlineOnly ? { is_online: true } : {}),
  }),
  initialPageParam: 1,
  getNextPageParam: (last, all) => all.reduce((count, page) => count + page.items.length, 0) < last.total ? all.length + 1 : undefined,
  refetchInterval: 30_000,
});

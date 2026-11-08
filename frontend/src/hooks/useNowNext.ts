import { useQueries } from '@tanstack/react-query';
import { tvChannelService, type TVChannelNowNext } from '../services/tvChannelService';

/** Guide reads grow with loaded catalogue pages, never with the entire installation. */
export const useNowNext = (channelIds: number[]) => {
  const batches: number[][] = [];
  for (let start = 0; start < channelIds.length; start += 50) batches.push(channelIds.slice(start, start + 50));
  return useQueries({
    queries: batches.map(ids => ({
      queryKey: ['tvChannels', 'now-next', ids],
      queryFn: () => tvChannelService.nowNext(ids),
      staleTime: 60_000, refetchInterval: 60_000,
    })),
    combine: results => ({
      data: results.some(result => result.isPending) ? undefined : new Map(results.flatMap(result => result.data ?? []).map((row: TVChannelNowNext) => [row.tv_channel_id, row])),
      isError: results.some(result => result.isError),
    }),
  });
};

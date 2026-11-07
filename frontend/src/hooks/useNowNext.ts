import { useQuery } from '@tanstack/react-query';
import { tvChannelService, type TVChannelNowNext } from '../services/tvChannelService';

/** One batched Now/Next read for the whole Live TV list, keyed by TV channel id. */
export const useNowNext = () => useQuery({
  queryKey: ['tvChannels', 'now-next'],
  queryFn: tvChannelService.nowNext,
  staleTime: 60_000,
  refetchInterval: 60_000,
  select: (rows: TVChannelNowNext[]) => new Map(rows.map((row) => [row.tv_channel_id, row])),
});

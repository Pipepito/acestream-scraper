import React, { useEffect, useRef } from 'react';
import { Alert, Box, Button, LinearProgress, Stack, Typography } from '@mui/material';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import type { AcestreamChannel } from '../../services/channelService';
import { useStreamPages } from '../../hooks/useStreamPages';
import { formatRelativeTime } from '../../utils/format';
import PlayOnMenu from '../player/PlayOnMenu';

interface StreamListProps {
  search: string;
  onlineOnly: boolean;
  /** TV channel names by id, to say where an assigned stream lives. */
  tvNames: Map<number, string>;
  onWatch: (stream: AcestreamChannel) => void;
}

const statusText = (stream: AcestreamChannel) => {
  const state = stream.is_online === true ? 'Online' : stream.is_online === false ? 'Offline' : 'Unknown';
  return stream.last_checked ? `${state} · ${formatRelativeTime(stream.last_checked)}` : `${state} · not checked yet`;
};

/** Every stream, 50 at a time: a Show more button plus automatic loading near the end of the list. */
const StreamList: React.FC<StreamListProps> = ({ search, onlineOnly, tvNames, onWatch }) => {
  const streams = useStreamPages({ search, onlineOnly });
  const sentinel = useRef<HTMLDivElement>(null);
  const { fetchNextPage, hasNextPage, isFetchingNextPage } = streams;
  useEffect(() => {
    const node = sentinel.current;
    if (!node || !hasNextPage || typeof IntersectionObserver === 'undefined') return undefined;
    const observer = new IntersectionObserver((entries) => { if (entries.some((entry) => entry.isIntersecting) && !isFetchingNextPage) void fetchNextPage(); }, { rootMargin: '200px' });
    observer.observe(node);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);
  const items = streams.data?.pages.flatMap((page) => page.items) ?? [];
  const total = streams.data?.pages[0]?.total ?? 0;
  if (streams.isLoading) return <LinearProgress aria-label="Loading streams" />;
  if (streams.isError) return <Alert severity="error" action={<Button color="inherit" onClick={() => void streams.refetch()}>Retry</Button>}>Unable to load streams.</Alert>;
  if (!items.length) return <Alert severity="info">{search ? 'No streams match this search.' : onlineOnly ? 'No online streams.' : 'No streams yet.'}</Alert>;
  return <Box>
    {items.map((stream) => <Stack component="article" key={stream.id} aria-label={stream.name} direction="row" spacing={1.5} useFlexGap flexWrap="wrap" alignItems="center" sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
      <Box sx={{ flex: '1 1 180px', minWidth: 0 }}>
        <Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{stream.name}</Typography>
        <Typography variant="body2" color="text.secondary">{statusText(stream)}{stream.group ? ` · ${stream.group}` : ''}{stream.tv_channel_id && tvNames.get(stream.tv_channel_id) ? ` · in ${tvNames.get(stream.tv_channel_id)}` : ''}</Typography>
      </Box>
      <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap">
        <Button variant="outlined" startIcon={<PlayArrowRounded />} aria-label={`Watch ${stream.name}`} onClick={() => onWatch(stream)}>Watch</Button>
        <PlayOnMenu contentId={stream.id} title={stream.name} label="Send to player" />
      </Stack>
    </Stack>)}
    <Stack direction="row" spacing={2} alignItems="center" sx={{ py: 2 }}>
      <Typography variant="body2" color="text.secondary">Showing {items.length} of {total}</Typography>
      {hasNextPage ? <Button aria-label="Show more streams" disabled={isFetchingNextPage} onClick={() => void fetchNextPage()}>{isFetchingNextPage ? 'Loading…' : 'Show more'}</Button> : null}
    </Stack>
    <div ref={sentinel} aria-hidden />
  </Box>;
};

export default StreamList;

import React, { useEffect, useMemo, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Checkbox, FormControlLabel, LinearProgress, Pagination, Stack, TextField, Typography } from '@mui/material';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import { useTVChannelCatalog, useTVChannel } from '../hooks/useTVChannels';
import { useAcestreamChannels } from '../hooks/useChannels';
import type { AcestreamChannel } from '../services/channelService';
import ContentSection from '../components/layout/ContentSection';
import { formatRelativeTime } from '../utils/format';
import { useNow } from '../hooks/useNow';
import PageHeader from '../components/layout/PageHeader';
import StatusLine from '../components/StatusLine';
import ChannelGuide from '../components/player/ChannelGuide';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import PlayOnMenu from '../components/player/PlayOnMenu';

const PAGE_SIZE = 12;

const LiveTV: React.FC = () => {
  const catalog = useTVChannelCatalog();
  const [streamPage, setStreamPage] = useState(1);
  const [streamSearch, setStreamSearch] = useState('');
  const [playingStream, setPlayingStream] = useState<AcestreamChannel | null>(null);
  const unassigned = useAcestreamChannels({ assigned: false, is_online: true, page: streamPage, page_size: PAGE_SIZE, search: streamSearch }, { refetchInterval: 30_000 });
  const streamPageCount = Math.max(1, Math.ceil((unassigned.data?.total ?? 0) / PAGE_SIZE));
  useEffect(() => {
    if (unassigned.data && streamPage > streamPageCount) setStreamPage(streamPageCount);
  }, [unassigned.data, streamPage, streamPageCount]);
  const [search, setSearch] = useState('');
  const [favorites, setFavorites] = useState(false);
  const [page, setPage] = useState(1);
  const [params, setParams] = useSearchParams();
  const selectedId = Number(params.get('channel')) || 0;
  const selected = useTVChannel(selectedId);
  const now = useNow();
  const channels = useMemo(() => (catalog.data ?? []).filter((channel) => channel.is_active && channel.acestream_channels.length > 0
    && (!favorites || channel.is_favorite)
    && `${channel.name} ${channel.category ?? ''} ${channel.channel_number ?? ''}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()))
    .sort((a, b) => (a.channel_number ?? Infinity) - (b.channel_number ?? Infinity) || a.name.localeCompare(b.name)), [catalog.data, search, favorites]);
  const pageCount = Math.max(1, Math.ceil(channels.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const close = () => { const next = new URLSearchParams(params); next.delete('channel'); setParams(next, { replace: true }); };

  return <Box>
    <PageHeader title="Live TV" subtitle="Choose a channel, see what’s on, and watch."
      actions={<Button component={RouterLink} to="/tv-channels" variant="outlined">Manage channels</Button>} />
    <StatusLine items={[{ label: 'Channels', value: channels.length }, { label: 'Guide times', value: timezone }]} />
    <ContentSection title="TV channels">
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 2 }}>
        <TextField fullWidth label="Find a channel" type="search" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} />
        <FormControlLabel sx={{ flexShrink: 0 }} control={<Checkbox checked={favorites} onChange={(_event, checked) => { setFavorites(checked); setPage(1); }} />} label="Favorites only" />
      </Stack>
      {catalog.isLoading ? <LinearProgress aria-label="Loading channels" /> : null}
      {catalog.isError ? <Alert severity="error" action={<Button color="inherit" onClick={() => void catalog.refetch()}>Retry</Button>}>Unable to load channels.</Alert> : null}
      {!catalog.isLoading && !catalog.isError && channels.length === 0 ? <Alert severity="info">
        {search || favorites ? 'No channels match these filters.' : 'No active TV channels with streams yet. Add a channel and attach a stream in Manage channels.'}
      </Alert> : null}
      <Box>
        {channels.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE).map((channel) => <Box component="article" key={channel.id} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ xs: 'stretch', sm: 'center' }} sx={{ mb: 1 }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{channel.channel_number != null ? `${channel.channel_number}. ` : ''}{channel.name}</Typography>
              <Typography variant="body2" color="text.secondary">{channel.acestream_channels.length ? `${channel.acestream_channels.length} stream${channel.acestream_channels.length === 1 ? '' : 's'}` : 'No streams attached'}{channel.category ? ` · ${channel.category}` : ''}</Typography>
            </Box>
            <Stack direction="row" spacing={0.5} sx={{ flexShrink: 0 }}>
              <Button variant="contained" startIcon={<PlayArrowRounded />} disabled={!channel.acestream_channels.length}
                aria-label={`Watch ${channel.name}`} onClick={() => { const next = new URLSearchParams(params); next.set('channel', String(channel.id)); setParams(next); }}>Watch</Button>
              <PlayOnMenu contentId={channel.acestream_channels[0].id} title={channel.name} label="Send to player" />
            </Stack>
          </Stack>
          <ChannelGuide channel={channel} now={now} compact />
        </Box>)}
      </Box>
      {pageCount > 1 ? <Pagination count={pageCount} page={currentPage} onChange={(_event, value) => setPage(value)} size="small" siblingCount={0} sx={{ my: 2 }} /> : null}
    </ContentSection>
    <ContentSection title="Online streams without a channel" description="Online at their last status check. These streams are not attached to a TV channel.">
      <TextField fullWidth label="Find an unassigned stream" type="search" value={streamSearch}
        onChange={(event) => { setStreamSearch(event.target.value); setStreamPage(1); }} />
      {unassigned.isLoading ? <LinearProgress aria-label="Loading unassigned streams" /> : null}
      {unassigned.isError ? <Alert severity="error" action={<Button color="inherit" onClick={() => void unassigned.refetch()}>Retry</Button>}>Unable to load unassigned streams.</Alert> : null}
      {!unassigned.isLoading && !unassigned.isError && !unassigned.data?.items.length ? <Alert severity="info" sx={{ mt: 2 }}>
        {streamSearch ? 'No online unassigned streams match this search.' : 'No online streams without a channel.'}
      </Alert> : null}
      {unassigned.data?.items.map((stream) => <Stack component="article" key={stream.id} direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ xs: 'stretch', sm: 'center' }} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{stream.name}</Typography>
          <Typography variant="body2" color="text.secondary">Online at last check · {stream.last_checked ? formatRelativeTime(stream.last_checked) : 'Check time unavailable'}{stream.group ? ` · ${stream.group}` : ''}</Typography>
        </Box>
        <Stack direction="row" spacing={0.5} sx={{ flexShrink: 0 }}>
          <Button variant="outlined" startIcon={<PlayArrowRounded />} aria-label={`Watch ${stream.name}`} onClick={() => setPlayingStream(stream)}>Watch</Button>
          <PlayOnMenu contentId={stream.id} title={stream.name} label="Send to player" />
        </Stack>
      </Stack>)}
      {(unassigned.data?.total ?? 0) > PAGE_SIZE ? <Pagination aria-label="Unassigned stream pages" count={streamPageCount} page={streamPage} onChange={(_event, value) => setStreamPage(value)} size="small" siblingCount={0} sx={{ my: 2 }} /> : null}
    </ContentSection>
    <ChannelPlayerDialog open={Boolean(playingStream)} contentId={playingStream?.id ?? null} title={playingStream?.name ?? ''} onClose={() => setPlayingStream(null)} />
    {selectedId && selected.isLoading ? <LinearProgress aria-label="Loading selected channel" /> : null}
    {selectedId && selected.isError ? <Alert severity="error" action={<Button color="inherit" onClick={close}>Dismiss</Button>}>Unable to open this channel.</Alert> : null}
    {selected.data && selectedId && !selected.data.acestream_channels.length ? <Alert severity="info" action={<Button color="inherit" onClick={close}>Dismiss</Button>}>This channel has no streams attached.</Alert> : null}
    <ChannelPlayerDialog open={Boolean(selectedId && selected.data?.acestream_channels.length)} tvChannelId={selectedId}
      contentId={selected.data?.acestream_channels[0]?.id ?? null} title={selected.data?.name ?? ''} onClose={close} />
  </Box>;
};
export default LiveTV;

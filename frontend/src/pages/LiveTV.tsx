import React, { useMemo, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Checkbox, FormControlLabel, LinearProgress, Pagination, Stack, TextField, Typography } from '@mui/material';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import { useTVChannelCatalog, useTVChannel } from '../hooks/useTVChannels';
import { useNow } from '../hooks/useNow';
import PageHeader from '../components/layout/PageHeader';
import StatusLine from '../components/StatusLine';
import ChannelGuide from '../components/player/ChannelGuide';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';

const PAGE_SIZE = 12;

const LiveTV: React.FC = () => {
  const catalog = useTVChannelCatalog();
  const [search, setSearch] = useState('');
  const [favorites, setFavorites] = useState(false);
  const [page, setPage] = useState(1);
  const [params, setParams] = useSearchParams();
  const selectedId = Number(params.get('channel')) || 0;
  const selected = useTVChannel(selectedId);
  const now = useNow();
  const channels = useMemo(() => (catalog.data ?? []).filter((channel) => channel.is_active
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
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ mb: 2 }}>
      <TextField fullWidth label="Find a channel" type="search" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} />
      <FormControlLabel sx={{ flexShrink: 0 }} control={<Checkbox checked={favorites} onChange={(_event, checked) => { setFavorites(checked); setPage(1); }} />} label="Favorites only" />
    </Stack>
    {catalog.isLoading ? <LinearProgress aria-label="Loading channels" /> : null}
    {catalog.isError ? <Alert severity="error" action={<Button color="inherit" onClick={() => void catalog.refetch()}>Retry</Button>}>Unable to load channels.</Alert> : null}
    {!catalog.isLoading && !catalog.isError && channels.length === 0 ? <Alert severity="info">
      {search || favorites ? 'No channels match these filters.' : 'No active TV channels yet. Add a channel and attach a stream in Manage channels.'}
    </Alert> : null}
    <Box component="section" aria-label="TV channels">
      {channels.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE).map((channel) => <Box component="article" key={channel.id} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 1 }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography component="h2" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{channel.channel_number != null ? `${channel.channel_number}. ` : ''}{channel.name}</Typography>
            <Typography variant="body2" color="text.secondary">{channel.acestream_channels.length ? `${channel.acestream_channels.length} stream${channel.acestream_channels.length === 1 ? '' : 's'}` : 'No streams attached'}{channel.category ? ` · ${channel.category}` : ''}</Typography>
          </Box>
          <Button variant="contained" startIcon={<PlayArrowRounded />} disabled={!channel.acestream_channels.length}
            aria-label={`Watch ${channel.name}`} onClick={() => { const next = new URLSearchParams(params); next.set('channel', String(channel.id)); setParams(next); }}>Watch</Button>
        </Stack>
        <ChannelGuide channel={channel} now={now} compact />
      </Box>)}
    </Box>
    {pageCount > 1 ? <Pagination count={pageCount} page={currentPage} onChange={(_event, value) => setPage(value)} size="small" siblingCount={0} sx={{ my: 2 }} /> : null}
    {selectedId && selected.isLoading ? <LinearProgress aria-label="Loading selected channel" /> : null}
    {selectedId && selected.isError ? <Alert severity="error" action={<Button color="inherit" onClick={close}>Dismiss</Button>}>Unable to open this channel.</Alert> : null}
    {selected.data && selectedId && !selected.data.acestream_channels.length ? <Alert severity="info" action={<Button color="inherit" onClick={close}>Dismiss</Button>}>This channel has no streams attached.</Alert> : null}
    <ChannelPlayerDialog open={Boolean(selectedId && selected.data?.acestream_channels.length)} tvChannelId={selectedId}
      contentId={selected.data?.acestream_channels[0]?.id ?? null} title={selected.data?.name ?? ''} onClose={close} />
  </Box>;
};
export default LiveTV;

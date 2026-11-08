import { useTranslation } from 'react-i18next';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Checkbox, FormControlLabel, LinearProgress, Stack, TextField, Typography, useMediaQuery, useTheme } from '@mui/material';
import { useTVChannelCatalog, useTVChannel } from '../hooks/useTVChannels';
import { useNowNext } from '../hooks/useNowNext';
import type { AcestreamChannel } from '../services/channelService';
import type { TVChannel } from '../types/tvChannelTypes';
import ContentSection from '../components/layout/ContentSection';
import { useNow } from '../hooks/useNow';
import PageHeader from '../components/layout/PageHeader';
import StatusLine from '../components/StatusLine';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import BrowseModeToggle, { parseBrowseMode, type BrowseMode } from '../components/livetv/BrowseModeToggle';
import TVChannelList from '../components/livetv/TVChannelList';
import StreamList from '../components/livetv/StreamList';
import EventList from '../components/livetv/EventList';

const SEARCH_LABEL: Record<BrowseMode, string> = { tv: 'Find a channel', streams: 'Find a stream', events: 'Find an event' };

const LiveTV: React.FC<{ home?: boolean }> = ({ home = false }) => {
  const { t } = useTranslation();
  const canResizePlayer = useMediaQuery(useTheme().breakpoints.up('lg'));
  const [largePlayer, setLargePlayer] = useState(false);
  const viewingArea = useRef<HTMLDivElement>(null);
  const catalog = useTVChannelCatalog(undefined, 30_000);
  const nowNext = useNowNext();
  const [playingStream, setPlayingStream] = useState<AcestreamChannel | null>(null);
  const [favorites, setFavorites] = useState(false);
  const [params, setParams] = useSearchParams();
  const onlineOnly = params.get('availability') !== 'all';
  const mode = parseBrowseMode(params.get('list'));
  const search = params.get('q') ?? '';
  const selectedId = Number(params.get('channel')) || 0;
  const selected = useTVChannel(selectedId, 30_000);
  const now = useNow();
  const updateParams = (changes: Record<string, string | null>, replace = false) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => { if (value === null || value === '' || (key === 'list' && value === 'tv')) next.delete(key); else next.set(key, value); });
    setParams(next, { replace });
  };
  const channels = useMemo(() => (catalog.data ?? []).filter((channel) => channel.is_active && channel.acestream_channels.some((stream) => stream.is_active !== false && (!onlineOnly || stream.is_online === true))
    && (!favorites || channel.is_favorite)
    && `${channel.name} ${channel.category ?? ''} ${channel.channel_number ?? ''}`.toLocaleLowerCase().includes(search.toLocaleLowerCase()))
    .sort((a, b) => (a.channel_number ?? Infinity) - (b.channel_number ?? Infinity) || a.name.localeCompare(b.name)), [catalog.data, search, favorites, onlineOnly]);
  const tvNames = useMemo(() => new Map((catalog.data ?? []).map((channel) => [channel.id, channel.name])), [catalog.data]);
  const isWatching = Boolean(playingStream || (selectedId && selected.data?.acestream_channels.length));
  useEffect(() => {
    if (isWatching) viewingArea.current?.scrollIntoView?.({ block: 'start' });
  }, [isWatching, canResizePlayer]);
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const close = () => updateParams({ channel: null }, true);
  const watchChannel = (channel: TVChannel | number) => {
    setPlayingStream(null);
    updateParams({ channel: String(typeof channel === 'number' ? channel : channel.id), list: 'tv' });
  };
  const watchStream = (stream: AcestreamChannel) => { close(); setPlayingStream(stream); };

  return <Box>
    <PageHeader title={home ? t('watch') : 'Live TV'} subtitle="Choose a channel, see what’s on, and watch."
      actions={<Button component={RouterLink} to="/tv-channels" variant="outlined">Manage channels</Button>} />
    <StatusLine items={[{ label: 'Channels', value: channels.length }, { label: 'Guide times', value: timezone }]} />
    <Box ref={viewingArea} sx={{ scrollMarginTop: '76px', display: 'grid', gridTemplateColumns: { xs: 'minmax(0, 1fr)', lg: isWatching ? (largePlayer ? 'minmax(0, 2.5fr) minmax(320px, 1fr)' : 'minmax(0, 1.3fr) minmax(320px, 1fr)') : 'minmax(0, 1fr)' }, gap: 2, alignItems: 'start' }}>
      <Box sx={{ minWidth: 0, display: isWatching || selectedId ? 'block' : 'none' }}>
        <ChannelPlayerDialog inline hideUnavailableSources={onlineOnly} largePlayer={largePlayer} onTogglePlayerSize={canResizePlayer ? () => setLargePlayer((value) => !value) : undefined} open={Boolean(playingStream)} contentId={playingStream?.id ?? null} title={playingStream?.name ?? ''} onClose={() => setPlayingStream(null)} />
        {selectedId && selected.isLoading ? <LinearProgress aria-label="Loading selected channel" /> : null}
        {selectedId && selected.isError ? <Alert severity="error" action={<Button color="inherit" onClick={close}>Dismiss</Button>}>Unable to open this channel.</Alert> : null}
        {selected.data && selectedId && !selected.data.acestream_channels.length ? <Alert severity="info" action={<Button color="inherit" onClick={close}>Dismiss</Button>}>This channel has no streams attached.</Alert> : null}
        <ChannelPlayerDialog inline hideUnavailableSources={onlineOnly} largePlayer={largePlayer} onTogglePlayerSize={canResizePlayer ? () => setLargePlayer((value) => !value) : undefined} open={Boolean(selectedId && selected.data?.acestream_channels.length)} tvChannelId={selectedId}
          contentId={(selected.data?.acestream_channels.find(stream => stream.is_active !== false && stream.is_online === true) ?? selected.data?.acestream_channels.find(stream => stream.is_active !== false))?.id ?? null} title={selected.data?.name ?? ''} onClose={close} />
      </Box>
      <Box component="section" aria-label="Browse channels" tabIndex={0} sx={{ minWidth: 0, '& > section': { height: 'auto' }, ...(isWatching ? { maxHeight: { xs: '70dvh', lg: 'calc(100dvh - 92px)' }, overflowY: 'auto', overscrollBehavior: 'contain', pr: 0.5 } : {}) }}>
        <ContentSection title="Browse">
          <Stack spacing={1.5} sx={{ mb: 2 }}>
            <BrowseModeToggle value={mode} onChange={(next) => updateParams({ list: next }, true)} />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
              <TextField fullWidth label={SEARCH_LABEL[mode]} type="search" value={search} onChange={(event) => updateParams({ q: event.target.value }, true)} />
              {mode === 'tv' ? <FormControlLabel sx={{ flexShrink: 0 }} control={<Checkbox checked={favorites} onChange={(_event, checked) => setFavorites(checked)} />} label="Favorites only" /> : null}
              {mode !== 'events' ? <FormControlLabel sx={{ flexShrink: 0 }} control={<Checkbox checked={onlineOnly} onChange={(_event, checked) => updateParams({ availability: checked ? null : 'all' }, true)} />} label="Online only" /> : null}
            </Stack>
            {mode !== 'events' ? <Typography variant="body2" color="text.secondary">{onlineOnly ? 'Showing streams that passed their last check. Offline and unchecked streams stay in your library.' : 'Showing all enabled streams, including offline and unchecked ones.'} Scheduled checks continue; this list refreshes automatically.</Typography> : null}
          </Stack>
          {mode === 'tv' ? <>
            {catalog.isLoading ? <LinearProgress aria-label="Loading channels" /> : null}
            {catalog.isError ? <Alert severity="error" action={<Button color="inherit" onClick={() => void catalog.refetch()}>Retry</Button>}>Unable to load channels.</Alert> : null}
            {!catalog.isLoading && !catalog.isError && channels.length === 0 ? <Alert severity="info">
              {search || favorites ? 'No channels match these filters.' : onlineOnly ? 'No channels have an online stream yet. Show all channels to try an unchecked stream, or review stream checks in Settings → Automation.' : 'No active TV channels with streams yet. Add a channel and attach a stream in Manage channels.'}
              {onlineOnly ? <Button color="inherit" onClick={() => updateParams({ availability: 'all' }, true)}>Show all channels</Button> : null}
            </Alert> : null}
            <TVChannelList channels={channels} selectedId={selectedId} now={now} nowNext={nowNext.data} nowNextFailed={nowNext.isError} onWatch={watchChannel} />
          </> : null}
          {mode === 'streams' ? <StreamList search={search} onlineOnly={onlineOnly} tvNames={tvNames} onWatch={watchStream} /> : null}
          {mode === 'events' ? <EventList search={search} onWatchChannel={watchChannel} /> : null}
        </ContentSection>
      </Box>
    </Box>
  </Box>;
};
export default LiveTV;

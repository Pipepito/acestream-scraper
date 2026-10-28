import RecordingOverview from '../components/recordings/RecordingOverview';
import React from 'react';
import { useQueryClient } from '@tanstack/react-query';
import UpcomingEvents from '../components/overview/UpcomingEvents';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Stack, Typography } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import ActiveStreamsList from '../components/player/ActiveStreamsList';
import InventoryTotals from '../components/overview/InventoryTotals';
import NextContentUpdates from '../components/overview/NextContentUpdates';
import { useStats, useTvChannelStats } from '../hooks/useConfig';
import { useBackgroundTaskStatus } from '../hooks/useDashboard';
import { useActiveStreams } from '../hooks/usePlayer';
import { normalizeApiError } from '../services/apiErrors';

const REFRESH_MS = 30_000;

export default function TVDashboard() {
  const cache = useQueryClient();
  const stats = useStats({ refetchInterval: REFRESH_MS });
  const tvStats = useTvChannelStats({ refetchInterval: REFRESH_MS });
  const tasks = useBackgroundTaskStatus(REFRESH_MS);
  const playback = useActiveStreams();
  const playing = playback.data?.streams.filter(stream => stream.state === 'ready' || stream.state === 'streaming').length;
  const refresh = () => {
    void cache.invalidateQueries({ queryKey: ['events', 'dashboard'] });
    void stats.refetch();
    void tvStats.refetch();
    void tasks.refetch();
    void playback.refetch();
  };

  return <Box>
    <PageHeader title="TV dashboard" subtitle="Playback, upcoming events and channels." actions={<Stack direction="row" gap={1} flexWrap="wrap">
      <Button component={RouterLink} to="/events">Events</Button>
      <Button component={RouterLink} to="/live-tv" variant="contained">Watch TV</Button>
    </Stack>} />
    <StatusLine aria-label="TV dashboard summary" items={[
      { label: 'Playing', value: playback.error ? 'Unavailable' : playing ?? 'Loading…' },
      { label: 'TV channels', value: tvStats.error ? 'Unavailable' : tvStats.data?.total ?? 'Loading…' },
      { label: 'Streams', value: stats.error ? 'Unavailable' : stats.data?.channels.total ?? 'Loading…' },
    ]} action={<Button size="small" variant="outlined" onClick={refresh}>Refresh</Button>} />

    <ContentSection title="Playing through this app" description="Browser sessions and server relays. Players connected directly to an external engine are not shown.">
      {playback.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void playback.refetch()}>Retry playback</Button>}>
        Could not load current playback: {normalizeApiError(playback.error).message}
      </Alert> : !playback.data ? <Typography role="status">Loading playback…</Typography> : <ActiveStreamsList streams={playback.data.streams} />}
    </ContentSection>

    <RecordingOverview />
    <UpcomingEvents />

    <ContentSection title="Channels and streams" description="Saved inventory and the last observed stream status." actions={<Stack direction="row" gap={1} flexWrap="wrap">
      <Button component={RouterLink} to="/tv-channels">TV channels</Button>
      <Button component={RouterLink} to="/acestream-channels">Streams</Button>
      <Button component={RouterLink} to="/epg">Guide</Button>
    </Stack>}>
      <Stack spacing={2}>
        {stats.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void stats.refetch()}>Retry inventory</Button>}>Could not load streams and guide: {normalizeApiError(stats.error).message}</Alert> : !stats.data ? <Typography role="status">Loading streams and guide…</Typography> : null}
        {tvStats.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void tvStats.refetch()}>Retry channels</Button>}>Could not load TV channels: {normalizeApiError(tvStats.error).message}</Alert> : !tvStats.data ? <Typography role="status">Loading TV channels…</Typography> : null}
        {(stats.data && !stats.error) || (tvStats.data && !tvStats.error) ? <InventoryTotals stats={stats.error ? undefined : stats.data} tvStats={tvStats.error ? undefined : tvStats.data} /> : null}
        {!stats.error && stats.data?.channels.total === 0 ? <Box><Typography variant="body2">Add a source to start building your channel catalogue.</Typography><Button component={RouterLink} to="/scraper">Add sources</Button></Box> : null}
      </Stack>
    </ContentSection>

    <ContentSection title="Next updates" actions={<Button component={RouterLink} to="/system">All scheduled jobs</Button>}>
      {tasks.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void tasks.refetch()}>Retry updates</Button>}>Could not load next updates: {normalizeApiError(tasks.error).message}</Alert>
        : !tasks.data ? <Typography role="status">Loading next updates…</Typography>
        : <NextContentUpdates tasks={tasks.data} />}
    </ContentSection>
  </Box>;
}

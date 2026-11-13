import { Alert,Box,Button,Stack,Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import React,{ useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import InventoryTotals from '../components/overview/InventoryTotals';
import NextContentUpdates from '../components/overview/NextContentUpdates';
import UpcomingEvents from '../components/overview/UpcomingEvents';
import ActiveStreamsList from '../components/player/ActiveStreamsList';
import PlaylistDialog from '../components/playlist/PlaylistDialog';
import RecordingOverview from '../components/recordings/RecordingOverview';
import StatusLine from '../components/StatusLine';
import { useStats,useTvChannelStats } from '../hooks/useConfig';
import { useBackgroundTaskStatus } from '../hooks/useDashboard';
import { useActiveStreams } from '../hooks/usePlayer';
import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { getErrorMessage } from '../utils/errorUtils';

const REFRESH_MS = 30_000;

export default function TVDashboard({ embedded = false }: { embedded?: boolean }) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const stats = useStats({ refetchInterval: REFRESH_MS });
  const tvStats = useTvChannelStats({ refetchInterval: REFRESH_MS });
  const tasks = useBackgroundTaskStatus(REFRESH_MS);
  const playback = useActiveStreams();
  const [playlistOpen, setPlaylistOpen] = useState(false);
  const playing = playback.data?.streams.filter(stream => stream.state === 'ready' || stream.state === 'streaming').length;
  const refresh = () => {
    void cache.invalidateQueries({ queryKey: ['events', 'dashboard'] });
    void stats.refetch();
    void tvStats.refetch();
    void tasks.refetch();
    void playback.refetch();
  };

  return <Box>
    {!embedded ? <PageHeader title={tUi("TV dashboard")} subtitle={tUi("Playback, upcoming events and channels.")} actions={<Stack direction="row" gap={1} flexWrap="wrap">
      <Button component={RouterLink} to="/events">{tUi("Events")}</Button>
      <Button variant="outlined" onClick={() => setPlaylistOpen(true)}>{tUi("Playlist")}</Button>
      <Button component={RouterLink} to="/live-tv" variant="contained">{tUi("Watch TV")}</Button>
    </Stack>} /> : null}
    <PlaylistDialog open={playlistOpen} onClose={() => setPlaylistOpen(false)} />
    <StatusLine aria-label={tUi("TV dashboard summary")} items={[
      { label: uiText("Playing"), value: playback.error ? uiText("Unavailable") : playing ?? tUi('Loading…') },
      { label: uiText("TV channels"), value: tvStats.error ? uiText("Unavailable") : tvStats.data?.total ?? tUi('Loading…') },
      { label: uiText("Streams"), value: stats.error ? uiText("Unavailable") : stats.data?.channels.total ?? tUi('Loading…') },
    ]} action={<Button size="small" variant="outlined" onClick={refresh}>{tUi("Refresh")}</Button>} />

    <ContentSection title={tUi("Playing through this app")} description={tUi("Browser sessions and server relays. Players connected directly to an external engine are not shown.")}>
      {playback.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void playback.refetch()}>{tUi("Retry playback")}</Button>}>
        {tUi("Could not load current playback:")}{' '}{getErrorMessage(playback.error)}
      </Alert> : !playback.data ? <Typography role="status">{tUi("Loading playback…")}</Typography> : <ActiveStreamsList streams={playback.data.streams} />}
    </ContentSection>

    <RecordingOverview />
    <UpcomingEvents />

    <ContentSection title={tUi("Channels and streams")} description={tUi("Saved inventory and the last observed stream status.")} actions={<Stack direction="row" gap={1} flexWrap="wrap">
      <Button component={RouterLink} to="/tv-channels">{tUi("TV channels")}</Button>
      <Button component={RouterLink} to="/acestream-channels">{tUi("Streams")}</Button>
      <Button component={RouterLink} to="/epg">{tUi("Guide")}</Button>
    </Stack>}>
      <Stack spacing={2}>
        {stats.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void stats.refetch()}>{tUi("Retry inventory")}</Button>}>{tUi("Could not load streams and guide:")}{' '}{getErrorMessage(stats.error)}</Alert> : !stats.data ? <Typography role="status">{tUi("Loading streams and guide…")}</Typography> : null}
        {tvStats.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void tvStats.refetch()}>{tUi("Retry channels")}</Button>}>{tUi("Could not load TV channels:")}{' '}{getErrorMessage(tvStats.error)}</Alert> : !tvStats.data ? <Typography role="status">{tUi("Loading TV channels…")}</Typography> : null}
        {(stats.data && !stats.error) || (tvStats.data && !tvStats.error) ? <InventoryTotals stats={stats.error ? undefined : stats.data} tvStats={tvStats.error ? undefined : tvStats.data} /> : null}
        {!stats.error && stats.data?.channels.total === 0 ? <Box><Typography variant="body2">{tUi("Add a source to start building your channel catalogue.")}</Typography><Button component={RouterLink} to="/scraper">{tUi("Add sources")}</Button></Box> : null}
      </Stack>
    </ContentSection>

    <ContentSection title={tUi("Next updates")} actions={<Button component={RouterLink} to="/system">{tUi("All scheduled jobs")}</Button>}>
      {tasks.error ? <Alert severity="warning" action={<Button color="inherit" onClick={() => void tasks.refetch()}>{tUi("Retry updates")}</Button>}>{tUi("Could not load next updates:")}{' '}{getErrorMessage(tasks.error)}</Alert>
        : !tasks.data ? <Typography role="status">{tUi("Loading next updates…")}</Typography>
        : <NextContentUpdates tasks={tasks.data} />}
    </ContentSection>
  </Box>;
}

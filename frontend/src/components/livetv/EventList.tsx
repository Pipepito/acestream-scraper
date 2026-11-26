import { statusLabel } from '../../i18n/status';
import { uiText } from '../../i18n/text';
import { getLocale } from '../../i18n/locale';
import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, LinearProgress, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { eventService, type SportingEvent } from '../../services/eventService';
import { readEventPreferences } from '../../hooks/useDashboardEvents';

interface EventListProps {
  search: string;
  onWatchChannel: (tvChannelId: number) => void;
}

const EVENT_LIMIT = 100;

/** Today's and tomorrow's events, with the dashboard's interests and time zone, and Watch for linked broadcasters. */
const EventList: React.FC<EventListProps> = ({ search, onWatchChannel }) => {
  const tUi = useUiText();
  const [preferences] = useState(readEventPreferences);
  const hasInterests = Object.values(preferences.interests).some((names) => names?.length);
  const filters = { selection: 'agenda' as const, limit: EVENT_LIMIT, window_days: 2, search, sport: '', competition: '', source: '',
    zone: preferences.zone, upcoming: true, followed: preferences.view === 'following', archived: false, offset: 0,
    interests: preferences.view === 'interests' && hasInterests ? JSON.stringify(preferences.interests) : undefined };
  const events = useQuery({ queryKey: ['events', 'live-tv', filters], queryFn: () => eventService.list(filters), refetchInterval: 60_000 });
  if (events.isPending) return <LinearProgress aria-label={tUi("Loading events")} />;
  if (events.isError) return <Alert severity="error" action={<Button color="inherit" onClick={() => void events.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load events.")}</Alert>;
  const rows = events.data.events;
  const emptyCopy = search ? uiText("No events match this search.")
    : preferences.view === 'interests' ? uiText("No events for your selected interests today or tomorrow. Customize events on the TV dashboard.")
    : preferences.view === 'following' ? uiText("No followed events today or tomorrow.") : uiText("No events today or tomorrow.");
  const broadcasters = (event: SportingEvent) => Array.from(new Map(event.broadcasts.map((broadcast) => [broadcast.label, broadcast])).values());
  const detailsLink = (event: SportingEvent) => `/events?event=${encodeURIComponent(event.id)}&zone=${encodeURIComponent(preferences.zone)}`;
  return <Box>
    {!rows.length ? <Alert severity="info">{emptyCopy}</Alert> : rows.map((event) => <Box component="article" key={event.id} aria-label={event.title} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
      <Stack direction="row" spacing={1.5} alignItems="baseline" sx={{ minWidth: 0 }}>
        <Typography sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
          {event.starts_at ? new Date(event.starts_at).toLocaleString(getLocale(), { timeZone: preferences.zone, weekday: 'short', hour: '2-digit', minute: '2-digit' }) : tUi("Time TBC")}
        </Typography>
        <Box sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
          <Button component={RouterLink} to={detailsLink(event)} sx={{ p: 0, minHeight: 32, textAlign: 'left', justifyContent: 'flex-start', fontSize: '1rem', fontWeight: 600, color: 'text.primary' }}>{event.title}</Button>
          <Typography variant="body2" color="text.secondary">{[event.competition, event.sport].filter(Boolean).join(' · ')}{event.state && !['scheduled', 'unknown'].includes(event.state) ? tUi(" · {{value0}}", { value0: statusLabel(event.state) }) : ''}</Typography>
        </Box>
      </Stack>
      <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap" sx={{ mt: 1 }}>
        {broadcasters(event).length ? broadcasters(event).map((broadcast) => broadcast.target?.kind === 'tv'
          ? <Button key={broadcast.id} size="small" variant="outlined" aria-label={tUi("Watch {{value0}}", { value0: broadcast.label })} onClick={() => onWatchChannel(broadcast.target!.id)}>{tUi("Watch")}{' '}{broadcast.label}</Button>
          : <Button key={broadcast.id} size="small" component={RouterLink} to={detailsLink(event)} aria-label={tUi("Link {{value0}}", { value0: broadcast.label })}>{tUi("Link")}{' '}{broadcast.label}</Button>)
          : <Typography variant="body2" color="text.secondary">{tUi("Channels not announced")}</Typography>}
      </Stack>
    </Box>)}
    <Stack direction="row" spacing={2} alignItems="center" sx={{ py: 2 }}>
      <Typography variant="body2" color="text.secondary">{tUi("Showing")}{' '}{rows.length}{events.data.total > rows.length ? tUi(" of {{value0}}", { value0: events.data.total }) : ''}</Typography>
      <Button component={RouterLink} to="/events">{tUi("View all events")}</Button>
    </Stack>
  </Box>;
};

export default EventList;

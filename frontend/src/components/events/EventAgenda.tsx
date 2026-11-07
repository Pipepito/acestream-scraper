import React from 'react';
import { Box, Button, Chip, Link, Stack, Typography } from '@mui/material';
import type { SportingEvent } from '../../services/eventService';

type Broadcast = SportingEvent['broadcasts'][number];
export function EventChannelName({ broadcast }: { broadcast: Broadcast }) {
  const target = broadcast.target;
  return target ? <Link href={target.kind === 'tv' ? `./tv-channels/${target.id}` : `./epg/channels/${target.id}`} title={target.name}>{broadcast.label}</Link> : <>{broadcast.label}</>;
}

export function eventDay(event: SportingEvent, zone: string): string {
  if (!event.starts_at) return event.scheduled_date ?? '';
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date(event.starts_at));
  return ['year', 'month', 'day'].map((key) => parts.find((part) => part.type === key)?.value).join('-');
}

function dayLabel(day: string, today: string, compact = false): string {
  if (!day) return 'Date to be confirmed';
  const label = new Date(`${day}T12:00:00Z`).toLocaleDateString(undefined, { timeZone: 'UTC', weekday: compact ? 'short' : 'long', month: 'short', day: 'numeric' });
  return day === today ? `Today · ${label}` : label;
}

interface Props { events: SportingEvent[]; zone: string; today: string; onSelect: (id: string) => void }
export default function EventAgenda({ events, zone, today, onSelect }: Props) {
  const groups = new Map<string, SportingEvent[]>();
  for (const event of events) {
    const day = eventDay(event, zone);
    groups.set(day, [...(groups.get(day) ?? []), event]);
  }
  return <Stack spacing={3}>
    {Array.from(groups.entries()).sort(([a], [b]) => (a || '9999').localeCompare(b || '9999')).map(([day, rows]) => <Box component="section" key={day} aria-label={dayLabel(day, today)}>
      <Typography component="h3" variant="subtitle1" fontWeight={600} sx={{ pb: 1, borderBottom: 1, borderColor: 'divider' }}>{dayLabel(day, today)}</Typography>
      <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
        {rows.map(event => <EventAgendaRow key={event.id} event={event} zone={zone} onSelect={onSelect} />)}
      </Box>
    </Box>)}
  </Stack>;
}

export function EventAgendaRow({ event, zone, onSelect, showDate = false }: { event: SportingEvent; zone: string; onSelect: (id: string) => void; showDate?: boolean }) {
  const broadcasters = Array.from(new Map(event.broadcasts.map((broadcast) => [broadcast.label, broadcast])).values());
  return <Box component="li" sx={{ display: 'grid', gridTemplateColumns: { xs: '64px minmax(0, 1fr)', md: '80px minmax(0, 1fr) minmax(180px, 28%)' }, columnGap: 2, rowGap: 0.5, py: 2, borderBottom: 1, borderColor: 'divider' }}>
    <Typography sx={{ gridColumn: 1, gridRow: { xs: '1 / span 2', md: 1 }, pt: 0.5, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
      {showDate ? <Typography component="span" variant="caption" display="block">{dayLabel(eventDay(event, zone), '', true)}</Typography> : null}
      {event.starts_at ? new Date(event.starts_at).toLocaleTimeString(undefined, { timeZone: zone, hour: '2-digit', minute: '2-digit' }) : 'Time TBC'}
    </Typography>
    <Box sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
      <Button aria-label={`View broadcasts for ${event.title}`} sx={{ p: 0, minHeight: 32, textAlign: 'left', justifyContent: 'flex-start', fontSize: '1rem', fontWeight: 600, color: 'text.primary' }} onClick={() => onSelect(event.id)}>{event.title}</Button>
      <Typography variant="body2" color="text.secondary">{[event.competition, event.sport].filter(Boolean).join(' · ')}</Typography>
      {event.followed || !['scheduled', 'unknown'].includes(event.state ?? 'unknown') ? <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 0.5 }}>
        {!['scheduled', 'unknown'].includes(event.state ?? 'unknown') ? <Chip label={event.state === 'live' ? 'Live · reported' : event.state} size="small" variant="outlined" /> : null}
        {event.followed ? <Chip label="Following" size="small" variant="outlined" /> : null}
      </Stack> : null}
    </Box>
    <Typography component="div" variant="body2" sx={{ gridColumn: { xs: 2, md: 3 }, alignSelf: 'center', overflowWrap: 'anywhere', color: 'text.secondary' }}>
      {broadcasters.length ? <>
        <Box component="span" sx={{ mr: 0.5 }}>On</Box>
        {broadcasters.slice(0, 3).map((broadcast, index) => <React.Fragment key={broadcast.id}>{index ? ' · ' : ''}<EventChannelName broadcast={broadcast} /></React.Fragment>)}
        {broadcasters.length > 3 ? <Button size="small" onClick={() => onSelect(event.id)} aria-label={`Show all channels for ${event.title}`}>+{broadcasters.length - 3} more</Button> : null}
      </> : 'Channels not announced'}
    </Typography>
  </Box>;
}

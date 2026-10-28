import React, { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { type SportingEvent, type EventFields, type EventUpdate } from '../../services/eventService';
import { EventChannelName } from './EventAgenda';
import EventArtwork from './EventArtwork';
import EventBroadcastMapper from './EventBroadcastMapper';
import ContentSection from '../layout/ContentSection';
import { formatRelativeTime } from '../../utils/format';

interface Props { event: SportingEvent; zone: string; busy: boolean; onUpdate: (input: EventUpdate) => void; onPlay: (id: string, label: string) => void }
export default function EventDetails({ event, zone, busy, onUpdate, onPlay }: Props) {
  const [managing, setManaging] = useState(false);
  const [editing, setEditing] = useState(false);
  const [fields, setFields] = useState<EventFields>({ title: event.title, sport: event.sport, competition: event.competition, participants: event.participants, scheduled_date: event.scheduled_date, starts_at: event.starts_at, ends_at: event.ends_at, timezone: event.timezone, time_notes: event.time_notes, state: event.state });
  return <ContentSection title={event.title}>
    <Stack spacing={2}>
      <Typography variant="body2" color="text.secondary">{[event.competition, event.sport].filter(Boolean).join(' · ')}</Typography>
      <Typography fontWeight={600}>{event.starts_at ? new Date(event.starts_at).toLocaleString(undefined, { timeZone: zone, weekday: 'long', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : event.scheduled_date ? `${event.scheduled_date} · Time to be confirmed` : 'Date and time to be confirmed'}</Typography>
      <Stack direction="row" flexWrap="wrap" gap={1}>
        <Button disabled={busy} onClick={() => onUpdate({ revision: event.revision, followed: !event.followed })}>{event.followed ? 'Unfollow event' : 'Follow event'}</Button>
        <Button aria-expanded={managing} onClick={() => { setManaging(!managing); setEditing(false); }}>Manage event</Button>
      </Stack>
      {managing ? <Stack direction="row" flexWrap="wrap" gap={1}>
        <Button onClick={() => setEditing(!editing)}>{editing ? 'Cancel correction' : 'Correct schedule'}</Button>
        <Button disabled={busy} onClick={() => onUpdate({ revision: event.revision, archived: !event.archived })}>{event.archived ? 'Restore event' : 'Archive event'}</Button>
      </Stack> : null}
      {editing ? <Stack spacing={2}>
        <TextField label="Title" value={fields.title} onChange={(e) => setFields({ ...fields, title: e.target.value })} />
        <TextField select label="Event state" value={fields.state} onChange={(e) => setFields({ ...fields, state: e.target.value as EventFields['state'] })}>
          {['unknown', 'scheduled', 'live', 'finished', 'postponed', 'cancelled'].map((state) => <MenuItem key={state} value={state}>{state}</MenuItem>)}
        </TextField>
        <TextField label="Start (ISO date and time)" value={fields.starts_at ?? ''} onChange={(e) => setFields({ ...fields, starts_at: e.target.value || null })} helperText={`Include an offset, or use the source timezone ${fields.timezone}. Blank means unknown.`} />
        <TextField label="End (only if known)" value={fields.ends_at ?? ''} onChange={(e) => setFields({ ...fields, ends_at: e.target.value || null })} />
        <TextField label="Time notes" value={fields.time_notes} onChange={(e) => setFields({ ...fields, time_notes: e.target.value })} />
        <Stack direction="row" gap={1}><Button variant="contained" disabled={busy || !fields.title.trim()} onClick={() => onUpdate({ revision: event.revision, correction: fields })}>Save correction</Button>
          {event.corrected ? <Button disabled={busy} onClick={() => onUpdate({ revision: event.revision, correction: null })}>Use source schedule</Button> : null}</Stack>
      </Stack> : null}
      {event.corrected ? <Typography variant="caption" color="text.secondary">Schedule updated manually</Typography> : null}
      {event.state === 'live' ? <Alert severity="info">Live, as reported by the source.</Alert> : null}
      {event.state === 'postponed' ? <Alert severity="info">Postponed. Check the revised start time before watching.</Alert> : null}
      {event.state === 'finished' ? <Alert severity="info">This event has ended. A listed stream may now show other programming.</Alert> : null}
      {event.state === 'cancelled' ? <Alert severity="info">This event was cancelled.</Alert> : null}
      {event.epg_matches?.length ? <Stack spacing={1}>
        <Typography component="h3" variant="subtitle1" fontWeight={600}>Matching guide programmes</Typography>
        {event.epg_matches.map((match) => <Stack key={match.program_id} spacing={0.5}>
          <Typography>{match.title} · {new Date(match.starts_at).toLocaleString(undefined, { timeZone: zone })}</Typography>
          <Button component={RouterLink} to={`/epg/channels/${match.epg_channel.id}`} sx={{ alignSelf: 'flex-start' }}>{match.epg_channel.name} · {match.epg_channel.source_name}</Button>
          {match.tv_channel ? <Button component={RouterLink} to={`/tv-channels/${match.tv_channel.id}`} sx={{ alignSelf: 'flex-start' }}>Open {match.tv_channel.name}</Button> : null}
        </Stack>)}
        <Typography variant="caption">Matched by both teams and schedule time. Guide listings do not confirm live signal.</Typography>
      </Stack> : null}
      <Typography component="h3" variant="subtitle1" fontWeight={600}>Where to watch</Typography>
      {!event.broadcasts.length ? <Alert severity="info">No broadcast announced yet. You can follow this event and check back after the next import.</Alert> : null}
      {event.broadcasts.map((broadcast) => <Stack key={broadcast.id} direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ py: 1.5, borderTop: 1, borderColor: 'divider' }}>
        <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}>
          <Typography fontWeight={600}><EventChannelName broadcast={broadcast} /></Typography>
          {broadcast.target && broadcast.target.name !== broadcast.label ? <Typography variant="body2" color="text.secondary">Your channel: {broadcast.target.name}</Typography> : null}
          {managing ? <>
          <Typography variant="body2">{[broadcast.language, broadcast.quality, broadcast.country].filter(Boolean).join(' · ') || 'Language and quality not supplied'}</Typography>
          <Typography variant="body2">{broadcast.is_online === true ? 'Signal verified' : broadcast.is_online === false ? 'No signal verified' : 'Signal not checked'}{broadcast.checked_at ? ` · ${formatRelativeTime(broadcast.checked_at)}` : ''}</Typography>
          <Typography variant="body2" color="text.secondary">{broadcast.reason} · {broadcast.source_name}{broadcast.origin ? ` · ${broadcast.origin}` : ''}</Typography>
          </> : null}
          {broadcast.compatibility === 'unavailable' && !managing ? <Typography variant="body2" color="text.secondary">Channel unavailable. Choose another link below.</Typography> : null}
          {broadcast.compatibility === 'unsupported' && !managing ? <Typography variant="body2" color="text.secondary">Link a channel to watch this broadcast.</Typography> : null}
          {managing || (!broadcast.target && broadcast.compatibility !== 'playable') ? <EventBroadcastMapper event={event} broadcast={broadcast} /> : null}
        </Stack>
        {broadcast.content_id && broadcast.compatibility === 'playable' ? <Button variant="outlined" sx={{ alignSelf: { xs: 'flex-start', sm: 'center' }, flexShrink: 0 }} onClick={() => onPlay(broadcast.content_id!, broadcast.label)}>Play {broadcast.label}</Button> : null}
      </Stack>)}
      {event.time_notes ? <Box component="details">
        <Box component="summary" sx={{ cursor: 'pointer', color: 'text.secondary', py: 1 }}>Schedule notes</Box>
        <Typography variant="body2" sx={{ mt: 1 }}>{event.time_notes}</Typography>
      </Box> : null}
      {event.has_artwork ? <EventArtwork event={event} /> : null}
      {managing ? <>
        <Typography variant="subtitle2">Sources</Typography>
        {event.provenance.map((source) => <Typography key={`${source.source_id}:${source.external_id}`} variant="body2" color="text.secondary">{source.source_name} · {source.source_kind} · Updated {formatRelativeTime(source.updated_at)}</Typography>)}
        <Typography variant="caption" color="text.secondary">Following and corrections are saved for this installation. Changing streams affects only your viewer. No automatic fallback is enabled.</Typography>
      </> : null}
    </Stack>
  </ContentSection>;
}

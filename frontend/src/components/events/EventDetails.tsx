import React, { useState } from 'react';
import { Alert, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { type SportingEvent, type EventFields, type EventUpdate } from '../../services/eventService';
import EventArtwork from './EventArtwork';
import EventBroadcastMapper from './EventBroadcastMapper';
import ContentSection from '../layout/ContentSection';
import { formatRelativeTime } from '../../utils/format';

interface Props { event: SportingEvent; zone: string; busy: boolean; onUpdate: (input: EventUpdate) => void; onPlay: (id: string, label: string) => void }
export default function EventDetails({ event, zone, busy, onUpdate, onPlay }: Props) {
  const [editing, setEditing] = useState(false);
  const [fields, setFields] = useState<EventFields>({ title: event.title, sport: event.sport, competition: event.competition, participants: event.participants, starts_at: event.starts_at, ends_at: event.ends_at, timezone: event.timezone, time_notes: event.time_notes, state: event.state });
  return <ContentSection title={event.title}>
    <Stack spacing={2}>
      <Stack direction="row" flexWrap="wrap" gap={1}>
        <Button disabled={busy} onClick={() => onUpdate({ revision: event.revision, followed: !event.followed })}>{event.followed ? 'Unfollow event' : 'Follow event'}</Button>
        <Button onClick={() => setEditing(!editing)}>{editing ? 'Cancel correction' : 'Correct schedule'}</Button>
        <Button disabled={busy} onClick={() => onUpdate({ revision: event.revision, archived: !event.archived })}>{event.archived ? 'Restore event' : 'Archive event'}</Button>
      </Stack>
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
      {event.has_artwork ? <EventArtwork event={event} /> : null}
      <Typography>{event.starts_at ? new Date(event.starts_at).toLocaleString(undefined, { timeZone: zone }) : 'Start time unknown'} · {event.state}{event.corrected ? ' · Manually corrected' : ''}</Typography>
      {event.time_notes ? <Typography variant="body2">{event.time_notes}</Typography> : null}
      {event.state === 'postponed' ? <Alert severity="info">Postponed. Check the revised start time before watching.</Alert> : null}
      {event.state === 'finished' ? <Alert severity="info">This event has ended. A listed stream may now show other programming.</Alert> : null}
      {event.state === 'cancelled' ? <Alert severity="info">This event was cancelled.</Alert> : null}
      {!event.broadcasts.length ? <Alert severity="info">No broadcast announced yet. You can follow this event and check back after the next import.</Alert> : null}
      {event.broadcasts.map((broadcast) => <Stack key={broadcast.id} direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ py: 1.5, borderTop: 1, borderColor: 'divider' }}>
        <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}>
          <Typography fontWeight={600}>{broadcast.label}</Typography>
          <Typography variant="body2">{[broadcast.language, broadcast.quality, broadcast.country].filter(Boolean).join(' · ') || 'Language and quality not supplied'}</Typography>
          <Typography variant="body2">{broadcast.is_online === true ? 'Signal verified' : broadcast.is_online === false ? 'No signal verified' : 'Signal not checked'}{broadcast.checked_at ? ` · ${formatRelativeTime(broadcast.checked_at)}` : ''}</Typography>
          <Typography variant="body2" color="text.secondary">{broadcast.reason} · {broadcast.source_name}{broadcast.origin ? ` · ${broadcast.origin}` : ''}</Typography>
          <EventBroadcastMapper event={event} broadcast={broadcast} />
        </Stack>
        {broadcast.content_id && broadcast.compatibility === 'playable' ? <Button variant="outlined" sx={{ alignSelf: { xs: 'flex-start', sm: 'center' }, flexShrink: 0 }} onClick={() => onPlay(broadcast.content_id!, broadcast.label)}>Play {broadcast.label}</Button> : <Typography variant="body2">{broadcast.compatibility}</Typography>}
      </Stack>)}
      <Typography variant="subtitle2">Sources</Typography>
      {event.provenance.map((source) => <Typography key={`${source.source_id}:${source.external_id}`} variant="body2" color="text.secondary">{source.source_name} · {source.source_kind} · Updated {formatRelativeTime(source.updated_at)}</Typography>)}
      <Typography variant="caption" color="text.secondary">Following and corrections are saved for this installation. Changing streams affects only your viewer. No automatic fallback is enabled.</Typography>
    </Stack>
  </ContentSection>;
}

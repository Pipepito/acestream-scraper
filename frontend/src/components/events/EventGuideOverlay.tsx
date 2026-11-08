import { useUiText } from '../../i18n/useUiText';
import React, { useRef, useState } from 'react';
import { Alert, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { eventService, type SportingEvent, type EventOverlayRequest } from '../../services/eventService';
import { eventErrorMessage } from './eventErrors';
import { useUnsavedChanges } from '../UnsavedChanges';

export default function EventGuideOverlay({ event }: { event: SportingEvent }) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const [broadcastId, setBroadcastId] = useState('');
  const [end, setEnd] = useState(event.ends_at ?? '');
  const [baseline, setBaseline] = useState(() => JSON.stringify(['', event.ends_at ?? '']));
  const pending = useRef(false);
  const [reviewed, setReviewed] = useState<EventOverlayRequest | null>(null);
  const overlays = useQuery({ queryKey: ['events', event.id, 'guide-overlays'], queryFn: () => eventService.overlays(event.id) });
  const input: EventOverlayRequest = { revision: event.revision, broadcast_id: broadcastId, ends_at: end };
  const preview = useMutation({ mutationFn: () => eventService.previewOverlay(event.id, input), onSuccess: () => setReviewed(input) });
  const invalidate = () => { void cache.invalidateQueries({ queryKey: ['events'] }); void cache.invalidateQueries({ queryKey: ['epg'] }); };
  const apply = useMutation({ mutationFn: () => eventService.applyOverlay(event.id, reviewed!, preview.data!.fingerprint), onSuccess: () => { setBaseline(JSON.stringify([broadcastId, end])); setReviewed(null); preview.reset(); invalidate(); } });
  const remove = useMutation({ mutationFn: (id: string) => eventService.removeOverlay(event.id, event.revision, id), onSuccess: invalidate });
  const busy = preview.isPending || apply.isPending || remove.isPending;
  useUnsavedChanges(JSON.stringify([broadcastId, end]) !== baseline, busy);
  const run = async (operation: () => Promise<unknown>) => {
    if (pending.current) return;
    pending.current = true;
    try { await operation(); } catch { /* Keep draft and render the mutation error. */ }
    finally { pending.current = false; }
  };
  const eligible = Boolean(event.starts_at) && !event.archived && !['cancelled', 'postponed'].includes(event.state ?? '');
  const current = reviewed?.broadcast_id === broadcastId && reviewed?.ends_at === end && reviewed?.revision === event.revision;
  const error = preview.error ?? apply.error ?? remove.error;
  return <Stack spacing={2}>
    <Typography component="h3" variant="subtitle1" fontWeight={600}>{tUi("XMLTV guide overlay")}</Typography>
    <Typography variant="body2">{tUi("Place this event over its channel’s exported guide. Regular programmes remain before and after it. The original guide and built-in recording schedule stay unchanged.")}</Typography>
    {overlays.isError ? <Alert severity="error" action={<Button onClick={() => void overlays.refetch()}>{tUi("Retry")}</Button>}>{tUi("Could not load overlays.")}</Alert> : null}
    {overlays.data?.map((overlay) => <Stack key={overlay.broadcast_id} spacing={1}>
      <Typography>{overlay.channel.name} · {overlay.programme.starts_at} – {overlay.programme.ends_at}</Typography>
      <Typography variant="body2">{overlay.active ? tUi("Active in XMLTV exports") : tUi("Suspended: schedule or channel changed. Preview again to replace it.")}</Typography>
      <Button disabled={busy} onClick={() => void run(() => remove.mutateAsync(overlay.broadcast_id))}>{tUi("Remove overlay for")}{' '}{overlay.channel.name}</Button>
    </Stack>)}
    {!eligible ? <Alert severity="info">{tUi("A confirmed start and an unarchived event are required. Cancelled and postponed events cannot overlay a guide.")}</Alert> : <>
      <TextField select label={tUi("Overlay broadcast")} value={broadcastId} disabled={busy} onChange={(e) => setBroadcastId(e.target.value)}>
        {event.broadcasts.filter((b) => b.target).map((b) => <MenuItem key={b.id} value={b.id}>{b.label} → {b.target?.name}</MenuItem>)}
      </TextField>
      <TextField label={tUi("Overlay end (ISO date and time)")} value={end} disabled={busy} onChange={(e) => setEnd(e.target.value)}
        helperText={tUi("Confirm an end with a UTC offset, for example 2026-10-30T23:00:00+01:00. Maximum 12 hours; this does not change the event’s reported end.")} />
      <Button disabled={busy || !broadcastId || !end.trim()} onClick={() => void run(() => preview.mutateAsync())}>{tUi("Preview guide overlay")}</Button>
    </>}
    {JSON.stringify([broadcastId, end]) !== baseline ? <Button disabled={busy} onClick={() => { const [savedBroadcast, savedEnd] = JSON.parse(baseline) as [string, string]; setBroadcastId(savedBroadcast); setEnd(savedEnd); setReviewed(null); preview.reset(); apply.reset(); }}>{tUi('Cancel')}</Button> : null}
    {apply.isSuccess ? <Alert severity="success">{tUi('Guide overlay saved.')}</Alert> : null}
    {error ? <Alert severity="error">{eventErrorMessage(error)}</Alert> : null}
    {preview.data && current ? <Stack spacing={1}>
      <Typography fontWeight={600}>{preview.data.channel.name}: {preview.data.programme.title}</Typography>
      <Typography>{preview.data.programme.starts_at} – {preview.data.programme.ends_at}</Typography>
      <Typography variant="body2">{preview.data.affected.length ? tUi("These regular listings will be clipped around the event window:") : tUi("There are no regular listings in this window.")}</Typography>
      {preview.data.affected.map((p, index) => <Typography variant="body2" key={`${p.starts_at}:${index}`}>{p.title} · {p.starts_at} – {p.ends_at}</Typography>)}
      <Button variant="contained" disabled={busy} onClick={() => void run(() => apply.mutateAsync())}>{tUi("Apply reviewed overlay")}</Button>
    </Stack> : null}
  </Stack>;
}

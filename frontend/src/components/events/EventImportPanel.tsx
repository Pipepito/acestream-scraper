import React, { useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { eventService, type EventImport, type EventPreview } from '../../services/eventService';
import { getErrorMessage } from '../../utils/errorUtils';

interface Props { zone: string; onClose: () => void }
export default function EventImportPanel({ zone, onClose }: Props) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState('manual');
  const [title, setTitle] = useState('');
  const [start, setStart] = useState('');
  const [sport, setSport] = useState('');
  const [competition, setCompetition] = useState('');
  const [url, setUrl] = useState('');
  const [label, setLabel] = useState('');
  const [raw, setRaw] = useState('');
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<EventPreview | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [identity] = useState(() => crypto.randomUUID());
  const review = useMutation({ mutationFn: (input: EventImport) => eventService.preview(input),
    onSuccess: (result) => { setPreview(result); setSelected([]); setError(''); },
    onError: (err) => setError(getErrorMessage(err)) });
  const save = useMutation({ mutationFn: () => eventService.apply(preview!.token, selected),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['events'] }); onClose(); },
    onError: (err) => setError(getErrorMessage(err)) });
  const busy = review.isPending || save.isPending;
  const submit = () => {
    setError('');
    try {
      const input: EventImport = mode === 'json' ? JSON.parse(raw) as EventImport : { version: 1, observations: [{
        source_id: 'manual', source_name: 'Manual events', source_kind: 'manual', external_id: identity,
        title, timezone: zone, starts_at: start || null, sport, competition, state: start ? 'scheduled' : 'unknown',
        broadcasts: label || url ? [{ id: 'primary', label: label || 'Event stream', url: url || null }] : [],
      }] };
      review.mutate(input);
    } catch { setError('This is not valid JSON. Choose an event schedule file or correct the pasted text.'); }
  };
  return <ContentSection title="Add events">
    {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
    {preview ? <Stack spacing={2}>
      <Typography>Review the schedule, then select the events to save. Times shown in {zone}.</Typography>
      {preview.warnings.map((warning) => <Typography key={warning} variant="body2" color="text.secondary">{warning}</Typography>)}
      {preview.events.map((event) => <Box key={event.id} sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
        <FormControlLabel control={<Checkbox checked={selected.includes(event.id)} disabled={busy}
          onChange={(_, checked) => setSelected((ids) => checked ? [...ids, event.id] : ids.filter((id) => id !== event.id))} />}
          label={`${event.title} · ${event.state}`} />
        <Typography variant="body2">{event.starts_at ? new Date(event.starts_at).toLocaleString(undefined, { timeZone: zone }) : 'Start time unknown'} · {event.broadcasts.length} broadcast options</Typography>
        {event.broadcasts.map((broadcast) => <Typography variant="body2" key={broadcast.id}>{broadcast.label} · {broadcast.compatibility} · {broadcast.language} {broadcast.quality}</Typography>)}
        {event.corrected ? <Typography variant="body2">Manual correction will be kept.</Typography> : null}
      </Box>)}
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <Button variant="contained" disabled={!selected.length || busy} onClick={() => save.mutate()}>Save selected ({selected.length})</Button>
        <Button disabled={busy} onClick={() => setPreview(null)}>Back to input</Button>
        <Button disabled={busy} onClick={onClose}>Cancel</Button>
      </Stack>
    </Stack> : <Stack spacing={2}>
      <TextField select label="Add from" value={mode} onChange={(e) => setMode(e.target.value)} disabled={busy}>
        <MenuItem value="manual">Create an event</MenuItem><MenuItem value="json">Import event schedule JSON</MenuItem>
      </TextField>
      {mode === 'manual' ? <>
        <TextField required label="Event title" value={title} onChange={(e) => setTitle(e.target.value)} inputProps={{ maxLength: 300 }} />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField fullWidth label="Sport" value={sport} onChange={(e) => setSport(e.target.value)} />
          <TextField fullWidth label="Competition" value={competition} onChange={(e) => setCompetition(e.target.value)} />
        </Stack>
        <TextField label="Scheduled start" type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} InputLabelProps={{ shrink: true }} helperText={`${zone}. Leave blank if unknown. Repeated DST times require an explicit offset in JSON.`} />
        <TextField label="Broadcaster" value={label} onChange={(e) => setLabel(e.target.value)} helperText="Optional. A name alone stays unresolved until a stream is provided." />
        <TextField label="Stream URL" value={url} onChange={(e) => setUrl(e.target.value)} helperText="Optional AceStream, HLS (.m3u8) or MPEG-TS (.ts) link. Website links are kept as unsupported." />
      </> : <>
        <Typography variant="body2">Use the version 1 event schedule format documented in the Sports events guide. Raw W3U lists and Telegram messages need their own adapters.</Typography>
        <Button component="label" variant="outlined">Choose schedule file<input type="file" accept=".json,application/json" hidden onChange={(e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          if (file.size > 2 * 1024 * 1024) { setError('Choose a file smaller than 2 MiB.'); return; }
          void file.text().then(setRaw).catch(() => setError('Could not read this file.'));
        }} /></Button>
        <TextField multiline minRows={6} maxRows={12} label="Event schedule JSON" value={raw} onChange={(e) => setRaw(e.target.value)} inputProps={{ maxLength: 2 * 1024 * 1024 }} />
      </>}
      <Stack direction="row" spacing={1}>
        <Button variant="contained" disabled={busy || (mode === 'manual' ? !title.trim() : !raw.trim())} onClick={submit}>{review.isPending ? 'Preparing preview…' : 'Preview events'}</Button>
        <Button disabled={busy} onClick={onClose}>Cancel</Button>
      </Stack>
    </Stack>}
  </ContentSection>;
}

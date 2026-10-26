import React, { useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import EventProviderFields from './EventProviderFields';
import EventInterestFields, { emptyInterests } from './EventInterestFields';
import ContentSection from '../layout/ContentSection';
import { eventService, type EventImport, type EventPreview, type EventSource, type EventProviderOptions } from '../../services/eventService';
import { catalogueService } from '../../services/catalogueService';
import { eventErrorMessage as getErrorMessage } from './eventErrors';

interface Props { zone: string; onClose: () => void; source?: EventSource;
  catalogue?: { id: number; revision: number; entryIds: string[]; title: string } }

function createEventIdentity(): string {
  // getRandomValues also works over LAN HTTP, where randomUUID is unavailable.
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export default function EventImportPanel({ zone, onClose, source, catalogue }: Props) {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState(source?.provider_options ? 'provider' : source ? 'url' : catalogue ? 'manual' : 'provider');
  const year = new Date().getFullYear() - (new Date().getMonth() < 6 ? 1 : 0);
  const [provider, setProvider] = useState<EventProviderOptions>(source?.provider_options ?? { provider: 'wosti_es', feeds: ['all', 'automovilismo'], season: `${year}-${String(year + 1).slice(-2)}`, league: 'es.1', window_days: 14, interests: emptyInterests });
  const [title, setTitle] = useState(catalogue?.title ?? '');
  const [start, setStart] = useState('');
  const [sport, setSport] = useState('');
  const [competition, setCompetition] = useState('');
  const [format, setFormat] = useState<'event_import' | 'schema_org'>(source?.format ?? 'event_import');
  const [sourceZone, setSourceZone] = useState(source?.timezone ?? 'Europe/Madrid');
  const [scheduleUrl, setScheduleUrl] = useState('');
  const [refreshSource, setRefreshSource] = useState(source?.enabled ?? false);
  const [url, setUrl] = useState('');
  const [label, setLabel] = useState('');
  const [raw, setRaw] = useState('');
  const [error, setError] = useState('');
  const [reviewedProvider, setReviewedProvider] = useState('');
  const [preview, setPreview] = useState<EventPreview | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [identity] = useState(createEventIdentity);
  const review = useMutation({ mutationFn: (input: EventImport) => catalogue ? catalogueService.previewEvent(catalogue.id, {
      revision: catalogue.revision, entry_ids: catalogue.entryIds, title, timezone: sourceZone,
      starts_at: start || null, sport, competition, state: start ? 'scheduled' : 'unknown',
    }) : eventService.preview(input),
    onSuccess: (result) => { setPreview(result); setSelected([]); setError(''); },
    onError: (err) => setError(getErrorMessage(err)) });
  const reviewSource = useMutation({ mutationFn: () => eventService.previewSource(mode === 'provider' ? { source_id: source?.id, provider_options: provider, timezone: sourceZone } : source ? { source_id: source.id } : { url: scheduleUrl, format, timezone: sourceZone }),
    onSuccess: (result) => { setPreview(result); setSelected([]); setError(''); setReviewedProvider(JSON.stringify(provider)); },
    onError: (err) => setError(getErrorMessage(err)) });
  const save = useMutation({ mutationFn: () => (mode === 'url' || mode === 'provider') ? eventService.apply(preview!.token, selected, refreshSource) : eventService.apply(preview!.token, selected),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['events'] }); void queryClient.invalidateQueries({ queryKey: ['catalogue'] }); onClose(); },
    onError: (err) => setError(getErrorMessage(err)) });
  const previewStale = mode === 'provider' && reviewedProvider !== JSON.stringify(provider);
  const busy = review.isPending || reviewSource.isPending || save.isPending;
  const submit = () => {
    setError('');
    if (mode === 'url' || mode === 'provider') { reviewSource.mutate(); return; }
    try {
      if (mode === 'json' && new TextEncoder().encode(raw).length > 2 * 1024 * 1024) { setError('Choose a schedule smaller than 2 MiB.'); return; }
      const input: EventImport = mode === 'json' ? JSON.parse(raw) as EventImport : { version: 1, observations: [{
        source_id: 'manual', source_name: 'Manual events', source_kind: 'manual', external_id: identity,
        title, timezone: zone, starts_at: start || null, sport, competition, state: start ? 'scheduled' : 'unknown',
        broadcasts: label || url ? [{ id: 'primary', label: label || 'Event stream', url: url || null }] : [],
      }] };
      if (!input || input.version !== 1 || !Array.isArray(input.observations) || !input.observations.length) { setError('Use a version 1 event schedule with an observations array. For OpenFootball, choose Built-in provider.'); return; }
      review.mutate(input);
    } catch { setError('This is not valid JSON. Choose an event schedule file or correct the pasted text.'); }
  };
  return <ContentSection title="Add events">
    {error ? <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-line', overflowWrap: 'anywhere' }}>{error}</Alert> : null}
    {preview ? <Stack spacing={2}>
      <Typography>Review the schedule, then select the events to save. Times shown in {zone}.</Typography>
      {preview.warnings.map((warning) => <Typography key={warning} variant="body2" color="text.secondary">{warning}</Typography>)}
      {mode === 'provider' ? <>
        <EventInterestFields prefix="Import: " value={provider.interests ?? emptyInterests} choices={preview.available_interests} disabled={busy} onChange={(interests) => setProvider({ ...provider, interests })} />
        <Button disabled={busy} onClick={() => reviewSource.mutate()}>Update preview with interests</Button>
        <Typography variant="caption">Update the preview after changing interests before saving.</Typography>
      </> : null}
      {!preview.events.length ? <Alert severity="info">No matching events are published in this window. Change your interests or save the source to review later.</Alert> : <FormControlLabel control={<Checkbox disabled={busy} checked={selected.length === preview.events.length} indeterminate={selected.length > 0 && selected.length < preview.events.length} onChange={(_, checked) => setSelected(checked ? preview.events.map((event) => event.id) : [])} />} label="Select all shown events" />}
      <Box sx={{ maxHeight: 480, overflowY: 'auto' }}>
      {preview.events.map((event) => <Box key={event.id} sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
        <FormControlLabel control={<Checkbox checked={selected.includes(event.id)} disabled={busy}
          onChange={(_, checked) => setSelected((ids) => checked ? [...ids, event.id] : ids.filter((id) => id !== event.id))} />}
          label={`${event.title} · ${event.state}`} />
        <Typography variant="body2">{event.starts_at ? new Date(event.starts_at).toLocaleString(undefined, { timeZone: zone }) : event.scheduled_date ? `${event.scheduled_date} · Time unknown` : 'Start time unknown'} · {event.broadcasts.length} broadcast options</Typography>
        {event.broadcasts.map((broadcast) => <Typography variant="body2" key={broadcast.id}>{broadcast.label} · {broadcast.compatibility} · {broadcast.language} {broadcast.quality}</Typography>)}
        {event.corrected ? <Typography variant="body2">Manual correction will be kept.</Typography> : null}
      </Box>)}
      </Box>
      {mode === 'url' || mode === 'provider' ? <FormControlLabel control={<Checkbox checked={refreshSource} disabled={busy} onChange={(_, checked) => setRefreshSource(checked)} />} label="Refresh selected events automatically with scheduled scraping" /> : null}
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <Button variant="contained" disabled={(!selected.length && mode !== 'provider') || busy || previewStale} onClick={() => save.mutate()}>{mode === 'provider' && !selected.length ? 'Save source without events' : `Save selected (${selected.length})`}</Button>
        <Button disabled={busy} onClick={() => setPreview(null)}>Back to input</Button>
        <Button disabled={busy} onClick={onClose}>Cancel</Button>
      </Stack>
    </Stack> : <Stack spacing={2}>
      {!catalogue ? <TextField select label="Add from" value={mode} onChange={(e) => setMode(e.target.value)} disabled={busy || Boolean(source) || Boolean(catalogue)}>
        <MenuItem value="provider">Built-in provider</MenuItem><MenuItem value="manual">Create an event</MenuItem><MenuItem value="json">Import event schedule JSON</MenuItem><MenuItem value="url">Load schedule URL</MenuItem>
      </TextField> : null}
      {mode === 'provider' ? <EventProviderFields value={provider} onChange={setProvider} zone={sourceZone} onZone={setSourceZone} saved={Boolean(source)} disabled={busy} /> : mode === 'manual' ? <>
        <TextField required label="Event title" value={title} onChange={(e) => setTitle(e.target.value)} inputProps={{ maxLength: 300 }} />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField fullWidth label="Sport" value={sport} onChange={(e) => setSport(e.target.value)} />
          <TextField fullWidth label="Competition" value={competition} onChange={(e) => setCompetition(e.target.value)} />
        </Stack>
        <TextField label="Scheduled start" type={catalogue ? 'text' : 'datetime-local'} value={start} onChange={(e) => setStart(e.target.value)} InputLabelProps={{ shrink: true }} helperText={catalogue ? `${sourceZone}. Enter date and time, e.g. 2026-10-25T02:30:00+02:00. Include an offset for repeated DST times; leave blank if unknown.` : `${zone}. Leave blank if unknown. Repeated DST times require an explicit offset in JSON.`} />
        {catalogue ? <>
          <TextField label="Source timezone" value={sourceZone} onChange={(e) => setSourceZone(e.target.value)} helperText="Use the publisher’s IANA timezone. Start time is not inferred from the title." />
          <Typography variant="body2">The selected catalogue source becomes an event broadcast. Its private URL and headers stay on the server. Refresh the catalogue and review this entry again to update it; scheduled catalogue refresh does not change events.</Typography>
        </> : <>
        <TextField label="Broadcaster" value={label} onChange={(e) => setLabel(e.target.value)} helperText="Optional. A name alone stays unresolved until a stream is provided." />
        <TextField label="Stream URL" value={url} onChange={(e) => setUrl(e.target.value)} helperText="Optional AceStream, HLS (.m3u8) or MPEG-TS (.ts) link. Website links are kept as unsupported." />
        </>}
      </> : mode === 'url' ? <>
        {source ? <Typography>Review {source.name} · {source.origin}</Typography> : <TextField label="Schedule URL" value={scheduleUrl} onChange={(e) => setScheduleUrl(e.target.value)} inputProps={{ maxLength: 4096 }} />}
        {!source ? <>
          <TextField select label="Guide format" value={format} onChange={(e) => setFormat(e.target.value as typeof format)}>
            <MenuItem value="event_import">Event schedule JSON (version 1)</MenuItem><MenuItem value="schema_org">Structured sports guide (JSON or HTML JSON-LD)</MenuItem>
          </TextField>
          {format === 'schema_org' ? <TextField label="Source timezone" value={sourceZone} onChange={(e) => setSourceZone(e.target.value)} helperText="IANA timezone used by this guide for times without an offset. Check the source; do not assume your display timezone." /> : null}
        </> : null}
        <Typography variant="body2">Structured guides need SportsEvent records with stable IDs and explicit dates. Pages without this metadata and Telegram messages need adapters. Open raw W3U lists in Catalogues and use Add as event. Preview fetches the guide without saving it.</Typography>
      </> : <>
        <Typography variant="body2">Use the version 1 event schedule format documented in the Sports events guide. Open raw W3U lists in Catalogues and use Add as event. Telegram messages need an adapter.</Typography>
        <Button component="label" variant="outlined">Choose schedule file<input type="file" accept=".json,application/json" hidden onChange={(e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          if (file.size > 2 * 1024 * 1024) { setError('Choose a file smaller than 2 MiB.'); return; }
          void file.text().then(setRaw).catch(() => setError('Could not read this file.'));
        }} /></Button>
        <TextField multiline minRows={6} maxRows={12} label="Event schedule JSON" value={raw} onChange={(e) => setRaw(e.target.value)} inputProps={{ maxLength: 2 * 1024 * 1024 }} />
      </>}
      <Stack direction="row" spacing={1}>
        <Button variant="contained" disabled={busy || (mode === 'manual' ? !title.trim() : mode === 'url' ? !source && !scheduleUrl.trim() : mode === 'provider' ? provider.provider === 'wosti_es' && !provider.feeds?.length : !raw.trim())} onClick={submit}>{review.isPending || reviewSource.isPending ? 'Preparing preview…' : 'Preview events'}</Button>
        <Button disabled={busy} onClick={onClose}>Cancel</Button>
      </Stack>
    </Stack>}
  </ContentSection>;
}

import { Alert,Box,Button,Checkbox,FormControlLabel,MenuItem,Stack,TextField,Typography } from '@mui/material';
import { useMutation,useQueryClient } from '@tanstack/react-query';
import React,{ useRef,useState } from 'react';
import { getLocale } from '../../i18n/locale';
import { statusLabel } from '../../i18n/status';
import { useUiText } from '../../i18n/useUiText';
import { catalogueService } from '../../services/catalogueService';
import { eventService,type EventImport,type EventPreview,type EventProviderOptions,type EventSource } from '../../services/eventService';
import { useConfirm } from '../ConfirmDialog';
import ContentSection from '../layout/ContentSection';
import { useUnsavedChanges } from '../UnsavedChanges';
import { eventErrorMessage as getErrorMessage } from './eventErrors';
import EventInterestFields,{ emptyInterests } from './EventInterestFields';
import EventProviderFields from './EventProviderFields';

interface Props { zone: string; onClose: () => void; source?: EventSource;
  catalogue?: { id: number; revision: number; entryIds: string[]; title: string } }

function createEventIdentity(): string {
  // getRandomValues also works over LAN HTTP, where randomUUID is unavailable.
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export default function EventImportPanel({ zone, onClose, source, catalogue }: Props) {
  const tUi = useUiText();
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
  const [timeoutSeconds, setTimeoutSeconds] = useState(String(source?.timeout_seconds ?? 15));
  const validTimeout = /^\d+$/.test(timeoutSeconds) && Number(timeoutSeconds) >= 5 && Number(timeoutSeconds) <= 300;
  const [scheduleUrl, setScheduleUrl] = useState('');
  const [refreshSource, setRefreshSource] = useState(source?.enabled ?? false);
  const [url, setUrl] = useState('');
  const [label, setLabel] = useState('');
  const [raw, setRaw] = useState('');
  const [failure, setFailure] = useState<{ remote: unknown } | { local: () => string } | null>(null);
  const error = failure ? 'remote' in failure ? getErrorMessage(failure.remote) : failure.local() : '';
  const action = useRef(false);
  const { confirm, dialog } = useConfirm();
  const [reviewedProvider, setReviewedProvider] = useState('');
  const [preview, setPreview] = useState<EventPreview | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [identity] = useState(createEventIdentity);
  const review = useMutation({ mutationFn: (input: EventImport) => catalogue ? catalogueService.previewEvent(catalogue.id, {
      revision: catalogue.revision, entry_ids: catalogue.entryIds, title, timezone: sourceZone,
      starts_at: start || null, sport, competition, state: start ? 'scheduled' : 'unknown',
    }) : eventService.preview(input),
    onSuccess: (result) => { setPreview(result); setSelected([]); setFailure(null); },
    onError: (err) => setFailure({ remote: err }), onSettled: () => { action.current = false; } });
  const reviewSource = useMutation({ mutationFn: () => eventService.previewSource({ timeout_seconds: Number(timeoutSeconds), ...(mode === 'provider' ? { source_id: source?.id, provider_options: provider, timezone: sourceZone } : source ? { source_id: source.id } : { url: scheduleUrl, format, timezone: sourceZone }) }),
    onSuccess: (result) => { setPreview(result); setSelected([]); setFailure(null); setReviewedProvider(JSON.stringify(provider)); },
    onError: (err) => setFailure({ remote: err }), onSettled: () => { action.current = false; } });
  const save = useMutation({ mutationFn: () => (mode === 'url' || mode === 'provider') ? eventService.apply(preview!.token, selected, refreshSource) : eventService.apply(preview!.token, selected),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['events'] }); void queryClient.invalidateQueries({ queryKey: ['catalogue'] }); onClose(); },
    onError: (err) => setFailure({ remote: err }), onSettled: () => { action.current = false; } });
  const previewStale = mode === 'provider' && reviewedProvider !== JSON.stringify(provider);
  const busy = review.isPending || reviewSource.isPending || save.isPending;
  const draft = JSON.stringify({ mode, provider, title, start, sport, competition, format, sourceZone, timeoutSeconds, scheduleUrl, refreshSource, url, label, raw });
  const initialDraft = useRef(draft);
  const dirty = draft !== initialDraft.current || Boolean(preview);
  useUnsavedChanges(dirty, busy);
  const close = async () => {
    if (action.current || busy) return;
    if (dirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onClose();
  };
  const run = (operation: () => void) => {
    if (action.current) return;
    action.current = true;
    operation();
  };
  const submit = () => {
    if (action.current) return;
    setFailure(null);
    if (mode === 'url' || mode === 'provider') { run(() => reviewSource.mutate()); return; }
    try {
      if (mode === 'json' && new TextEncoder().encode(raw).length > 2 * 1024 * 1024) { setFailure({ local: () => tUi("Choose a schedule smaller than 2 MiB.") }); return; }
      const input: EventImport = mode === 'json' ? JSON.parse(raw) as EventImport : { version: 1, observations: [{
        source_id: 'manual', source_name: 'Manual events', source_kind: 'manual', external_id: identity,
        title, timezone: zone, starts_at: start || null, sport, competition, state: start ? 'scheduled' : 'unknown',
        broadcasts: label || url ? [{ id: 'primary', label: label || 'Event stream', url: url || null }] : [],
      }] };
      if (!input || input.version !== 1 || !Array.isArray(input.observations) || !input.observations.length) { setFailure({ local: () => tUi("Use a version 1 event schedule with an observations array. For OpenFootball, choose Built-in provider.") }); return; }
      run(() => review.mutate(input));
    } catch { setFailure({ local: () => tUi("This is not valid JSON. Choose an event schedule file or correct the pasted text.") }); }
  };
  return <ContentSection title={tUi("Add events")}>
    {dialog}
    <Box component="fieldset" disabled={busy} sx={{ border: 0, p: 0, m: 0, minWidth: 0 }}>
    {error ? <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-line', overflowWrap: 'anywhere' }}>{error}</Alert> : null}
    {preview ? <Stack spacing={2}>
      <Typography>{tUi("Review the schedule, then select the events to save. Times shown in")}{' '}{zone}.</Typography>
      {preview.warnings.map((warning) => <Typography key={warning} variant="body2" color="text.secondary">{warning}</Typography>)}
      {mode === 'provider' ? <>
        <EventInterestFields prefix="Import: " value={provider.interests ?? emptyInterests} choices={preview.available_interests} disabled={busy} onChange={(interests) => setProvider({ ...provider, interests })} />
        <Button disabled={busy} onClick={() => run(() => reviewSource.mutate())}>{tUi("Update preview with interests")}</Button>
        <Typography variant="caption">{tUi("Update the preview after changing interests before saving.")}</Typography>
      </> : null}
      {!preview.events.length ? <Alert severity="info">{tUi("No matching events are published in this window. Change your interests or save the source to review later.")}</Alert> : <FormControlLabel control={<Checkbox disabled={busy} checked={selected.length === preview.events.length} indeterminate={selected.length > 0 && selected.length < preview.events.length} onChange={(_, checked) => setSelected(checked ? preview.events.map((event) => event.id) : [])} />} label={tUi("Select all shown events")} />}
      <Box sx={{ maxHeight: 480, overflowY: 'auto' }}>
      {preview.events.map((event) => <Box key={event.id} sx={{ borderBottom: 1, borderColor: 'divider', pb: 1 }}>
        <FormControlLabel control={<Checkbox checked={selected.includes(event.id)} disabled={busy}
          onChange={(_, checked) => setSelected((ids) => checked ? [...ids, event.id] : ids.filter((id) => id !== event.id))} />}
          label={tUi("{{value0}} · {{value1}}", { value0: event.title, value1: statusLabel(event.state) })} />
        <Typography variant="body2">{event.starts_at ? new Date(event.starts_at).toLocaleString(getLocale(), { timeZone: zone }) : event.scheduled_date ? tUi("{{value0}} · Time unknown", { value0: event.scheduled_date }) : tUi("Start time unknown")} · {event.broadcasts.length} {' '}{tUi("broadcast options")}</Typography>
        {event.broadcasts.map((broadcast) => <Typography variant="body2" key={broadcast.id}>{broadcast.label} · {broadcast.compatibility} · {broadcast.language} {broadcast.quality}</Typography>)}
        {event.corrected ? <Typography variant="body2">{tUi("Manual correction will be kept.")}</Typography> : null}
      </Box>)}
      </Box>
      {mode === 'url' || mode === 'provider' ? <FormControlLabel control={<Checkbox checked={refreshSource} disabled={busy} onChange={(_, checked) => setRefreshSource(checked)} />} label={tUi("Refresh selected events automatically with scheduled scraping")} /> : null}
      <Stack direction="row" spacing={1} flexWrap="wrap">
        <Button variant="contained" disabled={(!selected.length && mode !== 'provider') || busy || previewStale} onClick={() => run(() => save.mutate())}>{mode === 'provider' && !selected.length ? tUi("Save source without events") : tUi("Save selected ({{value0}})", { value0: selected.length })}</Button>
        <Button disabled={busy} onClick={() => setPreview(null)}>{tUi("Back to input")}</Button>
        <Button disabled={busy} onClick={() => void close()}>{tUi("Cancel")}</Button>
      </Stack>
    </Stack> : <Stack spacing={2}>
      {!catalogue ? <TextField select label={tUi("Add from")} value={mode} onChange={(e) => setMode(e.target.value)} disabled={busy || Boolean(source) || Boolean(catalogue)}>
        <MenuItem value="provider">{tUi("Built-in provider")}</MenuItem><MenuItem value="manual">{tUi("Create an event")}</MenuItem><MenuItem value="json">{tUi("Import event schedule JSON")}</MenuItem><MenuItem value="url">{tUi("Load schedule URL")}</MenuItem>
      </TextField> : null}
      {mode === 'provider' ? <EventProviderFields value={provider} onChange={setProvider} zone={sourceZone} onZone={setSourceZone} saved={Boolean(source)} disabled={busy} /> : mode === 'manual' ? <>
        <TextField required label={tUi("Event title")} value={title} onChange={(e) => setTitle(e.target.value)} inputProps={{ maxLength: 300 }} />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField fullWidth label={tUi("Sport")} value={sport} onChange={(e) => setSport(e.target.value)} />
          <TextField fullWidth label={tUi("Competition")} value={competition} onChange={(e) => setCompetition(e.target.value)} />
        </Stack>
        <TextField label={tUi("Scheduled start")} type={catalogue ? 'text' : 'datetime-local'} value={start} onChange={(e) => setStart(e.target.value)} InputLabelProps={{ shrink: true }} helperText={catalogue ? tUi("{{value0}}. Enter date and time, e.g. 2026-10-25T02:30:00+02:00. Include an offset for repeated DST times; leave blank if unknown.", { value0: sourceZone }) : tUi("{{value0}}. Leave blank if unknown. Repeated DST times require an explicit offset in JSON.", { value0: zone })} />
        {catalogue ? <>
          <TextField label={tUi("Source timezone")} value={sourceZone} onChange={(e) => setSourceZone(e.target.value)} helperText={tUi("Use the publisher’s IANA timezone. Start time is not inferred from the title.")} />
          <Typography variant="body2">{tUi("The selected catalogue source becomes an event broadcast. Its private URL and headers stay on the server. Refresh the catalogue and review this entry again to update it; scheduled catalogue refresh does not change events.")}</Typography>
        </> : <>
        <TextField label={tUi("Broadcaster")} value={label} onChange={(e) => setLabel(e.target.value)} helperText={tUi("Optional. A name alone stays unresolved until a stream is provided.")} />
        <TextField label={tUi("Stream URL")} value={url} onChange={(e) => setUrl(e.target.value)} helperText={tUi("Optional AceStream, HLS (.m3u8) or MPEG-TS (.ts) link. Website links are kept as unsupported.")} />
        </>}
      </> : mode === 'url' ? <>
        {source ? <Typography>{tUi("Review")}{' '}{source.name} · {source.origin}</Typography> : <TextField label={tUi("Schedule URL")} value={scheduleUrl} onChange={(e) => setScheduleUrl(e.target.value)} inputProps={{ maxLength: 4096 }} />}
        {!source ? <>
          <TextField select label={tUi("Guide format")} value={format} onChange={(e) => setFormat(e.target.value as typeof format)}>
            <MenuItem value="event_import">{tUi("Event schedule JSON (version 1)")}</MenuItem><MenuItem value="schema_org">{tUi("Structured sports guide (JSON or HTML JSON-LD)")}</MenuItem>
          </TextField>
          {format === 'schema_org' ? <TextField label={tUi("Source timezone")} value={sourceZone} onChange={(e) => setSourceZone(e.target.value)} helperText={tUi("IANA timezone used by this guide for times without an offset. Check the source; do not assume your display timezone.")} /> : null}
        </> : null}
        <Typography variant="body2">{tUi("Structured guides need SportsEvent records with stable IDs and explicit dates. Pages without this metadata and Telegram messages need adapters. Open raw W3U lists in Scraper → W3U catalogues and use Add as event. Preview fetches the guide without saving it.")}</Typography>
      </> : <>
        <Typography variant="body2">{tUi("Use the version 1 event schedule format documented in the Sports events guide. Open raw W3U lists in Scraper → W3U catalogues and use Add as event. Telegram messages need an adapter.")}</Typography>
        <Button component="label" variant="outlined">{tUi("Choose schedule file")}<input type="file" accept=".json,application/json" hidden onChange={(e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          if (file.size > 2 * 1024 * 1024) { setFailure({ local: () => tUi("Choose a file smaller than 2 MiB.") }); return; }
          void file.text().then(setRaw).catch(() => setFailure({ local: () => tUi("Could not read this file.") }));
        }} /></Button>
        <TextField multiline minRows={6} maxRows={12} label={tUi("Event schedule JSON")} value={raw} onChange={(e) => setRaw(e.target.value)} inputProps={{ maxLength: 2 * 1024 * 1024 }} />
      </>}
      {mode === 'provider' || mode === 'url' ? <TextField label={tUi("Request timeout (seconds)")} type="number" value={timeoutSeconds}
        disabled={busy} onChange={(e) => setTimeoutSeconds(e.target.value)} inputProps={{ min: 5, max: 300 }} error={!validTimeout}
        helperText={tUi("5–300 seconds for the complete source request. Saved for previews and automatic refresh.")} /> : null}
      <Stack direction="row" spacing={1}>
        <Button variant="contained" disabled={busy || ((mode === 'provider' || mode === 'url') && !validTimeout) || (mode === 'manual' ? !title.trim() : mode === 'url' ? !source && !scheduleUrl.trim() : mode === 'provider' ? provider.provider === 'wosti_es' && !provider.feeds?.length : !raw.trim())} onClick={submit}>{review.isPending || reviewSource.isPending ? tUi("Preparing preview…") : tUi("Preview events")}</Button>
        <Button disabled={busy} onClick={() => void close()}>{tUi("Cancel")}</Button>
      </Stack>
    </Stack>}
    </Box>
  </ContentSection>;
}

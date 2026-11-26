import { statusLabel } from '../i18n/status';
import { uiText } from '../i18n/text';
import { getLocale } from '../i18n/locale';
import { useUiText } from '../i18n/useUiText';
import RecordingSettingsFields from '../components/recordings/RecordingSettingsFields';
import RecordingPlayback from '../components/recordings/RecordingPlayback';
import React, { useRef, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, LinearProgress, MenuItem, Pagination, Stack, Tab, Tabs, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import { useConfirm } from '../components/ConfirmDialog';
import RecordingDialog from '../components/recordings/RecordingDialog';
import { recordingService, recordingFileUrl, type Recording, type RecordingFile, type RecordingCollection } from '../services/recordingService';
import { getErrorMessage } from '../utils/errorUtils';
const activeStates = ['starting', 'recording', 'recovering', 'finalizing'];
const Recordings: React.FC = () => {
  const tUi = useUiText();
  const [params, setParams] = useSearchParams();
  const settingsOpen = params.get('tab') === 'settings';
  const collection: RecordingCollection = ['library', 'upcoming', 'history'].includes(params.get('view') ?? '') ? params.get('view') as RecordingCollection : 'library';
  const page = Math.max(1, Math.floor(Math.min(1000000, Number(params.get('page')) || 1)));
  const search = params.get('q') ?? '';
  const navigate = (updates: Record<string, string | null>, replace = false) => {
    const next = new URLSearchParams(params);
    Object.entries(updates).forEach(([key, value]) => { if (value) next.set(key, value); else next.delete(key); });
    setParams(next, { replace });
  };
  const availableStates = collection === 'upcoming' ? ['scheduled', ...activeStates] : collection === 'history'
    ? ['completed', 'partial', 'failed', 'missed', 'cancelled', 'deleting', 'deleted'] : ['completed', 'partial', 'failed'];
  const state = availableStates.includes(params.get('state') ?? '') ? params.get('state') ?? '' : '';

  const [editing, setEditing] = useState<Recording | null>(null);
  const [playing, setPlaying] = useState<{ row: Recording; file: RecordingFile } | null>(null);
  const queries = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const list = useQuery({ queryKey: ['recordings', 'list', collection, state, page, search], queryFn: () => recordingService.list(state, (page-1)*50, search, collection),
    refetchInterval: (query) => query.state.data?.items.some((row) => activeStates.includes(row.state)) ? 2000 : 30000 });
  const capabilities = useQuery({ queryKey: ['recordings', 'capabilities'], queryFn: recordingService.capabilities });
  const changing = useRef(false);
  const change = useMutation({ mutationFn: (fn: () => Promise<unknown>) => fn(), onSuccess: () => { void queries.invalidateQueries({ queryKey: ['recordings'] }); }, onSettled: () => { changing.current = false; } });
  const execute = (action: () => Promise<unknown>) => {
    if (changing.current) return;
    changing.current = true;
    change.mutate(action);
  };
  const stop = async (row: Recording) => {
    if (await confirm(() => ({ title: tUi('Stop recording?'), body: tUi('Stop “{{title}}” now? The captured part remains available if finalization succeeds.', { title: row.snapshot.title }),
      confirmLabel: tUi('Stop recording'), danger: true }))) execute(() => recordingService.stop(row.id));
  };
  const cancel = async (row: Recording) => {
    if (await confirm(() => ({ title: tUi('Cancel scheduled recording?'), body: tUi('“{{title}}” will not be recorded. This does not delete saved files.', { title: row.snapshot.title }),
      confirmLabel: tUi('Cancel recording'), danger: true }))) execute(() => recordingService.cancel(row.id));
  };
  const remove = async (row: Recording) => {
    if (await confirm(() => ({ title: uiText("Delete recording?"), body: tUi('Delete every saved part of “{{title}}”? This cannot be undone.', { title: row.snapshot.title }), confirmLabel: uiText("Delete files"), danger: true }))) execute(() => recordingService.delete(row.id));
  };
  const prepare = async (row: Recording, file: RecordingFile, profile: 'remux' | 'aac') => {
    if (await confirm(() => ({ title: profile === 'aac' ? tUi('Prepare browser audio?') : tUi('Prepare an MP4 copy?'),
      body: profile === 'aac' ? tUi('Create an MP4 copy with AAC audio for this part. The original and its video remain unchanged. Preparation waits while recording is active.')
        : tUi('Create an MP4 copy of this part without re-encoding. The original remains available. Preparation waits while recording is active.'),
      confirmLabel: profile === 'aac' ? tUi('Prepare browser audio') : tUi('Prepare MP4') }))) execute(() => recordingService.convert(row.id, file.id, profile));
  };
  const protect = async (row: Recording) => {
    if (row.protected && !await confirm(() => ({ title: tUi('Remove recording protection?'),
      body: tUi('“{{title}}” can then be deleted manually or by automatic retention. Its files are not deleted now.', { title: row.snapshot.title }), confirmLabel: tUi('Remove protection'), danger: true }))) return;
    execute(() => recordingService.edit(row.id, { expected_revision: row.revision, protected: !row.protected }));
  };
  const preparing = (row: Recording, file: RecordingFile, profile: string) => (row.files ?? []).some(candidate => candidate.source_artifact_id === file.id && candidate.profile === profile && candidate.state !== 'failed');
  const fileLabel = (row: Recording, file: RecordingFile) => {
    const originals = (row.files ?? []).filter(candidate => candidate.kind === 'original');
    const part = originals.findIndex(candidate => candidate.id === (file.kind === 'original' ? file.id : file.source_artifact_id)) + 1;
    return file.kind === 'original' ? tUi('Original · part {{part}}', { part }) : part ? tUi('MP4 · part {{part}}', { part }) : tUi('MP4');
  };
  return <Box>
    <PageHeader title={tUi("Recordings")} subtitle={tUi("Scheduled programmes and saved recordings.")} actions={<Button component={RouterLink} to={{ pathname: '/recordings', search: (() => { const next = new URLSearchParams(params); next.set('tab', 'settings'); return next.toString(); })() }} variant="outlined">{tUi("Recording settings")}</Button>} />
    <Dialog open={settingsOpen} onClose={() => { const next = new URLSearchParams(params); next.delete('tab'); setParams(next); }} fullWidth maxWidth="sm" aria-labelledby="recording-settings-title">
      <DialogTitle id="recording-settings-title">{tUi("Recording settings")}</DialogTitle>
      <DialogContent>{settingsOpen ? <RecordingSettingsFields /> : null}<Button onClick={() => { const next = new URLSearchParams(params); next.delete('tab'); setParams(next); }}>{tUi("Close")}</Button></DialogContent>
    </Dialog>
    <StatusLine items={[{ label: uiText("Recordings"), value: list.data?.total ?? '—' }, { label: uiText("Capture"), value: capabilities.data ? capabilities.data.enabled ? uiText("Enabled") : uiText("Disabled") : '—' }]} />
    {capabilities.data && !capabilities.data.available ? <Alert severity="info" sx={{ mb: 2 }}>{!capabilities.data.enabled ? tUi('Recordings are disabled. Enable them in Recording settings when storage is ready.') : !capabilities.data.storage_ready ? tUi('Recording storage is unavailable. Configure a persistent recording directory and check its permissions.') : !capabilities.data.stream_copy ? tUi('FFmpeg and ffprobe are required to capture recordings.') : tUi('Recording capture is unavailable. Check Recording settings.')}</Alert> : null}
    {capabilities.isError ? <Alert severity="warning">{tUi("Recording availability could not be checked. Saved recordings are still listed below.")}</Alert> : null}
    <Tabs value={collection} onChange={(_, view: string) => navigate({ view, state: null, page: null })} variant="fullWidth" aria-label={tUi('Recording collections')} sx={{ mb: 2 }}>
      <Tab value="library" label={tUi('Library')} /><Tab value="upcoming" label={tUi('Upcoming and active')} /><Tab value="history" label={tUi('History')} />
    </Tabs>
    <ContentSection title={collection === 'library' ? tUi('Saved recordings') : collection === 'upcoming' ? tUi('Upcoming and active') : tUi("Recording history")} description={tUi("Record from Live TV or schedule a programme from its guide. Guide updates never move saved times.")}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <TextField fullWidth label={tUi("Search recordings")} value={search} onChange={(e) => navigate({ q: e.target.value, page: null }, true)} />
        <TextField select label={tUi("Status")} SelectProps={{ displayEmpty: true }} InputLabelProps={{ shrink: true }} value={state} sx={{ minWidth: 180 }} onChange={(e) => navigate({ state: e.target.value, page: null })}><MenuItem value="">{tUi("All recordings")}</MenuItem>{availableStates.map((item) => <MenuItem key={item} value={item}>{statusLabel(item)}</MenuItem>)}</TextField>
      </Stack>
      {list.isLoading ? <LinearProgress aria-label={tUi("Loading recordings")} /> : null}
      {list.isError ? <Alert severity="error" action={<Button onClick={() => void list.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load recordings.")}</Alert> : null}
      {change.isError ? <Alert severity="error">{getErrorMessage(change.error)}</Alert> : null}
      {list.data?.items.length === 0 ? <Typography color="text.secondary">{search || state ? tUi('No recordings match these filters.') : collection === 'library' ? tUi('No saved recordings yet. Record now from Watch or schedule a programme from its guide. Active captures appear in Upcoming and active.') : collection === 'upcoming' ? tUi('No upcoming or active recordings. Schedule a programme from its guide or record a channel now.') : tUi('No recording history yet. Completed, failed, cancelled and deleted recordings appear here.')}</Typography> : null}
      {list.data?.items.map((row) => <Box component="article" key={row.id} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap><Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{row.snapshot.title}</Typography><Chip label={statusLabel(row.state)} size="small" />{row.protected ? <Chip label={tUi("Protected")} size="small" variant="outlined" /> : null}</Stack>
        <Typography>{row.snapshot.channel_name} · {new Date(row.start_time).toLocaleString(getLocale())} – {new Date(row.end_time).toLocaleString(getLocale())}</Typography>
        <Typography variant="body2" color="text.secondary">{tUi("Scheduled timezone:")}{' '}{row.timezone}{row.actual_start ? tUi(" · First media: {{value0}}", { value0: new Date(row.actual_start).toLocaleString(getLocale()) }) : ''}{row.actual_end ? tUi(" · Finished: {{value0}}", { value0: new Date(row.actual_end).toLocaleString(getLocale()) }) : ''}</Typography>
        {row.reason ? <Typography variant="body2">{statusLabel(row.reason)}</Typography> : null}
        {row.gaps.map((gap, i) => <Typography key={i} variant="body2" color="warning.main">{tUi("Missing interval:")}{' '}{new Date(gap.start).toLocaleTimeString(getLocale())} – {new Date(gap.end).toLocaleTimeString(getLocale())} · {statusLabel(gap.reason)}</Typography>)}
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ my: 1 }}>
          {row.state === 'scheduled' || activeStates.includes(row.state) ? <Button disabled={change.isPending} onClick={() => setEditing(row)}>{tUi("Edit times")}</Button> : null}
          {row.state === 'scheduled' ? <Button disabled={change.isPending} onClick={() => void cancel(row)}>{tUi("Cancel recording")}</Button> : null}
          {['starting', 'recording', 'recovering'].includes(row.state) ? <Button color="error" disabled={change.isPending} onClick={() => void stop(row)}>{tUi("Stop recording")}</Button> : null}
          {row.state !== 'deleted' && row.state !== 'deleting' ? <Button disabled={change.isPending} onClick={() => void protect(row)}>{row.protected ? tUi("Remove protection") : tUi("Protect")}</Button> : null}
          {!activeStates.includes(row.state) && row.state !== 'scheduled' && row.state !== 'deleted' && row.state !== 'deleting' ? <Button color="error" disabled={row.protected || change.isPending} onClick={() => void remove(row)}>{tUi("Delete")}</Button> : null}
        </Stack>
        {(row.files ?? []).map((file) => <Stack direction="row" alignItems="center" flexWrap="wrap" useFlexGap spacing={1} key={file.id} sx={{ mt: 1 }}>
          <Typography variant="body2">{fileLabel(row, file)} · {statusLabel(file.state)} · {(file.bytes/1024**2).toLocaleString(getLocale(), { maximumFractionDigits: 1 })} {' '}{tUi("MiB")}{file.reason ? tUi(" · {{value0}}", { value0: statusLabel(file.reason) }) : ''}</Typography>
          {file.state === 'ready' && row.state !== 'deleted' && row.state !== 'deleting' ? <><Button component="a" href={recordingFileUrl(row.id, file.id, true)} referrerPolicy="no-referrer">{tUi("Download")}</Button>
            <Button disabled={activeStates.includes(row.state)} onClick={() => setPlaying({ row, file })}>{tUi("Play")}</Button>
            {file.kind === 'original' ? <><Button disabled={change.isPending || activeStates.includes(row.state) || preparing(row, file, 'remux') || capabilities.data?.mp4_remux === false} onClick={() => void prepare(row, file, 'remux')}>{tUi("Prepare MP4")}</Button><Button disabled={change.isPending || activeStates.includes(row.state) || preparing(row, file, 'aac') || capabilities.data?.aac_conversion === false} onClick={() => void prepare(row, file, 'aac')}>{tUi("Prepare browser audio")}</Button></> : null}
          </> : null}
        </Stack>)}
      </Box>)}
      {(list.data?.total ?? 0) > 50 ? <Pagination page={page} count={Math.ceil((list.data?.total ?? 0)/50)} onChange={(_, value) => navigate({ page: value === 1 ? null : String(value) })} sx={{ mt: 2 }} /> : null}
    </ContentSection>
    {editing ? <RecordingDialog channelId={editing.tv_channel_id ?? 0} channelName={editing.snapshot.channel_name} recording={editing} onClose={() => setEditing(null)} /> : null}
    <Dialog open={Boolean(playing)} onClose={() => setPlaying(null)} fullWidth maxWidth="md" aria-labelledby="recording-playback-title"><DialogTitle id="recording-playback-title">{playing?.row.snapshot.title}<Button onClick={() => setPlaying(null)} sx={{ float: 'right' }}>{tUi("Close")}</Button></DialogTitle><DialogContent>
      {playing ? <RecordingPlayback key={`${playing.row.id}:${playing.file.id}`} recordingId={playing.row.id} fileId={playing.file.id} /> : null}
    </DialogContent></Dialog>
    {dialog}
  </Box>;
};
export default Recordings;

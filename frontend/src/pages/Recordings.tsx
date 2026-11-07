import RecordingPlayback from '../components/recordings/RecordingPlayback';
import React, { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, LinearProgress, MenuItem, Pagination, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import { useConfirm } from '../components/ConfirmDialog';
import RecordingDialog from '../components/recordings/RecordingDialog';
import { recordingService, recordingFileUrl, type Recording, type RecordingFile } from '../services/recordingService';
import { getErrorMessage } from '../utils/errorUtils';
const activeStates = ['starting', 'recording', 'recovering', 'finalizing'];
const Recordings: React.FC = () => {
  const [state, setState] = useState('');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<Recording | null>(null);
  const [playing, setPlaying] = useState<{ row: Recording; file: RecordingFile } | null>(null);
  const queries = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const list = useQuery({ queryKey: ['recordings', 'list', state, page, search], queryFn: () => recordingService.list(state, (page-1)*50, search),
    refetchInterval: (query) => query.state.data?.items.some((row) => activeStates.includes(row.state)) ? 2000 : 30000 });
  const capabilities = useQuery({ queryKey: ['recordings', 'capabilities'], queryFn: recordingService.capabilities });
  const change = useMutation({ mutationFn: (fn: () => Promise<unknown>) => fn(), onSuccess: () => { void queries.invalidateQueries({ queryKey: ['recordings'] }); } });
  const remove = async (row: Recording) => {
    if (await confirm({ title: 'Delete recording?', body: `Delete every saved part of “${row.snapshot.title}”? This cannot be undone.`, confirmLabel: 'Delete files', danger: true })) change.mutate(() => recordingService.delete(row.id));
  };
  return <Box>
    <PageHeader title="Recordings" subtitle="Scheduled programmes and saved recordings." actions={<Button component={RouterLink} to="/settings?tab=automation" variant="outlined">Recording settings</Button>} />
    <StatusLine items={[{ label: 'Recordings', value: list.data?.total ?? '—' }, { label: 'Capture', value: capabilities.data?.enabled ? 'Enabled' : 'Disabled' }]} />
    {capabilities.data && !capabilities.data.available ? <Alert severity="info" sx={{ mb: 2 }}>Recordings are {capabilities.data.enabled ? 'unavailable' : 'disabled'}. {capabilities.data.message}</Alert> : null}
    <ContentSection title="Recording history" description="Record from Live TV or schedule a programme from its guide. Guide updates never move saved times.">
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <TextField fullWidth label="Search recordings" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        <TextField select label="Status" SelectProps={{ displayEmpty: true }} InputLabelProps={{ shrink: true }} value={state} sx={{ minWidth: 180 }} onChange={(e) => { setState(e.target.value); setPage(1); }}><MenuItem value="">All recordings</MenuItem>{['scheduled', ...activeStates, 'completed', 'partial', 'failed', 'missed', 'cancelled', 'deleting', 'deleted'].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}</TextField>
      </Stack>
      {list.isLoading ? <LinearProgress aria-label="Loading recordings" /> : null}
      {list.isError ? <Alert severity="error" action={<Button onClick={() => void list.refetch()}>Retry</Button>}>Unable to load recordings.</Alert> : null}
      {change.isError ? <Alert severity="error">{getErrorMessage(change.error)}</Alert> : null}
      {list.data?.items.length === 0 ? <Typography color="text.secondary">No recordings match. Choose Record now in Live TV or Schedule recording in a programme guide.</Typography> : null}
      {list.data?.items.map((row) => <Box component="article" key={row.id} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap><Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{row.snapshot.title}</Typography><Chip label={row.state} size="small" />{row.protected ? <Chip label="Protected" size="small" variant="outlined" /> : null}</Stack>
        <Typography>{row.snapshot.channel_name} · {new Date(row.start_time).toLocaleString()} – {new Date(row.end_time).toLocaleString()}</Typography>
        <Typography variant="body2" color="text.secondary">Scheduled timezone: {row.timezone}{row.actual_start ? ` · First media: ${new Date(row.actual_start).toLocaleString()}` : ''}{row.actual_end ? ` · Finished: ${new Date(row.actual_end).toLocaleString()}` : ''}</Typography>
        {row.reason ? <Typography variant="body2">{row.reason.replaceAll('_', ' ')}</Typography> : null}
        {row.gaps.map((gap, i) => <Typography key={i} variant="body2" color="warning.main">Missing interval: {new Date(gap.start).toLocaleTimeString()} – {new Date(gap.end).toLocaleTimeString()} · {gap.reason.replaceAll('_', ' ')}</Typography>)}
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ my: 1 }}>
          {row.state === 'scheduled' || activeStates.includes(row.state) ? <Button disabled={change.isPending} onClick={() => setEditing(row)}>Edit times</Button> : null}
          {row.state === 'scheduled' ? <Button disabled={change.isPending} onClick={() => change.mutate(() => recordingService.cancel(row.id))}>Cancel recording</Button> : null}
          {activeStates.includes(row.state) ? <Button color="error" disabled={change.isPending} onClick={() => change.mutate(() => recordingService.stop(row.id))}>Stop recording</Button> : null}
          {row.state !== 'deleted' && row.state !== 'deleting' ? <Button disabled={change.isPending} onClick={() => change.mutate(() => recordingService.edit(row.id, { expected_revision: row.revision, protected: !row.protected }))}>{row.protected ? 'Remove protection' : 'Protect'}</Button> : null}
          {!activeStates.includes(row.state) && row.state !== 'scheduled' && row.state !== 'deleted' ? <Button color="error" disabled={row.protected || change.isPending} onClick={() => void remove(row)}>Delete</Button> : null}
        </Stack>
        {(row.files ?? []).map((file, index) => <Stack direction="row" alignItems="center" flexWrap="wrap" useFlexGap spacing={1} key={file.id} sx={{ mt: 1 }}>
          <Typography variant="body2">{file.kind === 'original' ? 'Original' : 'MP4'} {index+1} · {file.state} · {(file.bytes/1024**2).toFixed(1)} MiB{file.reason ? ` · ${file.reason.replaceAll('_', ' ')}` : ''}</Typography>
          {file.state === 'ready' ? <><Button component="a" href={recordingFileUrl(row.id, file.id, true)} referrerPolicy="no-referrer">Download</Button>
            <Button disabled={activeStates.includes(row.state)} onClick={() => setPlaying({ row, file })}>Play</Button>
            {file.kind === 'original' ? <><Button disabled={change.isPending || activeStates.includes(row.state)} onClick={() => change.mutate(() => recordingService.convert(row.id, file.id, 'remux'))}>Prepare MP4</Button><Button disabled={change.isPending || activeStates.includes(row.state)} onClick={() => change.mutate(() => recordingService.convert(row.id, file.id, 'aac'))}>Prepare browser audio</Button></> : null}
          </> : null}
        </Stack>)}
      </Box>)}
      {(list.data?.total ?? 0) > 50 ? <Pagination page={page} count={Math.ceil((list.data?.total ?? 0)/50)} onChange={(_, value) => setPage(value)} sx={{ mt: 2 }} /> : null}
    </ContentSection>
    {editing ? <RecordingDialog channelId={editing.tv_channel_id ?? 0} channelName={editing.snapshot.channel_name} recording={editing} onClose={() => setEditing(null)} /> : null}
    <Dialog open={Boolean(playing)} onClose={() => setPlaying(null)} fullWidth maxWidth="md" aria-labelledby="recording-playback-title"><DialogTitle id="recording-playback-title">{playing?.row.snapshot.title}<Button onClick={() => setPlaying(null)} sx={{ float: 'right' }}>Close</Button></DialogTitle><DialogContent>
      {playing ? <RecordingPlayback key={`${playing.row.id}:${playing.file.id}`} recordingId={playing.row.id} fileId={playing.file.id} /> : null}
    </DialogContent></Dialog>
    {dialog}
  </Box>;
};
export default Recordings;

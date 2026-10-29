import React, { useMemo, useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { recordingService, type Recording, type RecordingCreate } from '../../services/recordingService';
import type { EPGProgram } from '../../services/epgService';
import { localRecordingTime, recordingTimeChoices } from '../../utils/recordingTimes';
import { getErrorMessage } from '../../utils/errorUtils';

interface Props { channelId: number; channelName: string; programme?: EPGProgram; recording?: Recording; onClose: () => void }
const RecordingDialog: React.FC<Props> = ({ channelId, channelName, programme, recording, onClose }) => {
  const initialZone = recording?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
  const [zone, setZone] = useState(initialZone);
  const [start, setStart] = useState(() => localRecordingTime(new Date(recording?.start_time ?? programme?.start_time ?? Date.now()), initialZone));
  const [end, setEnd] = useState(() => localRecordingTime(new Date(recording?.end_time ?? programme?.end_time ?? Date.now() + 3600_000), initialZone));
  const [startChoice, setStartChoice] = useState('');
  const [endChoice, setEndChoice] = useState('');
  const [requestStart] = useState(() => new Date().toISOString());
  const [key] = useState(() => crypto.randomUUID());
  const starts = useMemo(() => recordingTimeChoices(start, zone), [start, zone]);
  const ends = useMemo(() => recordingTimeChoices(end, zone), [end, zone]);
  const startInstant = starts.length === 1 ? starts[0] : starts.includes(startChoice) ? startChoice : '';
  const endInstant = ends.length === 1 ? ends[0] : ends.includes(endChoice) ? endChoice : '';
  const active = recording && recording.state !== 'scheduled';
  const now = !recording && (!programme || Date.parse(programme.start_time) <= Date.now());
  const queries = useQueryClient();
  const save = useMutation({ mutationFn: async () => {
    if (recording) return recordingService.edit(recording.id, { expected_revision: recording.revision, ...(!active ? { start_time: startInstant } : {}), end_time: endInstant });
    const selection: RecordingCreate['programme'] = programme ? { id: programme.id, epg_channel_id: programme.epg_channel_id, title: programme.title,
      start_time: programme.start_time, end_time: programme.end_time, subtitle: programme.subtitle, description: programme.description, category: programme.category } : undefined;
    return recordingService.create({ tv_channel_id: channelId, mode: now ? 'now' : 'schedule', start_time: now ? requestStart : startInstant,
      end_time: endInstant, timezone: zone, idempotency_key: key, programme: selection });
  }, onSuccess: () => { void queries.invalidateQueries({ queryKey: ['recordings'] }); onClose(); } });
  const minutes = endInstant && (startInstant || now) ? Math.round((Date.parse(endInstant) - (now ? Date.now() : Date.parse(startInstant))) / 60000) : 0;
  return <Dialog open onClose={save.isPending ? undefined : onClose} fullWidth maxWidth="sm" aria-labelledby="recording-title">
    <DialogTitle id="recording-title">{recording ? 'Edit recording' : now ? 'Record now' : 'Schedule recording'}</DialogTitle>
    <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      <Typography fontWeight={600}>{programme?.title ?? recording?.snapshot.title ?? channelName}</Typography>
      <Typography color="text.secondary">{channelName} · Uses the channel’s available streams, which may differ from the stream you’re watching.</Typography>
      <TextField label="Timezone" value={zone} onChange={(e) => setZone(e.target.value)} disabled={Boolean(recording)} />
      <TextField label="Start" type="datetime-local" value={start} InputLabelProps={{ shrink: true }} disabled={Boolean(active || now)} onChange={(e) => setStart(e.target.value)} />
      {!now && starts.length > 1 ? <TextField select label="Start occurs twice — choose an instant" value={startChoice} onChange={(e) => setStartChoice(e.target.value)}>{starts.map((value) => <MenuItem key={value} value={value}>{value} (UTC)</MenuItem>)}</TextField> : null}
      <TextField label="End" type="datetime-local" value={end} InputLabelProps={{ shrink: true }} onChange={(e) => setEnd(e.target.value)} />
      {ends.length > 1 ? <TextField select label="End occurs twice — choose an instant" value={endChoice} onChange={(e) => setEndChoice(e.target.value)}>{ends.map((value) => <MenuItem key={value} value={value}>{value} (UTC)</MenuItem>)}</TextField> : null}
      {!ends.length || (!now && !starts.length) ? <Alert severity="warning">This time does not exist in the chosen timezone, or the timezone is invalid.</Alert> : null}
      {minutes > 0 ? <Typography variant="body2">{minutes} minutes · Estimated {((minutes * 60 * 3_000_000) / 1024**3).toFixed(1)} GiB with headroom. Actual size depends on the stream.</Typography> : null}
      <Typography variant="body2" color="text.secondary">Start early to allow for source startup. Guide changes won’t move this recording.</Typography>
      {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    </Stack></DialogContent>
    <DialogActions><Button onClick={onClose} disabled={save.isPending}>Cancel</Button><Button variant="contained" disabled={save.isPending || !endInstant || (!now && !startInstant) || minutes <= 0 || minutes > 720} onClick={() => save.mutate()}>{save.isPending ? 'Saving…' : recording ? 'Save times' : now ? 'Record now' : 'Schedule'}</Button></DialogActions>
  </Dialog>;
};
export default RecordingDialog;

import { getLocale } from '../../i18n/locale';
import { useUiText } from '../../i18n/useUiText';
import React, { useMemo, useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { recordingService, type Recording, type RecordingCreate } from '../../services/recordingService';
import type { EPGProgram } from '../../services/epgService';
import { localRecordingTime, recordingTimeChoices } from '../../utils/recordingTimes';
import { getErrorMessage } from '../../utils/errorUtils';
import { createRecordingIntent } from '../../utils/recordingIntent';

interface Props { channelId: number; channelName: string; programme?: EPGProgram; recording?: Recording; onClose: () => void; onSaved?: () => void }
const RecordingDialog: React.FC<Props> = ({ channelId, channelName, programme, recording, onClose, onSaved }) => {
  const tUi = useUiText();
  const initialZone = recording?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
  const [adjustTimes, setAdjustTimes] = useState(!programme || Boolean(recording));
  const [startEdited, setStartEdited] = useState(false);
  const [endEdited, setEndEdited] = useState(false);
  const [zone, setZone] = useState(initialZone);
  const [start, setStart] = useState(() => localRecordingTime(new Date(recording?.start_time ?? programme?.start_time ?? Date.now()), initialZone));
  const [end, setEnd] = useState(() => localRecordingTime(new Date(recording?.end_time ?? programme?.end_time ?? Date.now() + 3600_000), initialZone));
  const [startChoice, setStartChoice] = useState('');
  const [endChoice, setEndChoice] = useState('');
  const [requestStart] = useState(() => new Date().toISOString());
  const [key] = useState(() => recording ? null : createRecordingIntent());
  const submitting = React.useRef(false);
  const starts = useMemo(() => recordingTimeChoices(start, zone), [start, zone]);
  const ends = useMemo(() => recordingTimeChoices(end, zone), [end, zone]);
  const originalStart = recording?.start_time ?? programme?.start_time;
  const originalEnd = recording?.end_time ?? programme?.end_time;
  const startInstant = !startEdited && originalStart ? new Date(originalStart).toISOString() : starts.length === 1 ? starts[0] : starts.includes(startChoice) ? startChoice : '';
  const endInstant = !endEdited && originalEnd ? new Date(originalEnd).toISOString() : ends.length === 1 ? ends[0] : ends.includes(endChoice) ? endChoice : '';
  const active = recording && recording.state !== 'scheduled';
  const now = !recording && (!programme || Date.parse(programme.start_time) <= Date.now());
  const queries = useQueryClient();
  const save = useMutation({ mutationFn: async () => {
    if (recording) return recordingService.edit(recording.id, { expected_revision: recording.revision, ...(!active ? { start_time: startInstant } : {}), end_time: endInstant });
    if (!key) throw new Error('This browser cannot create a secure recording request. Use an updated browser or HTTPS.');
    const selection: RecordingCreate['programme'] = programme ? { id: programme.id, epg_channel_id: programme.epg_channel_id, title: programme.title,
      start_time: programme.start_time, end_time: programme.end_time, subtitle: programme.subtitle, description: programme.description, category: programme.category } : undefined;
    return recordingService.create({ tv_channel_id: channelId, mode: now ? 'now' : 'schedule', start_time: now ? requestStart : startInstant,
      end_time: endInstant, timezone: zone, idempotency_key: key, programme: selection });
  }, onSuccess: () => { void queries.invalidateQueries({ queryKey: ['recordings'] }); onSaved?.(); onClose(); },
  onSettled: () => { submitting.current = false; } });
  const minutes = endInstant && (startInstant || now) ? Math.round((Date.parse(endInstant) - (now ? Date.now() : Date.parse(startInstant))) / 60000) : 0;
  return <Dialog open onClose={save.isPending ? undefined : onClose} fullWidth maxWidth="sm" aria-labelledby="recording-title">
    <DialogTitle id="recording-title">{recording ? tUi("Edit recording") : now ? tUi("Record now") : tUi("Schedule recording")}</DialogTitle>
    <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      <Typography fontWeight={600}>{programme?.title ?? recording?.snapshot.title ?? channelName}</Typography>
      {!recording && !key ? <Alert severity="error">{tUi("This browser cannot create a secure recording request. Use an updated browser or HTTPS. Your recording has not been created.")}</Alert> : null}
      <Typography color="text.secondary">{channelName} {' '}{tUi("· Uses the channel’s available streams, which may differ from the stream you’re watching.")}</Typography>
      {programme ? <>
        <Typography>{tUi("Programme:")}{' '}{new Date(programme.start_time).toLocaleString(getLocale())} – {new Date(programme.end_time).toLocaleString(getLocale())} · {initialZone}</Typography>
        {now ? <Typography>{tUi("Recording starts now and stops at the selected end time.")}</Typography> : null}
        <Button aria-expanded={adjustTimes} onClick={() => setAdjustTimes(value => !value)}>{adjustTimes ? tUi("Hide time controls") : tUi("Adjust recording times")}</Button>
      </> : null}
      {adjustTimes ? <>
      <TextField label={tUi("Timezone")} value={zone} onChange={(e) => { setZone(e.target.value); setStartEdited(true); setEndEdited(true); }} disabled={Boolean(recording)} />
      <TextField label={tUi("Start")} type="datetime-local" value={start} InputLabelProps={{ shrink: true }} disabled={Boolean(active || now)} onChange={(e) => { setStart(e.target.value); setStartEdited(true); }} />
      {!now && (startEdited || !originalStart) && starts.length > 1 ? <TextField select label={tUi("Start occurs twice — choose an instant")} value={startChoice} onChange={(e) => setStartChoice(e.target.value)}>{starts.map((value) => <MenuItem key={value} value={value}>{value} {' '}{tUi("(UTC)")}</MenuItem>)}</TextField> : null}
      <TextField label={tUi("End")} type="datetime-local" value={end} InputLabelProps={{ shrink: true }} onChange={(e) => { setEnd(e.target.value); setEndEdited(true); }} />
      {(endEdited || !originalEnd) && ends.length > 1 ? <TextField select label={tUi("End occurs twice — choose an instant")} value={endChoice} onChange={(e) => setEndChoice(e.target.value)}>{ends.map((value) => <MenuItem key={value} value={value}>{value} {' '}{tUi("(UTC)")}</MenuItem>)}</TextField> : null}
      {!ends.length || (!now && !starts.length) ? <Alert severity="warning">{tUi("This time does not exist in the chosen timezone, or the timezone is invalid.")}</Alert> : null}
      </> : null}
      {minutes > 0 ? <Typography variant="body2">{minutes} {' '}{tUi("minutes · Estimated")}{' '}{((minutes * 60 * 3_000_000) / 1024**3).toFixed(1)} {' '}{tUi("GiB with headroom. Actual size depends on the stream.")}</Typography> : null}
      <Typography variant="body2" color="text.secondary">{tUi("Start early to allow for source startup. Guide changes won’t move this recording.")}</Typography>
      {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    </Stack></DialogContent>
    <DialogActions><Button onClick={onClose} disabled={save.isPending}>{tUi("Cancel")}</Button><Button variant="contained" disabled={save.isPending || (!recording && !key) || !endInstant || (!now && !startInstant) || minutes <= 0 || minutes > 720} onClick={() => { if (!submitting.current) { submitting.current = true; save.mutate(); } }}>{save.isPending ? tUi("Saving…") : recording ? tUi("Save times") : now ? tUi("Record now") : tUi("Schedule")}</Button></DialogActions>
  </Dialog>;
};
export default RecordingDialog;

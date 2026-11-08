import { useUnsavedChanges } from '../UnsavedChanges';
import { useConfirm } from '../ConfirmDialog';
import { useUiText } from '../../i18n/useUiText';
import React, { useRef, useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, LinearProgress, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { recordingService, type RecordingSettings } from '../../services/recordingService';
import { getErrorMessage } from '../../utils/errorUtils';
const Editor: React.FC<{ initial: RecordingSettings }> = ({ initial }) => {
  const tUi = useUiText();
  const normalize = (settings: RecordingSettings): RecordingSettings => ({ enabled: settings.enabled ?? false, max_concurrent: settings.max_concurrent ?? 1,
    min_free_bytes: settings.min_free_bytes ?? 2147483648, max_recording_bytes: settings.max_recording_bytes ?? 107374182400, retention_days: settings.retention_days ?? null });
  const [baseline, setBaseline] = useState(() => normalize(initial));
  const [value, setValue] = useState(baseline);
  const { confirm, dialog } = useConfirm();
  const submitting = useRef(false);
  const queries = useQueryClient();
  const save = useMutation({ mutationFn: recordingService.configure, onSuccess: result => {
    const saved = normalize(result); setBaseline(saved); setValue(saved);
    queries.setQueryData(['recordings', 'settings'], result);
    void queries.invalidateQueries({ queryKey: ['recordings'] });
  }, onSettled: () => { submitting.current = false; } });
  const dirty = JSON.stringify(value) !== JSON.stringify(baseline);
  useUnsavedChanges(dirty, save.isPending);
  const valid = Number.isInteger(value.max_concurrent) && value.max_concurrent! >= 1 && value.max_concurrent! <= 4
    && Number.isSafeInteger(value.min_free_bytes) && value.min_free_bytes! >= 64 * 1024**2
    && Number.isSafeInteger(value.max_recording_bytes) && value.max_recording_bytes! >= 1024**2
    && (value.retention_days == null || Number.isInteger(value.retention_days) && value.retention_days >= 1 && value.retention_days <= 3650);
  const submit = async () => {
    if (!dirty || !valid || submitting.current) return;
    submitting.current = true;
    const submitted = value;
    if (baseline.enabled && !submitted.enabled && !await confirm(() => ({ title: tUi('Disable recordings?'),
      body: tUi('Active recordings will stop and future recordings will be cancelled. Saved files will remain.'),
      confirmLabel: tUi('Disable recordings'), danger: true }))) { submitting.current = false; return; }
    save.mutate(submitted);
  };
  return <>{dialog}<Stack component="fieldset" disabled={save.isPending} spacing={2} sx={{ border: 0, m: 0, p: 0, minWidth: 0 }}>

    <FormControlLabel control={<Checkbox checked={value.enabled} onChange={(_, enabled) => setValue({ ...value, enabled })} />} label={tUi("Enable recordings")} />
    <Typography variant="body2">{tUi("Configure RECORDINGS_DIR on the server to an existing persistent directory. Disabling stops active recordings and cancels future recordings; saved files remain.")}</Typography>
    <TextField label={tUi("Simultaneous recordings")} type="number" inputProps={{ min: 1, max: 4 }} value={value.max_concurrent} onChange={(e) => setValue({ ...value, max_concurrent: Number(e.target.value) })} />
    <TextField label={tUi("Keep free (GiB)")} type="number" inputProps={{ min: 0.0625, step: "any" }} value={(value.min_free_bytes ?? 2147483648)/1024**3} onChange={(e) => setValue({ ...value, min_free_bytes: Math.round(Number(e.target.value)*1024**3) })} />
    <TextField label={tUi("Maximum size per recording (GiB)")} type="number" inputProps={{ min: 1/1024, step: "any" }} value={(value.max_recording_bytes ?? 107374182400)/1024**3} onChange={(e) => setValue({ ...value, max_recording_bytes: Math.round(Number(e.target.value)*1024**3) })} />
    <FormControlLabel control={<Checkbox checked={value.retention_days != null} onChange={(_, enabled) => setValue({ ...value, retention_days: enabled ? 30 : null })} />} label={tUi("Automatically delete old, unprotected recordings")} />
    {value.retention_days != null ? <TextField label={tUi("Delete after (days)")} type="number" inputProps={{ min: 1, max: 3650 }} value={value.retention_days} onChange={(e) => setValue({ ...value, retention_days: Number(e.target.value) })} /> : <Typography variant="body2">{tUi("Keep all recordings until you delete them. Low storage stops recording.")}</Typography>}
    {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    {save.isSuccess ? <Alert severity="success">{tUi("Recording settings saved.")}</Alert> : null}
    <Button variant="contained" onClick={() => void submit()} disabled={!dirty || !valid || save.isPending}>{tUi("Save recording settings")}</Button>
    <Button disabled={!dirty || save.isPending} onClick={() => { setValue(baseline); save.reset(); }}>{tUi('Discard changes')}</Button>
  </Stack></>;
};
const RecordingSettingsFields: React.FC = () => {
  const tUi = useUiText();
  const query = useQuery({ queryKey: ['recordings', 'settings'], queryFn: recordingService.settings });
  if (query.isLoading) return <LinearProgress aria-label={tUi("Loading recording settings")} />;
  if (query.isError || !query.data) return <Alert severity="error" action={<Button onClick={() => void query.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load recording settings.")}</Alert>;
  return <Editor initial={query.data} />;
};
export default RecordingSettingsFields;

import React, { useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, LinearProgress, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { recordingService, type RecordingSettings } from '../../services/recordingService';
import { getErrorMessage } from '../../utils/errorUtils';
const Editor: React.FC<{ initial: RecordingSettings }> = ({ initial }) => {
  const [value, setValue] = useState(initial);
  const queries = useQueryClient();
  const save = useMutation({ mutationFn: () => recordingService.configure(value), onSuccess: () => { void queries.invalidateQueries({ queryKey: ['recordings'] }); } });
  return <Stack spacing={2}>
    <FormControlLabel control={<Checkbox checked={value.enabled} onChange={(_, enabled) => setValue({ ...value, enabled })} />} label="Enable recordings" />
    <Typography variant="body2">Configure RECORDINGS_DIR on the server to an existing persistent directory. Disabling stops active recordings and cancels future recordings; saved files remain.</Typography>
    <TextField label="Simultaneous recordings" type="number" inputProps={{ min: 1, max: 4 }} value={value.max_concurrent} onChange={(e) => setValue({ ...value, max_concurrent: Number(e.target.value) })} />
    <TextField label="Keep free (GiB)" type="number" value={(value.min_free_bytes ?? 2147483648)/1024**3} onChange={(e) => setValue({ ...value, min_free_bytes: Math.round(Number(e.target.value)*1024**3) })} />
    <TextField label="Maximum size per recording (GiB)" type="number" value={(value.max_recording_bytes ?? 107374182400)/1024**3} onChange={(e) => setValue({ ...value, max_recording_bytes: Math.round(Number(e.target.value)*1024**3) })} />
    <FormControlLabel control={<Checkbox checked={value.retention_days != null} onChange={(_, enabled) => setValue({ ...value, retention_days: enabled ? 30 : undefined })} />} label="Automatically delete old, unprotected recordings" />
    {value.retention_days != null ? <TextField label="Delete after (days)" type="number" inputProps={{ min: 1 }} value={value.retention_days} onChange={(e) => setValue({ ...value, retention_days: Number(e.target.value) })} /> : <Typography variant="body2">Keep all recordings until you delete them. Low storage stops recording.</Typography>}
    {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    {save.isSuccess ? <Alert severity="success">Recording settings saved.</Alert> : null}
    <Button variant="contained" onClick={() => save.mutate()} disabled={save.isPending}>Save recording settings</Button>
  </Stack>;
};
const RecordingSettingsFields: React.FC = () => {
  const query = useQuery({ queryKey: ['recordings', 'settings'], queryFn: recordingService.settings });
  if (query.isLoading) return <LinearProgress aria-label="Loading recording settings" />;
  if (query.isError || !query.data) return <Alert severity="error">Unable to load recording settings.</Alert>;
  return <Editor initial={query.data} />;
};
export default RecordingSettingsFields;

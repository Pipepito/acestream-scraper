import React, { useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, LinearProgress, Stack, Switch, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getOfflineCleanup, saveOfflineCleanup, previewOfflineCleanup, type OfflineCleanupConfig } from '../../services/configService';
import { getErrorMessage } from '../../utils/errorUtils';

export default function OfflineCleanupFields() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ['offlineCleanup'], queryFn: getOfflineCleanup });
  const [draft, setDraft] = useState<OfflineCleanupConfig | null>(null);
  const save = useMutation({ mutationFn: saveOfflineCleanup, onSuccess: data => {
    client.setQueryData(['offlineCleanup'], data);
    void client.invalidateQueries({ queryKey: ['dashboard-background-tasks'] });
    setDraft(null);
  } });
  const preview = useMutation({ mutationFn: previewOfflineCleanup });
  const config = draft ?? query.data;
  if (query.isLoading) return <LinearProgress aria-label="Loading offline cleanup settings" />;
  if (query.isError || !config) return <Alert severity="error" action={<Button onClick={() => void query.refetch()}>Retry</Button>}>Could not load offline cleanup settings.</Alert>;
  const change = (patch: Partial<OfflineCleanupConfig>) => { setDraft({ ...config, ...patch }); save.reset(); preview.reset(); };
  const valid = Number.isInteger(config.offline_days) && config.offline_days >= 1 && config.offline_days <= 365 && Number.isInteger(config.interval_days) && config.interval_days >= 1 && config.interval_days <= 90;
  return <Stack component="form" aria-label="Offline stream cleanup" spacing={2} onSubmit={(event: React.FormEvent) => { event.preventDefault(); if (valid) save.mutate(config); }}>
    <FormControlLabel control={<Switch checked={config.enabled} disabled={save.isPending} onChange={(_, enabled) => change({ enabled })} />} label="Automatically remove long-offline AceStreams" />
    <Typography variant="body2" color="text.secondary">Live TV hides offline streams without deleting them. This optional job removes streams from enabled scraper sources after repeated offline checks, including a check in the last 24 hours. Manual additions, unknown results and checker outages do not qualify.</Typography>
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
      <TextField label="Offline for at least (days)" type="number" value={config.offline_days || ''} onChange={event => change({ offline_days: Number(event.target.value) })} inputProps={{ min: 1, max: 365, step: 1 }} disabled={save.isPending} helperText="Default: 14 days. Tracking starts with new checks after this update." />
      <TextField label="Run every (days)" type="number" value={config.interval_days || ''} onChange={event => change({ interval_days: Number(event.target.value) })} inputProps={{ min: 1, max: 90, step: 1 }} disabled={save.isPending} helperText="7 means weekly. Optional start time is below." />
    </Stack>
    <FormControlLabel control={<Checkbox checked={config.remove_linked} disabled={save.isPending} onChange={(_, remove_linked) => change({ remove_linked })} />} label="Also remove streams linked to TV channels" />
    {config.remove_linked ? <Alert severity="warning">TV channels and their guides stay. Removed streams lose their links and priority order; if found again, they may need matching again.</Alert> : <Typography variant="body2" color="text.secondary">Linked streams are kept by default.</Typography>}
    <FormControlLabel control={<Checkbox checked={config.rescrape} disabled={save.isPending} onChange={(_, rescrape) => change({ rescrape })} />} label="Re-scrape affected sources after cleanup" />
    <Typography variant="body2" color="text.secondary">Rediscovered streams return as unchecked until a probe verifies them. Up to 500 streams are removed per run. Cleanup waits for the maintenance queue and defers while someone is watching or recording.</Typography>
    {preview.data ? <Alert severity="info">{preview.data.eligible_streams} streams from {preview.data.sources} sources qualify now. Preview changes nothing; the job checks eligibility again when it runs.</Alert> : null}
    {preview.isError || save.isError ? <Alert severity="error">{getErrorMessage(preview.error ?? save.error)}</Alert> : null}
    {save.isSuccess ? <Alert severity="success">Offline cleanup settings saved.</Alert> : null}
    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
      <Button variant="outlined" disabled={!valid || save.isPending || preview.isPending} onClick={() => preview.mutate(config)}>{preview.isPending ? 'Checking…' : 'Preview cleanup'}</Button>
      <Button type="submit" variant="contained" disabled={!draft || !valid || save.isPending}>{save.isPending ? 'Saving…' : 'Save cleanup settings'}</Button>
    </Stack>
  </Stack>;
}

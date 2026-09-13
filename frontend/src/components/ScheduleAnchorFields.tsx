import React, { useState } from 'react';
import { Alert, Button, LinearProgress, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getScheduleAnchors, saveScheduleAnchors, type ScheduleAnchors } from '../services/configService';
import { getErrorMessage } from '../utils/errorUtils';

const jobs = [
  ['url_scraping', 'Scrape sources start time'],
  ['epg_refresh', 'EPG refresh start time'],
  ['channel_status', 'Stream checks start time'],
] as const;

export default function ScheduleAnchorFields() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ['scheduleAnchors'], queryFn: getScheduleAnchors });
  const [draft, setDraft] = useState<ScheduleAnchors | null>(null);
  const save = useMutation({ mutationFn: saveScheduleAnchors, onSuccess: data => {
    client.setQueryData(['scheduleAnchors'], data);
    void client.invalidateQueries({ queryKey: ['dashboard-background-tasks'] });
    setDraft(null);
  } });
  const config = draft ?? query.data;
  if (query.isLoading) return <LinearProgress aria-label="Loading schedule start times" />;
  if (query.isError || !config) return <Alert severity="error" action={<Button onClick={() => void query.refetch()}>Retry</Button>}>Unable to load schedule start times.</Alert>;
  const change = (value: Partial<ScheduleAnchors>) => { setDraft({ ...config, ...value }); save.reset(); };
  return <Stack component="form" aria-label="Schedule start times" spacing={2} onSubmit={(event: React.FormEvent) => {
    event.preventDefault();
    save.mutate(config);
  }}>
    <Typography variant="subtitle2">Schedule start times</Typography>
    <Typography variant="body2" color="text.secondary">Jobs repeat at the intervals above. Leave a start time blank to count from application startup. Due maintenance jobs wait their turn, so a long run can delay the next job.</Typography>
    <TextField label="Schedule timezone" size="small" required value={config.timezone} onChange={event => change({ timezone: event.target.value })} disabled={save.isPending} helperText="For example: Europe/Madrid or UTC. Intervals that divide evenly into an hour or day keep local clock times. Other intervals use elapsed time and can shift with daylight saving." />
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
      {jobs.map(([key, label]) => <TextField key={key} label={label} type="time" size="small" value={config[key] ?? ''} disabled={save.isPending} InputLabelProps={{ shrink: true }} onChange={event => change({ [key]: event.target.value || null })} sx={theme => ({ flex: 1, colorScheme: theme.palette.mode })} />)}
    </Stack>
    {save.isError && <Alert severity="error">{getErrorMessage(save.error)}</Alert>}
    {save.isSuccess && <Alert severity="success">Schedule start times saved.</Alert>}
    <Button type="submit" variant="outlined" disabled={!draft || save.isPending} sx={{ alignSelf: 'flex-start' }}>{save.isPending ? 'Saving…' : 'Save start times'}</Button>
  </Stack>;
}

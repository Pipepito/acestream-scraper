import React, { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, Link, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import { setupQueryKey, setupService, type SetupState, type RuntimeOption } from '../services/setupService';
import { ApiError } from '../services/apiErrors';
import { getErrorMessage } from '../utils/errorUtils';

const steps = ['Playback', 'Network access', 'Optional services', 'Review'];
const groups = ['playback', 'network', 'services'];
const nextSteps = [
  { to: '/scraper', label: 'Add an official broadcaster', detail: 'Add https://www.atresplayer.com, https://www.mediasetinfinity.es, https://www.telemadrid.es or https://www.7riojaplay.tv in Scraper, then review the imported channels. Nothing is imported automatically.' },
  { to: '/epg?tab=sources', label: 'Add programme guides', detail: 'Choose your XMLTV sources, preview matches and apply the channel assignments you want.' },
  { to: '/tv-channels', label: 'Organize TV channels', detail: 'Assign streams, set numbers and favorites, then open Live TV or export a playlist.' },
  { to: '/settings?tab=automation', label: 'Schedule updates', detail: 'Choose refresh intervals and optional start times. Review matching and cleanup before enabling automation.' },
  { to: '/integrations/media-servers', label: 'Connect players and media servers', detail: 'Configure the public address, playback route, tuner and remote players for your network.' },
];

function SetupForm({ initial }: { initial: SetupState }) {
  const client = useQueryClient();
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(initial.runtime);
  const [step, setStep] = useState(0);
  const [advanced, setAdvanced] = useState(false);
  const [finished, setFinished] = useState(false);
  const heading = useRef<HTMLDivElement>(null);
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (finished) { top.current?.focus(); top.current?.scrollIntoView?.({ block: 'start' }); }
  }, [finished]);
  const changes = saved.options.filter(option => draft[option.name] !== saved.runtime[option.name]);
  const mutation = useMutation({
    mutationFn: setupService.save,
    onSuccess: state => { setSaved(state); setDraft(state.runtime); setFinished(true); client.setQueryData(setupQueryKey, state); },
  });
  const move = (index: number) => { setStep(index); heading.current?.focus(); };
  const field = (option: RuntimeOption) => {
    const value = draft[option.name] ?? option.default;
    const reason = saved.unavailable[option.name];
    if (option.kind === 'boolean') return <Box key={option.name}>
      <FormControlLabel control={<Checkbox checked={value === true} disabled={mutation.isPending || (Boolean(reason) && !value)} onChange={(_, checked) => setDraft(previous => ({ ...previous, [option.name]: checked }))} />} label={option.label} />
      <Typography variant="body2" color="text.secondary">{reason || option.help}</Typography>
    </Box>;
    const numeric = option.kind === 'number' || option.kind === 'integer';
    return <TextField key={option.name} label={option.label} value={value} disabled={mutation.isPending} fullWidth type={numeric ? 'number' : 'text'}
      helperText={option.help || undefined} inputProps={numeric ? { min: option.minimum, max: option.maximum, step: option.kind === 'integer' ? 1 : 'any' } : { maxLength: 4096 }}
      onChange={event => setDraft(previous => ({ ...previous, [option.name]: numeric && event.target.value !== '' ? Number(event.target.value) : event.target.value }))} />;
  };
  return <>
    <Box ref={top} tabIndex={-1} sx={{ outlineOffset: 4, scrollMarginTop: 80 }}><PageHeader title="Set up scraper" subtitle="Choose how this installation runs. You can revisit setup from Settings." actions={<Button component={RouterLink} to="/">Explore the app</Button>} /></Box>
    <StatusLine items={[{ label: 'Setup', value: finished ? 'Saved' : `${step + 1} of ${steps.length}` }, { label: 'Configuration', value: 'runtime-config.json beside the database' }, { label: 'Runtime', value: saved.restart_required ? 'Restart required' : 'Current settings' }]} />
    {mutation.isError ? <Alert severity="error" sx={{ mb: 2 }}>{mutation.error instanceof ApiError && mutation.error.status === 409 ? 'Configuration changed in another session. Reload the saved configuration before trying again.' : getErrorMessage(mutation.error)} <Button onClick={() => window.location.reload()}>Reload saved configuration</Button></Alert> : null}
    {finished ? <>
      <Alert severity="success" sx={{ mb: 2 }}>{saved.restart_required ? 'Setup saved. Restart the container or native application to apply runtime changes. This will interrupt active playback.' : 'Setup saved. You can now add your sources.'}</Alert>
      <ContentSection title="Build your catalogue" description="Start with broadcaster-owned sources you are authorized to access. Availability may depend on your region.">
        <Stack spacing={3}>{nextSteps.map(item => <Box key={item.to}><Link component={RouterLink} to={item.to}>{item.label}</Link><Typography variant="body2" sx={{ mt: 0.5 }}>{item.detail}</Typography></Box>)}</Stack>
      </ContentSection>
      <Button onClick={() => { setFinished(false); move(0); }}>Review runtime settings</Button>
    </> : <Box component="form" onSubmit={event => { event.preventDefault(); if (step < 3) move(step + 1); else mutation.mutate({ expected_revision: saved.revision, runtime: draft, setup_complete: true }); }}>
      <Box ref={heading} tabIndex={-1} sx={{ outlineOffset: 4 }}><Typography variant="h6" component="h2" sx={{ mb: 2 }}>{steps[step]}</Typography></Box>
      <ContentSection>
        <Stack spacing={3}>
          {step === 0 ? <Typography>Official HTTP broadcasts can play without AceStream. Choose an engine only if you need AceStream playback or checks. Existing saved playback and checker settings remain authoritative in Settings.</Typography> : null}
          {step === 1 ? <Alert severity={saved.api_protected ? 'success' : 'warning'}>{saved.api_protected ? 'API token protection is enabled.' : 'No API token is configured. Keep this installation on a trusted network, or set API_TOKEN in your deployment before exposing it.'} Credentials stay outside the setup file.</Alert> : null}
          {step === 2 ? <Typography>Software must be included in your image. Ports, persistent volumes and Docker permissions still belong in your Compose file. Enabling Acexy here does not change the playback route; choose that in Settings → Playback.</Typography> : null}
          {step < 3 ? saved.options.filter(option => option.group === groups[step]).map(field) : <>
            <Typography>Save runtime choices to the file beside your database. Once it exists, environment values for these options are ignored. Changes take effect after a restart. Existing database settings and sources are preserved.</Typography>
            <Typography component="h3" variant="subtitle1">{changes.length ? `${changes.length} changes` : 'No runtime changes'}</Typography>
            {changes.map(option => <Typography key={option.name} sx={{ overflowWrap: 'anywhere' }}>{option.label}: {String(draft[option.name]) || 'Not configured'}</Typography>)}
            <Button disabled={mutation.isPending} aria-expanded={advanced} onClick={() => setAdvanced(value => !value)}>{advanced ? 'Hide advanced settings' : 'Advanced settings'}</Button>
            {advanced ? saved.options.filter(option => option.group === 'advanced').map(field) : null}
          </>}
        </Stack>
      </ContentSection>
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button disabled={step === 0 || mutation.isPending} onClick={() => move(step - 1)}>Back</Button>
        <Button variant="contained" type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Saving…' : step === 3 ? 'Save setup' : 'Continue'}</Button>
      </Stack>
    </Box>}
  </>;
}

export default function Setup() {
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get });
  if (query.isPending) return <Typography role="status">Loading setup…</Typography>;
  if (query.isError) return <Alert severity="error">Setup could not be loaded. <Button onClick={() => query.refetch()}>Retry</Button></Alert>;
  return <SetupForm initial={query.data} />;
}

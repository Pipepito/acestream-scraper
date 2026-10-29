import React, { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, Link, Stack, TextField, Typography, Dialog, DialogTitle, DialogContent, DialogActions, Stepper, Step, StepLabel, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../components/layout/ContentSection';
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

function SetupForm({ initial, onClose }: { initial: SetupState; onClose: () => void }) {
  const fullScreen = useMediaQuery(useTheme().breakpoints.down('sm'));
  const client = useQueryClient();
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(initial.runtime);
  const [step, setStep] = useState(0);
  const [advanced, setAdvanced] = useState(false);
  const [finished, setFinished] = useState(false);
  const heading = useRef<HTMLDivElement>(null);
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const target = finished ? top.current : heading.current;
    target?.focus();
    target?.scrollIntoView?.({ block: 'start' });
  }, [finished, step]);
  const changes = saved.options.filter(option => draft[option.name] !== saved.runtime[option.name]);
  const mutation = useMutation({
    mutationFn: setupService.save,
    onSuccess: state => { setSaved(state); setDraft(state.runtime); setFinished(true); client.setQueryData(setupQueryKey, state); },
  });
  const move = (index: number) => { setStep(index); };
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
  return <Dialog open fullWidth maxWidth="md" fullScreen={fullScreen} aria-labelledby="setup-title" onClose={mutation.isPending ? undefined : onClose}>
    <DialogTitle id="setup-title" ref={top} tabIndex={-1}>Set up scraper</DialogTitle>
    <DialogContent dividers>
    <Typography color="text.secondary" sx={{ mb: 2 }}>Review the settings imported from your deployment. Saved configuration takes precedence on future starts.</Typography>
    {saved.restart_required ? <Alert severity="info" sx={{ mb: 2 }}>Restart required</Alert> : null}
    {!finished ? <>
      <Typography variant="body2" sx={{ display: { sm: 'none' }, mb: 2 }}>Step {step + 1} of {steps.length} · {steps[step]}</Typography>
      <Stepper activeStep={step} sx={{ display: { xs: 'none', sm: 'flex' }, mb: 3 }}>{steps.map(label => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}</Stepper>
    </> : null}
    {mutation.isError ? <Alert severity="error" sx={{ mb: 2 }}>{mutation.error instanceof ApiError && mutation.error.status === 409 ? 'Configuration changed in another session. Reload the saved configuration before trying again.' : getErrorMessage(mutation.error)} <Button onClick={() => window.location.reload()}>Reload saved configuration</Button></Alert> : null}
    {finished ? <>
      <Alert severity="success" sx={{ mb: 2 }}>{saved.restart_required ? 'Setup saved. Restart the container or native application to apply runtime changes. This will interrupt active playback.' : 'Setup saved. You can now add your sources.'}</Alert>
      <ContentSection title="Build your catalogue" description="Start with broadcaster-owned sources you are authorized to access. Availability may depend on your region.">
        <Stack spacing={3}>{nextSteps.map(item => <Box key={item.to}><Link component={RouterLink} to={item.to} onClick={onClose}>{item.label}</Link><Typography variant="body2" sx={{ mt: 0.5 }}>{item.detail}</Typography></Box>)}</Stack>
      </ContentSection>
      <Button onClick={() => { setFinished(false); move(0); }}>Review runtime settings</Button>
    </> : <Box component="form" id="setup-form" onSubmit={event => { event.preventDefault(); if (step < 3) move(step + 1); else mutation.mutate({ expected_revision: saved.revision, runtime: draft, setup_complete: true }); }}>
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
    </Box>}
    </DialogContent>
    <DialogActions sx={{ px: 3, py: 2 }}>
      <Button disabled={mutation.isPending} onClick={onClose}>{finished ? 'Done' : 'Set up later'}</Button>
      <Box sx={{ flex: 1 }} />
      {!finished ? <>
        <Button disabled={step === 0 || mutation.isPending} onClick={() => move(step - 1)}>Back</Button>
        <Button variant="contained" type="submit" form="setup-form" disabled={mutation.isPending}>{mutation.isPending ? 'Saving…' : step === 3 ? 'Save setup' : 'Continue'}</Button>
      </> : null}
    </DialogActions>
  </Dialog>;
}

export default function Setup({ onClose }: { onClose?: () => void }) {
  const navigate = useNavigate();
  const close = onClose ?? (() => navigate('/settings', { replace: true }));
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get });
  if (!query.data) return <Dialog open fullWidth maxWidth="sm" aria-labelledby="setup-loading-title" onClose={close}>
    <DialogTitle id="setup-loading-title">Set up scraper</DialogTitle>
    <DialogContent>{query.isError
      ? <Alert severity="error">Setup could not be loaded. <Button onClick={() => query.refetch()}>Retry</Button></Alert>
      : <Typography role="status">Loading setup…</Typography>}</DialogContent>
    <DialogActions><Button onClick={close}>Set up later</Button></DialogActions>
  </Dialog>;
  return <SetupForm initial={query.data} onClose={close} />;
}

import React, { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, Link, Stack, TextField, Typography, Dialog, DialogTitle, DialogContent, DialogActions, Stepper, Step, StepLabel, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../components/layout/ContentSection';
import { setupQueryKey, setupService, type SetupState, type RuntimeOption } from '../services/setupService';
import { ApiError } from '../services/apiErrors';
import { getErrorMessage } from '../utils/errorUtils';

const steps = ['Playback', 'Network access', 'Optional services', 'Review'];
const groups = ['playback', 'network', 'services'];
const serviceDetails = [
  { flag: 'ENABLE_ACESTREAM_ENGINE', group: 'acestream', label: 'Playback engine connection' },
  { flag: 'ENABLE_ACEXY', group: 'acexy', label: 'Acexy connection and buffering' },
  { flag: 'ENABLE_ZERONET', group: 'zeronet', label: 'ZeroNet ports and access' },
  { flag: 'ENABLE_IPFS', group: 'ipfs', label: 'IPFS ports and access' },
];


export default function RuntimeSetup({ initial, onClose }: { initial: SetupState; onClose: () => void }) {
  const fullScreen = useMediaQuery(useTheme().breakpoints.down('sm'));
  const client = useQueryClient();
  const [saved, setSaved] = useState(initial);
  const [draft, setDraft] = useState(initial.runtime);
  const [step, setStep] = useState(0);
  const [advanced, setAdvanced] = useState(false);
  const [expandedServices, setExpandedServices] = useState<string[]>([]);
  const [finished, setFinished] = useState(false);
  const heading = useRef<HTMLDivElement>(null);
  const top = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const target = finished ? top.current : heading.current;
    target?.focus();
    target?.scrollIntoView?.({ block: 'start' });
  }, [finished, step]);
  const changes = saved.options.filter(option => draft[option.name] !== saved.runtime[option.name]);
  const bundledPlayback = draft.ENABLE_ACESTREAM_ENGINE === true;
  const bundledChecker = draft.ENABLE_ACESTREAM_CHECK_ENGINE === true;
  const playbackAddress = `http://${draft.ACESTREAM_HTTP_HOST || 'localhost'}:${draft.ACESTREAM_HTTP_PORT || 6878}`;
  const checkerAddress = 'http://127.0.0.1:6880';
  const overrides = saved.saved_overrides ?? {};
  const setValues = (values: SetupState['runtime']) => setDraft(previous => ({ ...previous, ...values }));
  const mutation = useMutation({
    mutationFn: setupService.save,
    onSuccess: state => { setSaved(state); setDraft(state.runtime); setFinished(true); client.setQueryData(setupQueryKey, state); },
  });
  const move = (index: number) => { setStep(index); };
  const field = (option: RuntimeOption) => {
    const automaticPlayback = option.name === 'ACE_ENGINE_URL' && bundledPlayback && !draft.ACE_ENGINE_URL;
    const automaticChecker = option.name === 'ACE_CHECK_ENGINE_URL' && bundledChecker;
    const value = automaticChecker ? checkerAddress : automaticPlayback ? playbackAddress : draft[option.name] ?? option.default;
    const reason = saved.unavailable[option.name];
    const helper = automaticChecker ? 'Managed by the bundled checking engine. No external address is needed.'
      : automaticPlayback ? 'Automatic address from the bundled engine. Internal ports are used here, regardless of Docker host mappings.' : option.help;
    if (option.kind === 'boolean') return <Box key={option.name}>
      <FormControlLabel control={<Checkbox checked={value === true} disabled={mutation.isPending || (Boolean(reason) && !value)} onChange={(_, checked) => setDraft(previous => ({ ...previous, [option.name]: checked }))} />} label={option.label} />
      <Typography variant="body2" color="text.secondary">{reason || option.help}</Typography>
    </Box>;
    const numeric = option.kind === 'number' || option.kind === 'integer';
    return <TextField key={option.name} label={option.label} value={value} disabled={mutation.isPending} fullWidth type={numeric ? 'number' : 'text'}
      helperText={helper || undefined} InputProps={{ readOnly: automaticChecker }} inputProps={numeric ? { min: option.minimum, max: option.maximum, step: option.kind === 'integer' ? 1 : 'any' } : { maxLength: 4096 }}
      onChange={event => setDraft(previous => ({ ...previous, [option.name]: numeric && event.target.value !== '' ? Number(event.target.value) : event.target.value }))} />;
  };
  return <Dialog open fullWidth maxWidth="md" fullScreen={fullScreen} aria-labelledby="runtime-setup-title" onClose={mutation.isPending ? undefined : onClose}>
    <DialogTitle id="runtime-setup-title" ref={top} tabIndex={-1}>Connection settings</DialogTitle>
    <DialogContent dividers>
    <Typography color="text.secondary" sx={{ mb: 2 }}>Loaded from your saved configuration, with missing options imported from the deployment. Save here, then restart the container to apply changes.</Typography>
    {saved.restart_required ? <Alert severity="info" sx={{ mb: 2 }}>Restart required</Alert> : null}
    {!finished ? <>
      <Typography variant="body2" sx={{ display: { sm: 'none' }, mb: 2 }}>Step {step + 1} of {steps.length} · {steps[step]}</Typography>
      <Stepper activeStep={step} sx={{ display: { xs: 'none', sm: 'flex' }, mb: 3 }}>{steps.map(label => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}</Stepper>
    </> : null}
    {mutation.isError ? <Alert severity="error" sx={{ mb: 2 }}>{mutation.error instanceof ApiError && mutation.error.status === 409 ? 'Configuration changed in another session. Reload the saved configuration before trying again.' : getErrorMessage(mutation.error)} <Button onClick={() => window.location.reload()}>Reload saved configuration</Button></Alert> : null}
    {finished ? <>
      <Alert severity="success" sx={{ mb: 2 }}>{saved.restart_required ? 'Setup saved. Restart the container or native application to apply runtime changes. This will interrupt active playback.' : 'Connection settings saved.'}</Alert>
      <Typography sx={{ mb: 2 }}>Return to setup to add channel sources and an optional programme guide.</Typography>
      <Button onClick={() => { setFinished(false); move(0); }}>Review runtime settings</Button>
    </> : <Box component="form" id="runtime-setup-form" onSubmit={event => { event.preventDefault(); if (step < 3) move(step + 1); else mutation.mutate({ expected_revision: saved.revision, runtime: draft, setup_complete: saved.setup_complete }); }}>
      <Box ref={heading} tabIndex={-1} sx={{ outlineOffset: 4 }}><Typography variant="h6" component="h2" sx={{ mb: 2 }}>{steps[step]}</Typography></Box>
      <ContentSection>
        <Stack spacing={3}>
          {step === 0 ? <>
            <Alert severity="info">{bundledPlayback ? 'Bundled playback engine enabled in your configuration. Its internal connection is filled in below.' : 'No bundled playback engine is enabled. Use an external engine for AceStream, or leave it empty for HTTP broadcasts only.'} {bundledChecker ? 'A separate bundled engine is selected for channel checks.' : 'Checks use the playback engine unless you configure a dedicated checker.'}</Alert>
            {bundledPlayback && draft.ACE_ENGINE_URL && draft.ACE_ENGINE_URL !== playbackAddress ? <Box>
              <Typography>The bundled engine is available at {playbackAddress}. Your runtime address currently selects another endpoint.</Typography>
              <Button disabled={mutation.isPending} onClick={() => setValues({ ACE_ENGINE_URL: '' })}>Use bundled playback address</Button>
            </Box> : null}
            {bundledChecker && draft.ACE_CHECK_ENGINE_URL ? <Alert severity="warning">An external checker is also configured. Choose the bundled checker before saving, or disable it under Optional services. <Button onClick={() => setValues({ ACE_CHECK_ENGINE_URL: '' })}>Use bundled checker</Button></Alert> : null}
            {Object.prototype.hasOwnProperty.call(overrides, 'ACE_ENGINE_URL') ? <Alert severity="info">Playback currently uses the address saved in Settings: {overrides.ACE_ENGINE_URL || 'Disabled'}. It takes precedence over this runtime default. <Link component={RouterLink} to="/settings?tab=playback">Edit playback settings</Link></Alert> : null}
            {!bundledChecker && Object.prototype.hasOwnProperty.call(overrides, 'ACE_CHECK_ENGINE_URL') ? <Alert severity="info">Saved checking preference: {overrides.ACE_CHECK_ENGINE_URL || 'Use playback engine'}. <Link component={RouterLink} to="/settings?tab=automation">Edit checking settings</Link></Alert> : null}
          </> : null}
          {step === 1 ? <Alert severity={saved.api_protected ? 'success' : 'warning'}>{saved.api_protected ? 'API token protection is enabled.' : 'No API token is configured. Keep this installation on a trusted network, or set API_TOKEN in your deployment before exposing it.'} Credentials stay outside the setup file.</Alert> : null}
          {step === 1 && overrides.PUBLIC_BASE_URL ? <Alert severity="info">Public address saved in Integrations: {overrides.PUBLIC_BASE_URL}. This takes precedence over the runtime default. <Link component={RouterLink} to="/integrations/public-address">Edit public address</Link></Alert> : null}
          {step === 2 ? <>
            <Typography>Enabled services are loaded from your configuration. Expand their controls to change connections, ports and buffering. Restart the container after saving.</Typography>
            {draft.ENABLE_ACEXY === true ? <Alert severity="info">Acexy is enabled at {draft.ACEXY_LISTEN_ADDR || ':8080'}. To use it for app playback, select Acexy in <Link component={RouterLink} to="/settings?tab=playback">Playback settings</Link> with the container&apos;s internal listener port. {overrides.ACEXY_URL ? `Saved proxy address: ${overrides.ACEXY_URL}.` : 'Enabling the service does not change the saved playback route.'}</Alert> : null}
            {draft.ENABLE_WARP === true ? <Typography variant="body2">{draft.WARP_ENABLE_NAT === true ? 'WARP is set to connect before engines start.' : 'WARP is available but will not connect automatically.'} Keep /dev/net/tun, NET_ADMIN and SYS_ADMIN in Docker.</Typography> : null}
            <Typography variant="body2">{saved.recordings_configured ? 'Recordings storage is configured in the deployment.' : 'To record, add a persistent recordings volume and RECORDINGS_DIR to the deployment.'} Volumes, published ports, devices and permissions still need Docker configuration.</Typography>
          </> : null}
          {step < 3 ? saved.options.filter(option => option.group === groups[step]).map(field) : <>
            <Typography>Save these choices to runtime-config.json beside your database. Each saved option overrides its environment variable, so you can remove those variables from Docker after saving. Restart the container to apply them; this interrupts playback. Keep port mappings, volumes, devices, capabilities and credentials in Docker.</Typography>
            <Typography component="h3" variant="subtitle1">{changes.length ? `${changes.length} changes` : 'No runtime changes'}</Typography>
            {changes.map(option => <Typography key={option.name} sx={{ overflowWrap: 'anywhere' }}>{option.label}: {String(draft[option.name]) || 'Not configured'}</Typography>)}
            <Button disabled={mutation.isPending} aria-expanded={advanced} onClick={() => setAdvanced(value => !value)}>{advanced ? 'Hide advanced settings' : 'Advanced settings'}</Button>
            {advanced ? saved.options.filter(option => option.group === 'advanced').map(field) : null}
          </>}
          {step === 2 ? serviceDetails.filter(service => draft[service.flag] === true).map(service => <Box key={service.group}>
            <Button disabled={mutation.isPending} aria-expanded={expandedServices.includes(service.group)} onClick={() => setExpandedServices(previous => previous.includes(service.group) ? previous.filter(group => group !== service.group) : [...previous, service.group])}>{service.label}</Button>
            {expandedServices.includes(service.group) ? <Stack spacing={3} sx={{ mt: 2 }}>{saved.options.filter(option => option.group === service.group).map(field)}</Stack> : null}
            {expandedServices.includes(service.group) && service.group === 'acexy' && bundledPlayback && (draft.ACEXY_HOST !== (draft.ACESTREAM_HTTP_HOST || 'localhost') || draft.ACEXY_PORT !== (draft.ACESTREAM_HTTP_PORT || 6878)) ? <Alert severity="info" sx={{ mt: 2 }}>Acexy currently connects to a different engine. <Button disabled={mutation.isPending} onClick={() => setValues({ ACEXY_HOST: draft.ACESTREAM_HTTP_HOST || 'localhost', ACEXY_PORT: draft.ACESTREAM_HTTP_PORT || 6878 })}>Connect Acexy to bundled engine</Button></Alert> : null}
            {expandedServices.includes(service.group) && (service.group === 'ipfs' || service.group === 'zeronet') ? (() => {
              const name = service.group === 'ipfs' ? 'IPFS_GATEWAY_URL' : 'ZERONET_URL';
              const port = service.group === 'ipfs' ? draft.IPFS_GATEWAY_PORT || 8081 : draft.ZERONET_UI_PORT || 43110;
              const address = `http://127.0.0.1:${port}`;
              return <Box sx={{ mt: 2 }}><Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>Scraper gateway: {String(draft[name] || 'Not configured')}</Typography>{draft[name] !== address ? <Button disabled={mutation.isPending} onClick={() => setValues({ [name]: address })}>Use bundled {service.group === 'ipfs' ? 'IPFS' : 'ZeroNet'} gateway</Button> : null}</Box>;
            })() : null}
          </Box>) : null}
        </Stack>
      </ContentSection>
    </Box>}
    </DialogContent>
    <DialogActions sx={{ px: 3, py: 2 }}>
      <Button disabled={mutation.isPending} onClick={onClose}>{finished ? 'Return to setup' : 'Cancel'}</Button>
      <Box sx={{ flex: 1 }} />
      {!finished ? <>
        <Button disabled={step === 0 || mutation.isPending} onClick={() => move(step - 1)}>Back</Button>
        <Button variant="contained" type="submit" form="runtime-setup-form" disabled={mutation.isPending}>{mutation.isPending ? 'Saving…' : step === 3 ? 'Save setup' : 'Continue'}</Button>
      </> : null}
    </DialogActions>
  </Dialog>;
}

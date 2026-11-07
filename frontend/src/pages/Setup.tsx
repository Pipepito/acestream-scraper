import React, { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Step, StepLabel, Stepper, Typography, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { setupQueryKey, setupService, type SetupState } from '../services/setupService';
import { getErrorMessage } from '../utils/errorUtils';
import SetupSources from '../components/setup/SetupSources';
import SetupGuide from '../components/setup/SetupGuide';
import RuntimeSetup from './RuntimeSetup';

function SetupFlow({ initial, onClose }: { initial: SetupState; onClose: () => void }) {
  const fullScreen = useMediaQuery(useTheme().breakpoints.down('sm'));
  const client = useQueryClient();
  const [step, setStep] = useState(0);
  const [advanced, setAdvanced] = useState(false);
  const [sourceBusy, setSourceBusy] = useState(false);
  const [guideBusy, setGuideBusy] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const save = useMutation({ mutationFn: () => setupService.save({ expected_revision: initial.revision, runtime: {}, setup_complete: true }),
    onSuccess: state => { client.setQueryData(setupQueryKey, state); setStep(2); },
  });
  const busy = sourceBusy || guideBusy || save.isPending;
  useEffect(() => { if (!advanced) { heading.current?.focus(); heading.current?.scrollIntoView?.({ block: 'start' }); } }, [step, advanced]);
  return <>
    <Dialog open={!advanced} keepMounted fullWidth maxWidth="sm" fullScreen={fullScreen} aria-labelledby="setup-title" onClose={busy ? undefined : onClose}>
      <DialogTitle id="setup-title">Set up scraper</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={3}>
          {step < 2 ? <>
            <Typography color="text.secondary">Add your channels, then choose whether to show programme times.</Typography>
            <Stepper activeStep={step} alternativeLabel><Step><StepLabel>Add channels</StepLabel></Step><Step><StepLabel>Programme guide (optional)</StepLabel></Step></Stepper>
          </> : null}
          <Typography ref={heading} tabIndex={-1} component="h2" variant="h6">{step === 0 ? 'Where are your channels?' : step === 1 ? 'Add programme times' : 'Setup saved'}</Typography>
          <Box hidden={step !== 0}><SetupSources active={step === 0 && !advanced} onBusyChange={setSourceBusy} /></Box>
          <Box hidden={step !== 1}><SetupGuide active={step === 1 && !advanced} onBusyChange={setGuideBusy} /></Box>
          {step === 2 ? <Typography>Your sources and any guide matches are saved. Open your channels to see what was imported. You can add more sources in Scraper and manage programme times in EPG whenever you like.</Typography> : null}
          {initial.restart_required ? <Alert severity="info">Connection settings have changed. Restart the container to apply them; this interrupts playback.</Alert> : null}
          {save.isError ? <Alert severity="error">Could not finish setup. Your sources and guide choices are still saved. {getErrorMessage(save.error)} <Button onClick={() => void client.invalidateQueries({ queryKey: setupQueryKey })}>Reload settings</Button></Alert> : null}
          {step < 2 ? <Box><Typography variant="body2" color="text.secondary">Your installation settings are already loaded. Most people can leave them as they are.</Typography><Button disabled={busy} onClick={() => setAdvanced(true)}>Connection settings (advanced)</Button></Box> : null}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2, flexWrap: 'wrap', gap: 1 }}>
        <Button disabled={busy} onClick={onClose}>{step === 2 ? 'Close' : 'Set up later'}</Button>
        <Box sx={{ flex: 1 }} />
        {step === 1 ? <Button disabled={busy} onClick={() => setStep(0)}>Back</Button> : null}
        {step === 0 ? <Button variant="contained" disabled={busy} onClick={() => setStep(1)}>Continue</Button> : step === 1 ? <Button variant="contained" disabled={busy} onClick={() => save.mutate()}>{save.isPending ? 'Saving…' : 'Finish setup'}</Button> : <Button variant="contained" component={RouterLink} to="/acestream-channels" onClick={onClose}>View channels</Button>}
      </DialogActions>
    </Dialog>
    {advanced ? <RuntimeSetup initial={initial} onClose={() => setAdvanced(false)} /> : null}
  </>;
}

export default function Setup({ onClose }: { onClose?: () => void }) {
  const navigate = useNavigate();
  const close = onClose ?? (() => navigate('/settings', { replace: true }));
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get });
  if (!query.data) return <Dialog open fullWidth maxWidth="sm" aria-labelledby="setup-loading-title" onClose={close}>
    <DialogTitle id="setup-loading-title">Set up scraper</DialogTitle>
    <DialogContent>{query.isError ? <Alert severity="error">Setup could not be loaded. <Button onClick={() => void query.refetch()}>Retry</Button></Alert> : <Typography role="status">Loading setup…</Typography>}</DialogContent>
    <DialogActions><Button onClick={close}>Set up later</Button></DialogActions>
  </Dialog>;
  return <SetupFlow initial={query.data} onClose={close} />;
}

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Alert, Box, Button, Container, LinearProgress, Stack, TextField, Typography } from '@mui/material';
import { startupService, type RecoveryAction } from '../services/startupService';
import { ApiError } from '../services/apiErrors';
import { setApiToken } from '../services/apiToken';
import { useConfirm } from './ConfirmDialog';

const StartupGate: React.FC<React.PropsWithChildren> = ({ children }) => {
  const location = useLocation();
  const queryClient = useQueryClient();
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [actionError, setActionError] = useState('');
  const { confirm, dialog } = useConfirm();
  const dedicated = location.pathname === '/startup';
  const query = useQuery({
    queryKey: ['startup'], queryFn: startupService.status, retry: false,
    refetchInterval: (state) => state.state.data?.status === 'ready' && !state.state.data.migration && !dedicated ? 15000 : 2000,
  });
  const data = query.data;
  const authRequired = query.error instanceof ApiError && query.error.status === 401;
  const importPending = data?.migration && !['completed', 'complete', 'done', 'skipped'].includes(data.migration.status);

  const recover = async (action: RecoveryAction) => {
    if (!data) return;
    if (action !== 'retry' && !(await confirm({
      title: action === 'fresh' ? 'Start with an empty database?' : 'Rebuild from readable data?',
      body: action === 'fresh'
        ? 'Your current database and migration files will be backed up first. The app will then start empty. Channels, sources, settings and integrations will need to be set up again. Backups are kept on your data drive.'
        : 'Your current database and migration files will be backed up first. Scraper URLs and EPG sources are recovered first, with old errors and timestamps reset. Other readable V2 data is copied afterward. Channels and programme listings can be rebuilt by scraping and refreshing the recovered sources. Damaged or incompatible rows may be skipped. Programme listings and activity history are not copied. The original V1 import will not run again.',
      confirmLabel: action === 'fresh' ? 'Back up and start fresh' : 'Back up and rebuild', danger: action === 'fresh',
    }))) return;
    setShowResult(true);
    setBusy(true);
    setActionError('');
    try {
      queryClient.setQueryData(['startup'], await startupService.recover(action, data.recovery_token));
    } catch {
      setActionError('Could not request recovery. Refresh the status before trying again.');
      await query.refetch();
    } finally { setBusy(false); }
  };

  const download = async () => {
    setActionError('');
    try { await startupService.download(); }
    catch { setActionError('Could not download diagnostics. Check the connection and try again.'); }
  };

  if (data?.status === 'ready' && !dedicated && !showResult && !authRequired) {
    return <>
      {importPending ? <Alert severity={data.migration?.status === 'error' ? 'warning' : 'info'}
        action={<Button component={RouterLink} to="/startup" color="inherit">View progress</Button>}>
        {data.migration?.status === 'error' ? 'Programme import stopped. Your app is ready to use.'
          : `Importing programme listings: ${(data.migration?.processed ?? 0).toLocaleString()} of ${(data.migration?.total ?? 0).toLocaleString()}. You can use the app.`}
      </Alert> : null}
      {children}
    </>;
  }

  return <Container maxWidth="md" component="main" sx={{ py: { xs: 4, md: 8 } }}>
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" color="text.secondary">ACESTREAM SCRAPER · V2</Typography>
        <Typography variant="h4" component="h1" sx={{ mt: 1 }}>
          {authRequired ? 'Connect to your instance' : data?.status === 'failed' ? 'Startup needs your attention'
            : data?.status === 'ready' ? 'Startup and migration' : 'Getting your app ready'}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {data?.status === 'starting' ? 'Your database is being prepared. Large updates can take a while. Keep the app running.'
            : data?.status === 'ready' ? 'The app is ready. Programme listings may continue importing in the background.'
              : 'Follow startup progress and save a report if you need help.'}
        </Typography>
      </Box>
      {authRequired ? <Box component="form" onSubmit={(event: React.FormEvent) => {
        event.preventDefault(); setApiToken(token); setToken(''); void query.refetch();
      }}>
        <Stack spacing={2}>
          <Typography>This instance requires its API token before showing diagnostics or recovery controls.</Typography>
          <TextField label="API token" type="password" value={token} autoComplete="off" onChange={(event) => setToken(event.target.value)} />
          <Button type="submit" variant="contained" disabled={!token.trim()}>Connect</Button>
        </Stack>
      </Box> : <>
        {query.isError ? <Alert severity="warning" action={<Button onClick={() => void query.refetch()}>Check again</Button>}>
          Connection lost. Retrying automatically; the last known progress is shown below.
        </Alert> : null}
        <Box role="status" aria-live="polite">
          <Typography fontWeight={600}>{data?.phase ?? 'Connecting to the app…'}</Typography>
          {data?.status === 'starting' || !data ? <LinearProgress aria-label="Startup in progress" sx={{ mt: 2,
            '@media (prefers-reduced-motion: reduce)': { '& .MuiLinearProgress-bar': { animation: 'none' } } }} /> : null}
        </Box>
        {data?.guidance ? <Alert severity="error">{data.guidance}</Alert> : null}
        {data?.migration ? <Box>
          <Typography component="h2" variant="h6">Programme listings</Typography>
          <Typography color="text.secondary">{(data.migration.processed ?? 0).toLocaleString()} of {(data.migration.total ?? 0).toLocaleString()} checked · {(data.migration.migrated ?? 0).toLocaleString()} imported · {(data.migration.skipped ?? 0) + (data.migration.stale ?? 0)} skipped or expired</Typography>
          <LinearProgress variant="determinate" value={Math.min(100, Math.max(0, data.migration.percent ?? 0))} aria-label="Programme import progress" sx={{ my: 1 }} />
          {data.migration.status === 'error' ? <Alert severity="warning">The import stopped. Download diagnostics for support. Restarting the app will resume a retryable import from its saved progress.</Alert> : null}
        </Box> : null}
        {actionError ? <Alert severity="error">{actionError}</Alert> : null}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          {data?.status === 'failed' ? <Button variant="contained" disabled={busy || query.isError} onClick={() => void recover('retry')}>Try startup again</Button> : null}
          {data?.status === 'ready' ? <Button component={RouterLink} to="/" variant="contained" onClick={() => setShowResult(false)}>Open app</Button> : null}
          <Button variant="outlined" disabled={!data || busy} onClick={() => void download()}>Download diagnostics</Button>
        </Stack>
        {data?.status === 'failed' && data.recovery_available ? <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
          <Typography component="h2" variant="h6">Database recovery</Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>Try again first if you have fixed a storage or permissions problem. Rebuilding saves a backup and prioritizes your scraper URLs and EPG sources, so you can rebuild channels and programme listings.</Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" disabled={busy || query.isError} onClick={() => void recover('salvage')}>Recover readable data</Button>
            <Button color="error" disabled={busy || query.isError} onClick={() => void recover('fresh')}>Start fresh</Button>
          </Stack>
        </Box> : null}
        <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
          <Typography component="h2" variant="h6" sx={{ mb: 1 }}>Startup activity</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>Latest 300 startup events. Diagnostics exclude database values and credentials.</Typography>
          <Box component="ol" aria-label="Startup activity" sx={{ m: 0, pl: 3, maxHeight: 360, overflow: 'auto' }}>
            {data?.events.map((event, index) => <Box component="li" key={`${event.time}-${index}`} sx={{ py: 0.75, overflowWrap: 'anywhere' }}>
              <Typography component="time" variant="caption" dateTime={event.time} color="text.secondary" sx={{ mr: 1 }}>{new Date(event.time).toLocaleTimeString()}</Typography>
              {event.level !== 'info' ? `${event.level === 'error' ? 'Error' : 'Warning'}: ` : ''}{event.message}
            </Box>)}
          </Box>
        </Box>
      </>}
    </Stack>
    {dialog}
  </Container>;
};

export default StartupGate;

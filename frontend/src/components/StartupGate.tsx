import { uiText } from '../i18n/text';
import { getLocale } from '../i18n/locale';
import { useUiText } from '../i18n/useUiText';
import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Alert, Box, Button, Container, LinearProgress, Stack, TextField, Typography } from '@mui/material';
import { startupService, type RecoveryAction } from '../services/startupService';
import { ApiError } from '../services/apiErrors';
import { setApiToken } from '../services/apiToken';
import { useConfirm } from './ConfirmDialog';

const StartupGate: React.FC<React.PropsWithChildren> = ({ children }) => {
  const tUi = useUiText();
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
  const clockWarning = !query.isError && data?.status !== 'ready'
    && data?.startup_dependency === 'warp' && data.clockSample
    && Math.abs(data.clockSample.differenceMs) > 5 * 60 * 1000 ? data.clockSample : undefined;
  const authRequired = query.error instanceof ApiError && query.error.status === 401;
  const importPending = data?.migration && !['completed', 'complete', 'done', 'skipped'].includes(data.migration.status);

  const recover = async (action: RecoveryAction) => {
    if (!data) return;
    if (action !== 'retry' && !(await confirm(() => ({
      title: action === 'fresh' ? uiText("Start with an empty database?") : uiText("Rebuild from readable data?"),
      body: action === 'fresh'
        ? uiText("Your current database and migration files will be backed up first. The app will then start empty. Channels, sources, settings and integrations will need to be set up again. Backups are kept on your data drive.")
        : uiText("Your current database and migration files will be backed up first. Scraper URLs and EPG sources are recovered first, with old errors and timestamps reset. Other readable V2 data is copied afterward. Channels and programme listings can be rebuilt by scraping and refreshing the recovered sources. Damaged or incompatible rows may be skipped. Programme listings and activity history are not copied. The original V1 import will not run again."),
      confirmLabel: action === 'fresh' ? uiText("Back up and start fresh") : uiText("Back up and rebuild"), danger: action === 'fresh',
    })))) return;
    setShowResult(true);
    setBusy(true);
    setActionError('');
    try {
      queryClient.setQueryData(['startup'], await startupService.recover(action, data.recovery_token));
    } catch {
      setActionError(tUi("Could not request recovery. Refresh the status before trying again."));
      await query.refetch();
    } finally { setBusy(false); }
  };

  const download = async () => {
    setActionError('');
    try { await startupService.download(); }
    catch { setActionError(tUi("Could not download diagnostics. Check the connection and try again.")); }
  };

  if (data?.status === 'ready' && !dedicated && !showResult && !authRequired) {
    return <>
      {importPending ? <Alert severity={data.migration?.status === 'error' ? 'warning' : 'info'}
        action={<Button component={RouterLink} to="/startup" color="inherit">{tUi("View progress")}</Button>}>
        {data.migration?.status === 'error' ? tUi("Programme import stopped. Your app is ready to use.")
          : tUi("Importing programme listings: {{value0}} of {{value1}}. You can use the app.", { value0: (data.migration?.processed ?? 0).toLocaleString(getLocale()), value1: (data.migration?.total ?? 0).toLocaleString(getLocale()) })}
      </Alert> : null}
      {children}
    </>;
  }

  return <Container maxWidth="md" component="main" sx={{ py: { xs: 4, md: 8 } }}>
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" color="text.secondary">{tUi("ACESTREAM SCRAPER · V2")}</Typography>
        <Typography variant="h4" component="h1" sx={{ mt: 1 }}>
          {authRequired ? tUi("Connect to your instance") : data?.status === 'failed' ? tUi("Startup needs your attention")
            : data?.status === 'ready' ? tUi("Startup and migration") : tUi("Getting your app ready")}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {data?.status === 'starting' ? tUi("Your app is being prepared. Startup can take a while. Keep the app running.")
            : data?.status === 'ready' ? tUi("The app is ready. Programme listings may continue importing in the background.")
              : tUi("Follow startup progress and save a report if you need help.")}
        </Typography>
      </Box>
      {authRequired ? <Box component="form" onSubmit={(event: React.FormEvent) => {
        event.preventDefault(); setApiToken(token); setToken(''); void query.refetch();
      }}>
        <Stack spacing={2}>
          <Typography>{tUi("This instance requires its API token before showing diagnostics or recovery controls.")}</Typography>
          <TextField label={tUi("API token")} type="password" value={token} autoComplete="off" onChange={(event) => setToken(event.target.value)} />
          <Button type="submit" variant="contained" disabled={!token.trim()}>{tUi("Connect")}</Button>
        </Stack>
      </Box> : <>
        {query.isError ? <Alert severity="warning" action={<Button onClick={() => void query.refetch()}>{tUi("Check again")}</Button>}>
          {tUi("Connection lost. Retrying automatically; the last known progress is shown below.")}</Alert> : null}
        <Box role="status" aria-live="polite">
          <Typography fontWeight={600}>{data?.phase ?? tUi('Connecting to the app…')}</Typography>
          {data?.status === 'starting' || !data ? <LinearProgress aria-label={tUi("Startup in progress")} sx={{ mt: 2,
            '@media (prefers-reduced-motion: reduce)': { '& .MuiLinearProgress-bar': { animation: 'none' } } }} /> : null}
        </Box>
        {clockWarning ? <Alert severity="warning">
          <Typography>{tUi('The server and browser clocks differ. Check the host’s date and time synchronization. An incorrect clock can prevent WARP from connecting.')}</Typography>
          <Typography variant="body2" sx={{ mt: 1, overflowWrap: 'anywhere' }}>
            {tUi('Server: {{server}} · Browser: {{browser}} · About {{minutes}} minutes apart.', {
              server: new Date(clockWarning.serverTime).toISOString(), browser: new Date(clockWarning.browserTime).toISOString(),
              minutes: Math.round(Math.abs(clockWarning.differenceMs) / 60000).toLocaleString(getLocale()),
            })}
          </Typography>
          <Typography variant="body2">{tUi('The browser clock may also be incorrect. This warning does not change connection checks.')}</Typography>
          <Button href="https://github.com/Pipepito/acestream-scraper/blob/develop/wiki/Troubleshooting.md#warp-startup-and-system-clock" target="_blank" rel="noopener noreferrer" color="inherit">{tUi('Clock troubleshooting')}</Button>
        </Alert> : null}
        {data?.guidance ? <Alert severity="error">{data.guidance}</Alert> : null}
        {data?.migration ? <Box>
          <Typography component="h2" variant="h6">{tUi("Programme listings")}</Typography>
          <Typography color="text.secondary">{(data.migration.processed ?? 0).toLocaleString(getLocale())} {' '}{tUi("of")}{' '}{(data.migration.total ?? 0).toLocaleString(getLocale())} {' '}{tUi("checked ·")}{' '}{(data.migration.migrated ?? 0).toLocaleString(getLocale())} {' '}{tUi("imported ·")}{' '}{(data.migration.skipped ?? 0) + (data.migration.stale ?? 0)} {' '}{tUi("skipped or expired")}</Typography>
          <LinearProgress variant="determinate" value={Math.min(100, Math.max(0, data.migration.percent ?? 0))} aria-label={tUi("Programme import progress")} sx={{ my: 1 }} />
          {data.migration.status === 'error' ? <Alert severity="warning">{tUi("The import stopped. Download diagnostics for support. Restarting the app will resume a retryable import from its saved progress.")}</Alert> : null}
        </Box> : null}
        {actionError ? <Alert severity="error">{actionError}</Alert> : null}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          {data?.status === 'failed' ? <Button variant="contained" disabled={busy || query.isError} onClick={() => void recover('retry')}>{tUi("Try startup again")}</Button> : null}
          {data?.status === 'ready' ? <Button component={RouterLink} to="/" variant="contained" onClick={() => setShowResult(false)}>{tUi("Open app")}</Button> : null}
          <Button variant="outlined" disabled={!data || busy} onClick={() => void download()}>{tUi("Download diagnostics")}</Button>
        </Stack>
        {data?.status === 'failed' && data.recovery_available ? <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
          <Typography component="h2" variant="h6">{tUi("Database recovery")}</Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>{tUi("Try again first if you have fixed a storage or permissions problem. Rebuilding saves a backup and prioritizes your scraper URLs and EPG sources, so you can rebuild channels and programme listings.")}</Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" disabled={busy || query.isError} onClick={() => void recover('salvage')}>{tUi("Recover readable data")}</Button>
            <Button color="error" disabled={busy || query.isError} onClick={() => void recover('fresh')}>{tUi("Start fresh")}</Button>
          </Stack>
        </Box> : null}
        <Box sx={{ borderTop: 1, borderColor: 'divider', pt: 3 }}>
          <Typography component="h2" variant="h6" sx={{ mb: 1 }}>{tUi("Startup activity")}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>{tUi("Latest 300 startup events. Diagnostics exclude database values and credentials.")}</Typography>
          <Box component="ol" aria-label={tUi("Startup activity")} sx={{ m: 0, pl: 3, maxHeight: 360, overflow: 'auto' }}>
            {data?.events.map((event, index) => <Box component="li" key={`${event.time}-${index}`} sx={{ py: 0.75, overflowWrap: 'anywhere' }}>
              <Typography component="time" variant="caption" dateTime={event.time} color="text.secondary" sx={{ mr: 1 }}>{new Date(event.time).toLocaleTimeString(getLocale())}</Typography>
              {event.level !== 'info' ? tUi("{{value0}}: ", { value0: event.level === 'error' ? tUi('Error') : tUi('Warning') }) : ''}{event.message}
            </Box>)}
          </Box>
        </Box>
      </>}
    </Stack>
    {dialog}
  </Container>;
};

export default StartupGate;

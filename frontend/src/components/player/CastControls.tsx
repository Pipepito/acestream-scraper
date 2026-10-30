import React, { useEffect, useState } from 'react';
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { castService } from '../../services/castService';
import { loadBrowserCast, startBrowserCast, stopBrowserCast } from '../../services/browserCast';
import { useAccess } from '../access/AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';

export default function CastControls({ contentId, audioIndex, subtitleIndex }: { contentId: string; audioIndex: number | null; subtitleIndex: number | null }) {
  const access = useAccess();
  const [open, setOpen] = useState(false);
  const [device, setDevice] = useState('');
  const [compatible, setCompatible] = useState(false);
  const [replace, setReplace] = useState(false);
  const [browserSupported, setBrowserSupported] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const permissions = access?.status.permissions ?? [];
  const admin = access?.status.user?.administrator;
  const allowed = Boolean(admin || permissions.includes('cast') || permissions.includes('cast_server'));
  const canBrowser = Boolean(admin || permissions.includes('cast'));
  const capabilities = useQuery({ queryKey: ['cast-capabilities'], queryFn: castService.capabilities, enabled: open && allowed, retry: false });
  const devices = useQuery({ queryKey: ['cast-devices'], queryFn: castService.devices, enabled: open && Boolean(capabilities.data?.server_devices), refetchInterval: open ? 3000 : false, retry: false });
  const sessions = useQuery({ queryKey: ['cast-sessions'], queryFn: castService.sessions, enabled: open && Boolean(capabilities.data?.server_devices), refetchInterval: open ? 3000 : false, retry: false });
  useEffect(() => { if (open && canBrowser) { let active = true; void loadBrowserCast().then(value => { if (active) setBrowserSupported(value); }); return () => { active = false; }; } }, [open, canBrowser]);
  const run = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true); setError(''); setMessage('');
    try { await action(); setMessage(success); if (capabilities.data?.server_devices) await sessions.refetch(); }
    catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  if (!allowed) return null;
  const payload = { content_id: contentId, audio_index: audioIndex, subtitle_index: subtitleIndex, compatibility: compatible, replace };
  return <>
    <Button onClick={() => setOpen(true)}>Cast…</Button>
    <Dialog open={open} onClose={busy ? undefined : () => setOpen(false)} fullWidth maxWidth="sm" aria-labelledby="cast-title">
      <DialogTitle id="cast-title">Cast live video</DialogTitle><DialogContent dividers><Stack spacing={2}>
        {canBrowser ? <><Typography component="h3" variant="subtitle1">My devices</Typography>
          {browserSupported === false ? <Alert severity="info">This browser cannot discover Cast devices. Use server devices below when you have access. Browser casting requires HTTPS and a Cast-capable browser; Chrome on iOS is unsupported.</Alert> : <Button disabled={busy || !browserSupported} onClick={() => void run(() => startBrowserCast(payload), 'Casting to your selected TV. You can close this page.')}>{browserSupported === null ? 'Checking browser support…' : 'Choose a TV through this browser'}</Button>}
          {browserSupported ? <Button disabled={busy} onClick={() => void run(stopBrowserCast, 'Browser cast stopped.')}>Stop my browser cast</Button> : null}
        </> : null}
        <Typography component="h3" variant="subtitle1">Server devices</Typography>
        {capabilities.data?.server_devices ? <>
          <TextField select label="TV" value={device} onChange={e => setDevice(e.target.value)}><MenuItem value="">Select a TV</MenuItem>{devices.data?.map(tv => <MenuItem key={tv.id} value={tv.id}>{tv.name} · {tv.model}</MenuItem>)}</TextField>
          {!devices.data?.length ? <Typography variant="body2">Looking for TVs. Discovery requires multicast access from the scraper to your home network.</Typography> : null}
          {!capabilities.data.media_url_configured ? <Alert severity="info">An administrator must set the TV-accessible application URL in Settings → Access.</Alert> : null}
          <FormControlLabel label="Replace playback already on this TV" control={<Checkbox checked={replace} onChange={(_, value) => setReplace(value)} />} />
          <Button variant="contained" disabled={busy || !device || !capabilities.data.media_url_configured} onClick={() => void run(() => castService.start({ ...payload, device_id: device }), 'Casting started. The TV keeps playing when you close the page.')}>Cast to selected TV</Button>
          {sessions.data?.map(session => <Stack key={session.id} spacing={1}><Typography>{session.device_name} · {session.state}</Typography><Stack direction="row" spacing={1} flexWrap="wrap">{(['play', 'pause', 'stop'] as const).map(action => <Button key={action} disabled={busy} onClick={() => void run(() => castService.command(session.id, action), 'TV updated.')}>{action === 'play' ? 'Play' : action === 'pause' ? 'Pause' : 'Stop'}</Button>)}{session.volume != null ? <><Button disabled={busy} onClick={() => void run(() => castService.command(session.id, 'volume', Math.max(0, (session.volume ?? 0) - 0.1)), 'Volume lowered.')}>Volume down</Button><Typography sx={{ alignSelf: 'center' }}>{Math.round(session.volume * 100)}%</Typography><Button disabled={busy} onClick={() => void run(() => castService.command(session.id, 'volume', Math.min(1, (session.volume ?? 0) + 0.1)), 'Volume raised.')}>Volume up</Button></> : null}</Stack></Stack>)}
        </> : <Typography variant="body2">{capabilities.data?.message ?? 'Checking access…'}</Typography>}
        {capabilities.data?.compatibility_conversion ? <FormControlLabel label="Convert to H.264 for compatibility (720p maximum)" control={<Checkbox checked={compatible} onChange={(_, value) => setCompatible(value)} />} /> : null}
        {error || devices.isError || capabilities.isError ? <Alert severity="error">{error || 'Could not load casting information.'}</Alert> : null}
        {message ? <Alert severity="success">{message}</Alert> : null}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Close</Button></DialogActions>
    </Dialog>
  </>;
}

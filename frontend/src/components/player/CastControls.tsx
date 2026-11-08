import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useState } from 'react';
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { castService } from '../../services/castService';
import { loadBrowserCast, startBrowserCast, stopBrowserCast } from '../../services/browserCast';
import { useAccess } from '../access/AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';

interface CastContentProps { contentId: string; audioIndex: number | null; subtitleIndex: number | null; }

export function CastDialog({ contentId, audioIndex, subtitleIndex, open, onClose }: CastContentProps & { open: boolean; onClose: () => void }) {
  const tUi = useUiText();
  const access = useAccess();
  const [device, setDevice] = useState('');
  const [compatible, setCompatible] = useState(false);
  const [replace, setReplace] = useState(false);
  const [browserSupported, setBrowserSupported] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const permissions = access?.status.permissions ?? [];
  const admin = access?.status.user?.administrator;
  const allowed = Boolean(access?.status.mode === 'open' || admin || permissions.includes('cast') || permissions.includes('cast_server'));
  const canBrowser = Boolean(access?.status.mode === 'open' || admin || permissions.includes('cast'));
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
  return <Dialog open={open} onClose={busy ? undefined : onClose} fullWidth maxWidth="sm" aria-labelledby="cast-title">
      <DialogTitle id="cast-title">{tUi("Cast live video")}</DialogTitle><DialogContent dividers><Stack spacing={2}>
        {canBrowser ? <><Typography component="h3" variant="subtitle1">{tUi("My devices")}</Typography>
          {browserSupported === false ? <Alert severity="info">{tUi("This browser cannot discover Cast devices. Use server devices below when you have access. Browser casting requires HTTPS and a Cast-capable browser; Chrome on iOS is unsupported.")}</Alert> : <Button disabled={busy || !browserSupported} onClick={() => void run(() => startBrowserCast(payload), 'Casting to your selected TV. You can close this page.')}>{browserSupported === null ? tUi("Checking browser support…") : tUi("Choose a TV through this browser")}</Button>}
          {browserSupported ? <Button disabled={busy} onClick={() => void run(stopBrowserCast, 'Browser cast stopped.')}>{tUi("Stop my browser cast")}</Button> : null}
        </> : null}
        <Typography component="h3" variant="subtitle1">{tUi("Server devices")}</Typography>
        {capabilities.data?.server_devices ? <>
          <Button disabled={busy} onClick={() => void run(async () => { await castService.discover(); await devices.refetch(); }, 'TV search finished.')}>{tUi("Find TVs")}</Button>
          <TextField select label={tUi("TV")} value={device} onChange={e => setDevice(e.target.value)}><MenuItem value="">{tUi("Select a TV")}</MenuItem>{devices.data?.map(tv => <MenuItem key={tv.id} value={tv.id}>{tv.name} · {tv.model}</MenuItem>)}</TextField>
          {!devices.data?.length ? <Typography variant="body2">{tUi("Looking for TVs. Open TV casting in the menu to search your home network.")}</Typography> : null}
          {!capabilities.data.media_url_configured ? <Alert severity="info">{tUi("The TV has no address to fetch video from: set Application address for TVs in TV casting, or open the app from your home network.")}</Alert> : null}
          <FormControlLabel label={tUi("Replace playback already on this TV")} control={<Checkbox checked={replace} onChange={(_, value) => setReplace(value)} />} />
          <Button variant="contained" disabled={busy || !device || !capabilities.data.media_url_configured} onClick={() => void run(() => castService.start({ ...payload, device_id: device }), 'Casting started. The TV keeps playing when you close the page.')}>{tUi("Cast to selected TV")}</Button>
          {sessions.data?.map(session => <Stack key={session.id} spacing={1}><Typography>{session.device_name} · {session.state}</Typography><Stack direction="row" spacing={1} flexWrap="wrap">{(['play', 'pause', 'stop'] as const).map(action => <Button key={action} disabled={busy} onClick={() => void run(() => castService.command(session.id, action), 'TV updated.')}>{action === 'play' ? tUi("Play") : action === 'pause' ? tUi("Pause") : tUi("Stop")}</Button>)}{session.volume != null ? <><Button disabled={busy} onClick={() => void run(() => castService.command(session.id, 'volume', Math.max(0, (session.volume ?? 0) - 0.1)), 'Volume lowered.')}>{tUi("Volume down")}</Button><Typography sx={{ alignSelf: 'center' }}>{Math.round(session.volume * 100)}%</Typography><Button disabled={busy} onClick={() => void run(() => castService.command(session.id, 'volume', Math.min(1, (session.volume ?? 0) + 0.1)), 'Volume raised.')}>{tUi("Volume up")}</Button></> : null}</Stack></Stack>)}
        </> : <Typography variant="body2">{capabilities.data?.message ?? 'Checking access…'}</Typography>}
        {admin || access?.status.mode === 'open' ? <Button component={RouterLink} to="/integrations/tv-casting">{tUi("TV casting settings")}</Button> : null}
        {capabilities.data?.compatibility_conversion ? <FormControlLabel label={tUi("Convert to H.264 for compatibility (720p maximum)")} control={<Checkbox checked={compatible} onChange={(_, value) => setCompatible(value)} />} /> : null}
        {error || devices.isError || capabilities.isError ? <Alert severity="error">{error || 'Could not load casting information.'}</Alert> : null}
        {message ? <Alert severity="success">{message}</Alert> : null}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={onClose}>{tUi("Close")}</Button></DialogActions>
    </Dialog>;
}

export default function CastControls(props: CastContentProps) {
  const tUi = useUiText();
  const access = useAccess();
  const [open, setOpen] = useState(false);
  const permissions = access?.status.permissions ?? [];
  const allowed = access?.status.mode === 'open' || access?.status.user?.administrator || permissions.includes('cast') || permissions.includes('cast_server');
  if (!allowed) return null;
  return <><Button onClick={() => setOpen(true)}>{tUi("Cast…")}</Button><CastDialog {...props} open={open} onClose={() => setOpen(false)} /></>;
}

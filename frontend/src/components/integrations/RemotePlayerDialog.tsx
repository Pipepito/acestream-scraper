import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from '@mui/material';
import { useBaseUrls } from '../../hooks/useBaseUrls';
import { useCreateRemotePlayer, useTestRemotePlayer, useUpdateRemotePlayer } from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import { remotePlayerService, type RemotePlayer, type RemotePlayerKind } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';
import { describeRemotePlayerProbe } from '../player/playerCopy';

export interface RemotePlayerDialogProps {
  open: boolean;
  /** null = add a new player. */
  player: RemotePlayer | null;
  prefill?: { host: string; port: number; kind: RemotePlayerKind } | null;
  onClose: () => void;
  notify: (message: string, severity: 'success' | 'error') => void;
}

/** Add or edit one VLC/Kodi player, with an inline "Test connection" probe. */
const RemotePlayerDialog: React.FC<RemotePlayerDialogProps> = ({ open, player, prefill, onClose, notify }) => {
  const [pairing, setPairing] = useState<{ challenge: string; fingerprint: string } | null>(null);
  const [pairingBusy, setPairingBusy] = useState(false);
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [kind, setKind] = useState<RemotePlayerKind>('vlc');
  const [host, setHost] = useState('');
  const [port, setPort] = useState('8080');
  const [username, setUsername] = useState('kodi');
  const [password, setPassword] = useState('');
  const [baseUrlId, setBaseUrlId] = useState<number | ''>('');
  const [probe, setProbe] = useState<{ severity: 'success' | 'warning' | 'error'; text: string } | null>(null);
  const { data: baseUrls = [] } = useBaseUrls();
  const create = useCreateRemotePlayer();
  const update = useUpdateRemotePlayer();
  const test = useTestRemotePlayer();

  useEffect(() => {
    if (!open) return;
    setProbe(null);
    setPassword('');
    setPairing(null);
    setCode('');
    if (player) {
      setName(player.name);
      setKind(player.kind);
      setHost(player.host);
      setPort(String(player.port));
      setUsername(player.username ?? 'kodi');
      setBaseUrlId(player.base_url_id ?? '');
    } else {
      setName('');
      setKind(prefill?.kind ?? 'vlc');
      setHost(prefill?.host ?? '');
      setPort(String(prefill?.port ?? 8080));
      setUsername('kodi');
      setBaseUrlId('');
    }
  }, [open, player, prefill]);

  const resetPairing = () => {
    setPairing(null);
    setCode('');
    setPassword('');
    setProbe(null);
  };

  const pairAndroid = async (finish: boolean) => {
    setPairingBusy(true);
    setProbe(null);
    try {
      if (finish && pairing) {
        const result = await remotePlayerService.finishAndroidPairing({ host: host.trim(), port: Number(port), ...pairing, code });
        setPassword(result.password);
        setPairing(null);
        setCode('');
        setProbe({ severity: 'success', text: 'Paired with VLC Android. Save this player to keep the connection.' });
      } else {
        setPassword('');
        setCode('');
        setPairing(null);
        setPairing(await remotePlayerService.startAndroidPairing(host.trim(), Number(port)));
      }
    } catch (err) {
      setProbe({ severity: 'error', text: err instanceof ApiError ? err.message : getErrorMessage(err) });
    } finally {
      setPairingBusy(false);
    }
  };

  const runTest = async () => {
    setProbe(null);
    try {
      const result = await test.mutateAsync({
        kind,
        host: host.trim(),
        port: Number(port),
        username: kind === 'kodi' ? username : undefined,
        password: password || undefined,
        id: player?.id,
      });
      setProbe(describeRemotePlayerProbe(result));
    } catch (err) {
      setProbe({ severity: 'error', text: err instanceof ApiError ? err.message : getErrorMessage(err) });
    }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (pairingBusy || !valid) return;
    const body = {
      name: name.trim(),
      kind,
      host: host.trim(),
      port: Number(port),
      username: kind === 'kodi' ? username : null,
      base_url_id: baseUrlId === '' ? null : baseUrlId,
    };
    try {
      if (player) {
        await update.mutateAsync({ id: player.id, data: { ...body, password: password || undefined, clear_base_url: baseUrlId === '' } });
        notify(`Saved ${body.name}.`, 'success');
      } else {
        await create.mutateAsync({ ...body, password: password || null });
        notify(`Added ${body.name}.`, 'success');
      }
      onClose();
    } catch (err) {
      notify(
        err instanceof ApiError && err.status === 409 ? `A player named "${body.name}" already exists.` : getErrorMessage(err),
        'error'
      );
    }
  };

  const validTarget = Boolean(host.trim() && /^\d+$/.test(port) && Number(port) >= 1 && Number(port) <= 65535);
  const savedPairing = player?.kind === 'vlc_android' && player.has_password && player.host === host.trim() && player.port === Number(port);
  const valid = Boolean(name.trim() && validTarget && (kind !== 'vlc_android' || password || savedPairing));
  return (
    <Dialog open={open} onClose={pairingBusy ? undefined : onClose} fullWidth maxWidth="sm" aria-labelledby="remote-player-dialog-title">
      <form onSubmit={(event) => void submit(event)}>
        <DialogTitle id="remote-player-dialog-title">{player ? `Edit ${player.name}` : 'Add player'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              inputProps={{ 'aria-label': 'Name' }}
              fullWidth
              required
            />
            <FormControl fullWidth>
              <InputLabel id="remote-player-kind">Player</InputLabel>
              <Select
                labelId="remote-player-kind"
                label="Player"
                value={kind}
                disabled={pairingBusy}
                onChange={(event) => {
                  const next = event.target.value as RemotePlayerKind;
                  setKind(next);
                  setPort(next === 'vlc_android' ? '8443' : '8080');
                  resetPairing();
                }}
              >
                <MenuItem value="vlc">VLC (desktop)</MenuItem>
                <MenuItem value="vlc_android">VLC Android (3.6+)</MenuItem>
                <MenuItem value="kodi">Kodi</MenuItem>
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1}>
              <TextField
                label="Host"
                value={host}
                disabled={pairingBusy}
                onChange={(event) => { setHost(event.target.value); resetPairing(); }}
                inputProps={{ 'aria-label': 'Host' }}
                fullWidth
                required
                helperText={kind === 'vlc_android' ? "Use the host and HTTPS port shown in VLC > Settings > Remote access." : "IP address or hostname on your network"}
              />
              <TextField
                label="Port"
                value={port}
                disabled={pairingBusy}
                onChange={(event) => { setPort(event.target.value); resetPairing(); }}
                inputProps={{ 'aria-label': 'Port', inputMode: 'numeric' }}
                sx={{ width: 120 }}
              />
            </Stack>
            {kind === 'kodi' ? (
              <TextField label="Username" value={username} onChange={(event) => setUsername(event.target.value)} fullWidth />
            ) : null}
            {kind === 'vlc_android' ? (
              <Stack spacing={1}>
                <Alert severity="info">
                  Enable Remote access and playback control in VLC Android 3.6 or later. Keep VLC open when sending video.
                  Request a code, then enter the six digits shown on the Android device within 60 seconds.
                  Android supports pause, resume and volume; stop playback on the device.
                </Alert>
                <Button onClick={() => void pairAndroid(false)} disabled={!validTarget || pairingBusy}>
                  {pairingBusy ? 'Connecting…' : password || savedPairing ? 'Pair again' : 'Request pairing code'}
                </Button>
                {pairing ? <>
                  <Alert severity="info" sx={{ overflowWrap: 'anywhere' }}>
                    Confirm this is your device before pairing. This HTTPS certificate will be remembered.
                    SHA-256: {pairing.fingerprint}
                  </Alert>
                  <TextField label="Pairing code" value={code} disabled={pairingBusy}
                    onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
                    inputProps={{ inputMode: 'numeric', autoComplete: 'one-time-code', maxLength: 6 }} />
                  <Button onClick={() => void pairAndroid(true)} disabled={pairingBusy || !/^\d{6}$/.test(code)}>
                    Pair with VLC Android
                  </Button>
                </> : null}
                {savedPairing && !password ? <Alert severity="success">A paired connection is saved for this device.</Alert> : null}
              </Stack>
            ) : <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
              helperText={
                player?.has_password
                  ? 'Leave empty to keep the saved password. Moving the player to another address or port clears it — type it again.'
                  : kind === 'vlc'
                    ? 'The Lua HTTP password you set in VLC.'
                    : 'From Kodi > Settings > Services > Control.'
              }
            />}
            <FormControl fullWidth size="small">
              <InputLabel id="remote-player-link-format">Stream link format</InputLabel>
              <Select
                labelId="remote-player-link-format"
                label="Stream link format"
                value={baseUrlId}
                onChange={(event) => setBaseUrlId(event.target.value === '' ? '' : Number(event.target.value))}
              >
                <MenuItem value="">Server relay (recommended)</MenuItem>
                {baseUrls.map((entry) => (
                  <MenuItem key={entry.id} value={entry.id}>
                    {entry.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Alert severity="info">When Acexy routing is enabled in Settings, playback uses the server relay instead of this link format.</Alert>
            {probe ? <Alert severity={probe.severity}>{probe.text}</Alert> : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void runTest()} disabled={!validTarget || test.isPending || pairingBusy}>
            {test.isPending ? <CircularProgress size={18} /> : 'Test connection'}
          </Button>
          <Button onClick={onClose} color="inherit" disabled={pairingBusy}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={!valid || create.isPending || update.isPending || pairingBusy}>
            {player ? 'Save' : 'Add player'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default RemotePlayerDialog;

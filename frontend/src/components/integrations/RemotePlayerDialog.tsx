import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
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
import { remotePlayerService, type RemotePlayer, type RemotePlayerKind, type RemotePlayerProbe } from '../../services/remotePlayerService';
import { useConfirm } from '../ConfirmDialog';
import { useUnsavedChanges } from '../UnsavedChanges';
import { getErrorMessage } from '../../utils/errorUtils';
import { describeRemotePlayerProbe, describeRemotePlayerError } from '../player/playerCopy';

export interface RemotePlayerDialogProps {
  open: boolean;
  /** null = add a new player. */
  player: RemotePlayer | null;
  prefill?: { host: string; port: number; kind: RemotePlayerKind } | null;
  onClose: () => void;
  notify: (message: string | (() => string), severity: 'success' | 'error') => void;
}

/** Add or edit one VLC/Kodi player, with an inline "Test connection" probe. */
const RemotePlayerDialog: React.FC<RemotePlayerDialogProps> = ({ open, player, prefill, onClose, notify }) => {
  const tUi = useUiText();
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
  const [feedback, setFeedback] = useState<{ kind: 'probe'; value: RemotePlayerProbe } | { kind: 'paired' } | { kind: 'error'; value: unknown } | null>(null);
  const [saveError, setSaveError] = useState<unknown>(null);
  const [initial, setInitial] = useState('');
  const opened = useRef<string | null>(null);
  const acting = useRef(false);
  const [actionBusy, setActionBusy] = useState(false);
  const { confirm, dialog } = useConfirm();
  const { data: baseUrls = [] } = useBaseUrls();
  const create = useCreateRemotePlayer();
  const update = useUpdateRemotePlayer();
  const test = useTestRemotePlayer();

  useEffect(() => {
    if (!open) { opened.current = null; return; }
    const identity = player?.id.toString() ?? 'new';
    if (opened.current === identity) return;
    opened.current = identity;
    setInitial(JSON.stringify([player?.name ?? '', player?.kind ?? prefill?.kind ?? 'vlc', player?.host ?? prefill?.host ?? '', String(player?.port ?? prefill?.port ?? 8080), player?.username ?? 'kodi', player?.base_url_id ?? '']));
    setSaveError(null);
    setFeedback(null);
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
    setFeedback(null);
  };

  const pairAndroid = async (finish: boolean) => {
    if (acting.current) return;
    acting.current = true; setActionBusy(true);
    setPairingBusy(true);
    setFeedback(null);
    try {
      if (finish && pairing) {
        const result = await remotePlayerService.finishAndroidPairing({ host: host.trim(), port: Number(port), ...pairing, code });
        setPassword(result.password);
        setPairing(null);
        setCode('');
        setFeedback({ kind: 'paired' });
      } else {
        setPassword('');
        setCode('');
        setPairing(null);
        setPairing(await remotePlayerService.startAndroidPairing(host.trim(), Number(port)));
      }
    } catch (err) {
      setFeedback({ kind: 'error', value: err });
    } finally {
      setPairingBusy(false);
      acting.current = false; setActionBusy(false);
    }
  };

  const runTest = async () => {
    if (acting.current) return;
    acting.current = true; setActionBusy(true);
    setFeedback(null);
    try {
      const result = await test.mutateAsync({
        kind,
        host: host.trim(),
        port: Number(port),
        username: kind === 'kodi' ? username : undefined,
        password: password || undefined,
        id: player?.id,
      });
      setFeedback({ kind: 'probe', value: result });
    } catch (err) {
      setFeedback({ kind: 'error', value: err });
    } finally { acting.current = false; setActionBusy(false); }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (acting.current || !valid) return;
    acting.current = true; setActionBusy(true);
    setSaveError(null);
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
        notify(() => (tUi("Saved {{name}}.", { name: body.name })), 'success');
      } else {
        await create.mutateAsync({ ...body, password: password || null });
        notify(() => (tUi("Added {{name}}.", { name: body.name })), 'success');
      }
      onClose();
    } catch (err) {
      setSaveError(err);
    } finally { acting.current = false; setActionBusy(false); }
  };

  const busy = actionBusy || pairingBusy || test.isPending || create.isPending || update.isPending;
  const dirty = Boolean(password || pairing || code || (initial && JSON.stringify([name, kind, host, port, username, baseUrlId]) !== initial));
  useUnsavedChanges(open && dirty, open && busy);
  const close = async () => {
    if (acting.current || busy) return;
    if (dirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onClose();
  };
  const probe = !feedback ? null : feedback.kind === 'probe' ? describeRemotePlayerProbe(feedback.value)
    : feedback.kind === 'paired' ? { severity: 'success' as const, text: tUi('Paired with VLC Android. Save this player to keep the connection.') }
      : { severity: 'error' as const, text: feedback.value instanceof ApiError ? describeRemotePlayerError(feedback.value) : getErrorMessage(feedback.value) };

  const validTarget = Boolean(host.trim() && /^\d+$/.test(port) && Number(port) >= 1 && Number(port) <= 65535);
  const savedPairing = player?.kind === 'vlc_android' && player.has_password && player.host === host.trim() && player.port === Number(port);
  const valid = Boolean(name.trim() && validTarget && (kind !== 'vlc_android' || password || savedPairing));
  return (
    <><Dialog open={open} onClose={() => void close()} fullWidth maxWidth="sm" aria-labelledby="remote-player-dialog-title">
      <form onSubmit={(event) => void submit(event)}>
        <DialogTitle id="remote-player-dialog-title">{player ? tUi("Edit {{value0}}", { value0: player.name }) : tUi("Add player")}</DialogTitle>
        <DialogContent>
          <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0 }}>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label={tUi("Name")}
              value={name}
              onChange={(event) => setName(event.target.value)}
              inputProps={{ 'aria-label': uiText("Name") }}
              fullWidth
              required
            />
            <FormControl fullWidth>
              <InputLabel id="remote-player-kind">{tUi("Player")}</InputLabel>
              <Select
                labelId="remote-player-kind"
                label={tUi("Player")}
                value={kind}
                disabled={busy}
                onChange={(event) => {
                  const next = event.target.value as RemotePlayerKind;
                  setKind(next);
                  setPort(next === 'vlc_android' ? '8443' : '8080');
                  resetPairing();
                }}
              >
                <MenuItem value="vlc">{tUi("VLC (desktop)")}</MenuItem>
                <MenuItem value="vlc_android">{tUi("VLC Android (3.6+)")}</MenuItem>
                <MenuItem value="kodi">{tUi("Kodi")}</MenuItem>
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1}>
              <TextField
                label={tUi("Host")}
                value={host}
                disabled={busy}
                onChange={(event) => { setHost(event.target.value); resetPairing(); }}
                inputProps={{ 'aria-label': uiText("Host") }}
                fullWidth
                required
                helperText={kind === 'vlc_android' ? tUi("Use the host and HTTPS port shown in VLC > Settings > Remote access.") : tUi("IP address or hostname on your network")}
              />
              <TextField
                label={tUi("Port")}
                value={port}
                disabled={busy}
                onChange={(event) => { setPort(event.target.value); resetPairing(); }}
                inputProps={{ 'aria-label': uiText("Port"), inputMode: 'numeric' }}
                sx={{ width: 120 }}
              />
            </Stack>
            {kind === 'kodi' ? (
              <TextField label={tUi("Username")} value={username} onChange={(event) => setUsername(event.target.value)} fullWidth />
            ) : null}
            {kind === 'vlc_android' ? (
              <Stack spacing={1}>
                <Alert severity="info">
                  {tUi("Enable Remote access and playback control in VLC Android 3.6 or later. Keep VLC open when sending video. Request a code, then enter the six digits shown on the Android device within 60 seconds. Android supports pause, resume and volume; stop playback on the device.")}</Alert>
                <Button onClick={() => void pairAndroid(false)} disabled={!validTarget || busy}>
                  {pairingBusy ? tUi("Connecting…") : password || savedPairing ? tUi("Pair again") : tUi("Request pairing code")}
                </Button>
                {pairing ? <>
                  <Alert severity="info" sx={{ overflowWrap: 'anywhere' }}>
                    {tUi("Confirm this is your device before pairing. This HTTPS certificate will be remembered. SHA-256:")}{' '}{pairing.fingerprint}
                  </Alert>
                  <TextField label={tUi("Pairing code")} value={code} disabled={busy}
                    onChange={(event) => setCode(event.target.value.replace(/\D/g, '').slice(0, 6))}
                    inputProps={{ inputMode: 'numeric', autoComplete: 'one-time-code', maxLength: 6 }} />
                  <Button onClick={() => void pairAndroid(true)} disabled={pairingBusy || !/^\d{6}$/.test(code)}>
                    {tUi("Pair with VLC Android")}</Button>
                </> : null}
                {savedPairing && !password ? <Alert severity="success">{tUi("A paired connection is saved for this device.")}</Alert> : null}
              </Stack>
            ) : <TextField
              label={tUi("Password")}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
              helperText={
                player?.has_password
                  ? tUi("Leave empty to keep the saved password. Moving the player to another address or port clears it — type it again.")
                  : kind === 'vlc'
                    ? tUi("The Lua HTTP password you set in VLC.")
                    : tUi("From Kodi > Settings > Services > Control.")
              }
            />}
            <FormControl fullWidth size="small">
              <InputLabel id="remote-player-link-format">{tUi("Stream link format")}</InputLabel>
              <Select
                labelId="remote-player-link-format"
                label={tUi("Stream link format")}
                value={baseUrlId}
                onChange={(event) => setBaseUrlId(event.target.value === '' ? '' : Number(event.target.value))}
              >
                <MenuItem value="">{tUi("Server relay (recommended)")}</MenuItem>
                {baseUrls.map((entry) => (
                  <MenuItem key={entry.id} value={entry.id}>
                    {entry.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Alert severity="info">{tUi("When Acexy routing is enabled in Settings, playback uses the server relay instead of this link format.")}</Alert>
            {saveError ? <Alert severity="error">{saveError instanceof ApiError && saveError.status === 409 ? tUi('A player named "{{name}}" already exists.', { name }) : getErrorMessage(saveError)}</Alert> : null}
            {probe ? <Alert severity={probe.severity}>{probe.text}
              {feedback?.kind === 'probe' && !feedback.value.authenticated ? <Box component="details" sx={{ mt: 1 }}><summary>{tUi('Technical details')}</summary>{feedback.value.message}{feedback.value.hint && feedback.value.hint !== feedback.value.message ? ` ${feedback.value.hint}` : ''}</Box> : null}
            </Alert> : null}
          </Stack>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void runTest()} disabled={!validTarget || test.isPending || busy}>
            {test.isPending ? <CircularProgress size={18} /> : tUi("Test connection")}
          </Button>
          <Button onClick={() => void close()} color="inherit" disabled={busy}>
            {tUi("Cancel")}</Button>
          <Button type="submit" variant="contained" disabled={!valid || create.isPending || update.isPending || busy}>
            {player ? tUi("Save") : tUi("Add player")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>{dialog}</>
  );
};

export default RemotePlayerDialog;

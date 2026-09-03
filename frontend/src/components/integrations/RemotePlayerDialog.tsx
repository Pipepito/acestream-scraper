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
import type { RemotePlayer, RemotePlayerKind, RemotePlayerProbe } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';

export interface RemotePlayerDialogProps {
  open: boolean;
  /** null = add a new player. */
  player: RemotePlayer | null;
  prefill?: { host: string; port: number; kind: RemotePlayerKind } | null;
  onClose: () => void;
  notify: (message: string, severity: 'success' | 'error') => void;
}

const describeProbe = (probe: RemotePlayerProbe): { severity: 'success' | 'warning' | 'error'; text: string } => {
  if (!probe.reachable) return { severity: 'error', text: `${probe.message} ${probe.hint ?? ''}`.trim() };
  if (!probe.authenticated) return { severity: 'warning', text: probe.hint ?? probe.message };
  const access = probe.tuner_access.allowed
    ? ''
    : ` This player (${probe.tuner_access.addresses.join(', ')}) is outside TUNER_ALLOWED_NETWORKS and will get 403 from the stream link: add its network or choose a stream link format that points at the engine or Acexy.`;
  return {
    severity: probe.tuner_access.allowed ? 'success' : 'warning',
    text: `Connected${probe.version ? ` (version ${probe.version})` : ''}.${access}`,
  };
};

/** Add or edit one VLC/Kodi player, with an inline "Test connection" probe. */
const RemotePlayerDialog: React.FC<RemotePlayerDialogProps> = ({ open, player, prefill, onClose, notify }) => {
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
      setProbe(describeProbe(result));
    } catch (err) {
      setProbe({ severity: 'error', text: err instanceof ApiError ? err.message : getErrorMessage(err) });
    }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
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

  const valid = Boolean(name.trim() && host.trim() && /^\d+$/.test(port));
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="remote-player-dialog-title">
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
                onChange={(event) => setKind(event.target.value as RemotePlayerKind)}
              >
                <MenuItem value="vlc">VLC (desktop)</MenuItem>
                <MenuItem value="kodi">Kodi</MenuItem>
              </Select>
            </FormControl>
            <Stack direction="row" spacing={1}>
              <TextField
                label="Host"
                value={host}
                onChange={(event) => setHost(event.target.value)}
                inputProps={{ 'aria-label': 'Host' }}
                fullWidth
                required
                helperText="IP address or hostname on your network"
              />
              <TextField
                label="Port"
                value={port}
                onChange={(event) => setPort(event.target.value)}
                inputProps={{ 'aria-label': 'Port', inputMode: 'numeric' }}
                sx={{ width: 120 }}
              />
            </Stack>
            {kind === 'kodi' ? (
              <TextField label="Username" value={username} onChange={(event) => setUsername(event.target.value)} fullWidth />
            ) : null}
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
              helperText={
                player?.has_password
                  ? 'Leave empty to keep the saved password.'
                  : kind === 'vlc'
                    ? 'The Lua HTTP password you set in VLC.'
                    : 'From Kodi > Settings > Services > Control.'
              }
            />
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
            {probe ? <Alert severity={probe.severity}>{probe.text}</Alert> : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void runTest()} disabled={!host.trim() || test.isPending}>
            {test.isPending ? <CircularProgress size={18} /> : 'Test connection'}
          </Button>
          <Button onClick={onClose} color="inherit">
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={!valid || create.isPending || update.isPending}>
            {player ? 'Save' : 'Add player'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default RemotePlayerDialog;

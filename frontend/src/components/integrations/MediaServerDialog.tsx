import React, { useEffect, useId, useState } from 'react';
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormLabel,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Stack,
  Switch,
  TextField,
} from '@mui/material';
import { useCreateMediaServer, useTestMediaServer, useUpdateMediaServer } from '../../hooks/useMediaServers';
import { ApiError } from '../../services/apiErrors';
import type { MediaServer, MediaServerKind, MediaServerProbe, MediaServerTunerMode } from '../../services/mediaServerService';
import { describeMediaServerError, KIND_LABEL, type MediaServerNotify } from './mediaServerCopy';

export interface MediaServerDialogProps {
  open: boolean;
  /** null = add a new server. */
  server: MediaServer | null;
  onClose: () => void;
  notify: MediaServerNotify;
}

const KEY_HELPER: Record<MediaServerKind, string> = {
  jellyfin: 'Jellyfin: Dashboard > API Keys',
  plex: 'Plex: optional owner token, only needed for automatic guide refresh',
};

const describeProbe = (probe: MediaServerProbe, kind: MediaServerKind): { severity: 'success' | 'warning' | 'error'; text: string } => {
  if (!probe.reachable) return { severity: 'error', text: probe.message };
  if (!probe.authenticated) return { severity: 'warning', text: probe.message };
  const version = probe.version ? ` (version ${probe.version})` : '';
  if (probe.tuner_access.allowed) return { severity: 'success', text: `${probe.message}${version}.` };
  return {
    severity: 'warning',
    text: `${probe.message}${version}. ${KIND_LABEL[kind]} at ${probe.tuner_access.addresses.join(', ')} is outside TUNER_ALLOWED_NETWORKS and will get 403 from the tuner routes; add its network.`,
  };
};

/** Add or edit one Jellyfin/Plex server, with an inline "Test connection" probe. */
const MediaServerDialog: React.FC<MediaServerDialogProps> = ({ open, server, onClose, notify }) => {
  const tunerModeLabelId = useId();
  const [kind, setKind] = useState<MediaServerKind>('jellyfin');
  const [name, setName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [tunerMode, setTunerMode] = useState<MediaServerTunerMode>('hdhomerun');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [probe, setProbe] = useState<{ severity: 'success' | 'warning' | 'error'; text: string } | null>(null);
  const create = useCreateMediaServer();
  const update = useUpdateMediaServer();
  const test = useTestMediaServer();

  useEffect(() => {
    if (!open) return;
    setProbe(null);
    setApiKey('');
    if (server) {
      setKind(server.kind);
      setName(server.name);
      setBaseUrl(server.base_url);
      setTunerMode(server.tuner_mode);
      setAutoRefresh(server.auto_refresh);
    } else {
      setKind('jellyfin');
      setName('');
      setBaseUrl('');
      setTunerMode('hdhomerun');
      setAutoRefresh(true);
    }
  }, [open, server]);

  const runTest = async () => {
    setProbe(null);
    try {
      const result = await test.mutateAsync({ kind, base_url: baseUrl.trim(), api_key: apiKey || undefined, id: server?.id });
      setProbe(describeProbe(result, kind));
    } catch (err) {
      setProbe({ severity: 'error', text: describeMediaServerError(err) });
    }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = {
      name: name.trim(),
      base_url: baseUrl.trim(),
      tuner_mode: tunerMode,
      auto_refresh: autoRefresh,
    };
    try {
      if (server) {
        // An empty key keeps the stored one — the field never shows a secret.
        await update.mutateAsync({ id: server.id, data: apiKey ? { ...body, api_key: apiKey } : body });
        notify(`Saved ${body.name}.`, 'success');
      } else {
        await create.mutateAsync({ ...body, kind, api_key: apiKey || null });
        notify(`Added ${body.name}.`, 'success');
      }
      onClose();
    } catch (err) {
      notify(
        err instanceof ApiError && err.status === 409 ? `A media server named "${body.name}" already exists.` : describeMediaServerError(err),
        'error'
      );
    }
  };

  const valid = Boolean(name.trim() && baseUrl.trim());
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="media-server-dialog-title">
      <form onSubmit={(event) => void submit(event)}>
        <DialogTitle id="media-server-dialog-title">{server ? `Edit ${server.name}` : 'Add media server'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel id="media-server-kind">Media server</InputLabel>
              <Select
                labelId="media-server-kind"
                label="Media server"
                value={kind}
                disabled={server !== null}
                onChange={(event) => setKind(event.target.value as MediaServerKind)}
              >
                <MenuItem value="jellyfin">Jellyfin</MenuItem>
                <MenuItem value="plex">Plex</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              inputProps={{ 'aria-label': 'Name' }}
              fullWidth
              required
            />
            <TextField
              label="Address"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              inputProps={{ 'aria-label': 'Address' }}
              fullWidth
              required
              helperText={`Address of ${KIND_LABEL[kind]} as seen from this server, e.g. http://192.168.1.12:8096`}
            />
            <TextField
              label={kind === 'jellyfin' ? 'API key' : 'Token'}
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              fullWidth
              helperText={server?.has_api_key ? `Leave empty to keep the saved one. ${KEY_HELPER[kind]}` : KEY_HELPER[kind]}
            />
            {kind === 'jellyfin' ? (
              <FormControl>
                <FormLabel id={tunerModeLabelId}>Channels reach Jellyfin as</FormLabel>
                <RadioGroup
                  aria-labelledby={tunerModeLabelId}
                  value={tunerMode}
                  onChange={(event) => setTunerMode(event.target.value as MediaServerTunerMode)}
                >
                  <FormControlLabel
                    value="hdhomerun"
                    control={<Radio />}
                    label="HDHomeRun tuner (recommended) — stable channel identity, favorites survive changes"
                  />
                  <FormControlLabel
                    value="m3u"
                    control={<Radio />}
                    label="M3U playlist + XMLTV — uses tvg-id matching; any change to the address or link format recreates every channel in Jellyfin and drops favorites"
                  />
                </RadioGroup>
              </FormControl>
            ) : null}
            <FormControlLabel
              control={<Switch checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} />}
              label="Refresh the guide automatically when channels change"
            />
            {probe ? <Alert severity={probe.severity}>{probe.text}</Alert> : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void runTest()} disabled={!baseUrl.trim() || test.isPending}>
            {test.isPending ? <CircularProgress size={18} /> : 'Test connection'}
          </Button>
          <Button onClick={onClose} color="inherit">
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={!valid || create.isPending || update.isPending}>
            {server ? 'Save' : 'Add media server'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default MediaServerDialog;

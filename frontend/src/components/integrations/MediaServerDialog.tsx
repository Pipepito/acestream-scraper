import { useConfirm } from '../ConfirmDialog';
import { useUnsavedChanges } from '../UnsavedChanges';
import { translateKnown } from '../../i18n/text';
import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useId, useRef, useState } from 'react';
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
import type { MediaServer, MediaServerKind, MediaServerTunerMode, MediaServerProbe } from '../../services/mediaServerService';
import { describeMediaServerError, describeMediaServerProbe, KIND_LABEL, type MediaServerNotify } from './mediaServerCopy';

export interface MediaServerDialogProps {
  open: boolean;
  /** null = add a new server. */
  server: MediaServer | null;
  onClose: () => void;
  notify: MediaServerNotify;
}

const KEY_HELPER: Record<MediaServerKind, string> = {
  jellyfin: 'Jellyfin needs an administrator API key: in Jellyfin open Dashboard > API Keys and create one.',
  plex: 'Plex: optional owner token, only needed for automatic guide refresh',
};

/** Add or edit one Jellyfin/Plex server, with an inline "Test connection" probe. */
const MediaServerDialog: React.FC<MediaServerDialogProps> = ({ open, server, onClose, notify }) => {
  const tUi = useUiText();
  const tunerModeLabelId = useId();
  const [kind, setKind] = useState<MediaServerKind>('jellyfin');
  const [name, setName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [tunerMode, setTunerMode] = useState<MediaServerTunerMode>('hdhomerun');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [feedback, setFeedback] = useState<{ result: MediaServerProbe; kind: MediaServerKind } | { error: unknown } | null>(null);
  const probe = feedback ? 'result' in feedback ? describeMediaServerProbe(feedback.result, feedback.kind) : { severity: 'error' as const, text: describeMediaServerError(feedback.error) } : null;
  const [saveError, setSaveError] = useState<unknown>(null);
  const [initial, setInitial] = useState('');
  const opened = useRef<string | null>(null);
  const action = useRef(false);
  const { confirm, dialog } = useConfirm();
  const create = useCreateMediaServer();
  const update = useUpdateMediaServer();
  const test = useTestMediaServer();

  useEffect(() => {
    if (!open) { opened.current = null; return; }
    const identity = server?.id.toString() ?? 'new';
    if (opened.current === identity) return;
    opened.current = identity;
    setInitial(JSON.stringify([server?.kind ?? 'jellyfin', server?.name ?? '', server?.base_url ?? '', server?.tuner_mode ?? 'hdhomerun', server?.auto_refresh ?? true]));
    setSaveError(null);
    setFeedback(null);
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
    if (action.current) return;
    action.current = true;
    setFeedback(null);
    try {
      const result = await test.mutateAsync({ kind, base_url: baseUrl.trim(), api_key: apiKey || undefined, id: server?.id });
      setFeedback({ result, kind });
    } catch (err) {
      setFeedback({ error: err });
    } finally { action.current = false; }
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (action.current) return;
    action.current = true;
    setSaveError(null);
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
        notify(() => (tUi('Saved {{name}}.', { name: body.name })), 'success');
      } else {
        await create.mutateAsync({ ...body, kind, api_key: apiKey || null });
        notify(() => (tUi('Added {{name}}.', { name: body.name })), 'success');
      }
      onClose();
    } catch (err) {
      setSaveError(err);
    } finally { action.current = false; }
  };
  const busy = create.isPending || update.isPending || test.isPending;
  const dirty = JSON.stringify([kind, name, baseUrl, tunerMode, autoRefresh]) !== initial || Boolean(apiKey);
  useUnsavedChanges(open && dirty, open && busy);
  const close = async () => {
    if (action.current) return;
    if (dirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onClose();
  };

  const valid = Boolean(name.trim() && baseUrl.trim());
  return (<>
    {dialog}
    <Dialog open={open} onClose={() => void close()} fullWidth maxWidth="sm" aria-labelledby="media-server-dialog-title">
      <form onSubmit={(event) => void submit(event)}>
        <DialogTitle id="media-server-dialog-title">{server ? tUi("Edit {{value0}}", { value0: server.name }) : tUi("Add media server")}</DialogTitle>
        <DialogContent>
          <Stack component="fieldset" disabled={busy} spacing={2} sx={{ mt: 1, mx: 0, p: 0, border: 0, minWidth: 0 }}>
            {saveError != null ? <Alert severity="error">{saveError instanceof ApiError && saveError.status === 409 ? tUi('A media server named "{{name}}" already exists.', { name: name.trim() }) : describeMediaServerError(saveError)}</Alert> : null}
            <FormControl fullWidth>
              <InputLabel id="media-server-kind">{tUi("Media server")}</InputLabel>
              <Select
                labelId="media-server-kind"
                label={tUi("Media server")}
                value={kind}
                disabled={server !== null}
                onChange={(event) => setKind(event.target.value as MediaServerKind)}
              >
                <MenuItem value="jellyfin">{tUi("Jellyfin")}</MenuItem>
                <MenuItem value="plex">{tUi("Plex")}</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label={tUi("Name")}
              value={name}
              onChange={(event) => setName(event.target.value)}
              inputProps={{ 'aria-label': uiText("Name") }}
              fullWidth
              required
            />
            <TextField
              label={tUi("Address")}
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
              inputProps={{ 'aria-label': uiText("Address") }}
              fullWidth
              required
              helperText={tUi("Address of {{value0}} as seen from this server, e.g. http://192.168.1.12:8096", { value0: KIND_LABEL[kind] })}
            />
            <TextField
              label={kind === 'jellyfin' ? tUi("API key") : tUi("Token")}
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              fullWidth
              helperText={server?.has_api_key ? tUi("Leave empty to keep the saved one. {{value0}}", { value0: translateKnown(KEY_HELPER[kind]) }) : translateKnown(KEY_HELPER[kind])}
            />
            {kind === 'jellyfin' ? (
              <FormControl>
                <FormLabel id={tunerModeLabelId}>{tUi("Channels reach Jellyfin as")}</FormLabel>
                <RadioGroup
                  aria-labelledby={tunerModeLabelId}
                  value={tunerMode}
                  onChange={(event) => setTunerMode(event.target.value as MediaServerTunerMode)}
                >
                  <FormControlLabel
                    value="hdhomerun"
                    control={<Radio />}
                    label={tUi("HDHomeRun tuner (recommended) — stable channel identity, favorites survive changes")}
                  />
                  <FormControlLabel
                    value="m3u"
                    control={<Radio />}
                    label={tUi("M3U playlist + XMLTV — uses tvg-id matching; any change to the address or link format recreates every channel in Jellyfin and drops favorites")}
                  />
                </RadioGroup>
              </FormControl>
            ) : null}
            <FormControlLabel
              control={<Switch checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} />}
              label={tUi("Refresh the guide automatically when channels change")}
            />
            {probe ? <Alert severity={probe.severity}>{probe.text}</Alert> : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void runTest()} disabled={!baseUrl.trim() || busy}>
            {test.isPending ? <CircularProgress size={18} /> : tUi("Test connection")}
          </Button>
          <Button disabled={busy} onClick={() => void close()} color="inherit">
            {tUi("Cancel")}</Button>
          <Button type="submit" variant="contained" disabled={!valid || busy}>
            {server ? tUi("Save") : tUi("Add media server")}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  </>);
};

export default MediaServerDialog;

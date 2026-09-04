import React, { useEffect, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  FormControlLabel,
  Grid,
  IconButton,
  List,
  ListItem,
  Paper,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from '@mui/material';
import CheckCircleOutlineRoundedIcon from '@mui/icons-material/CheckCircleOutlineRounded';
import ContentCopyRoundedIcon from '@mui/icons-material/ContentCopyRounded';
import ErrorOutlineRoundedIcon from '@mui/icons-material/ErrorOutlineRounded';
import ExpandMoreRoundedIcon from '@mui/icons-material/ExpandMoreRounded';
import WarningAmberRoundedIcon from '@mui/icons-material/WarningAmberRounded';
import ContentSection from '../layout/ContentSection';
import RowActionsMenu from '../RowActionsMenu';
import { useConfirm } from '../ConfirmDialog';
import EmptyState from '../state/EmptyState';
import {
  useConnectMediaServer,
  useDeleteMediaServer,
  useDisconnectMediaServer,
  useMediaServerStatus,
  useMediaServers,
  useRefreshMediaServer,
  useTestMediaServer,
} from '../../hooks/useMediaServers';
import { useTunerSettings, useUpdateTunerSettings } from '../../hooks/useTuner';
import type { MediaServer } from '../../services/mediaServerService';
import type { TunerSettings } from '../../services/tunerService';
import { formatRelativeTime } from '../../utils/format';
import { describeMediaServerError, KIND_LABEL, SYNC_META, SYNC_NEEDS_ATTENTION, type MediaServerNotify } from './mediaServerCopy';
import MediaServerDialog from './MediaServerDialog';

export interface MediaServersSectionProps {
  notify: MediaServerNotify;
}

/** Plex refreshes its own guide only when it has both a token and a known DVR. */
const canRefresh = (server: MediaServer): boolean => server.kind !== 'plex' || (server.has_api_key && Boolean(server.dvr_key));

interface PasteRowProps {
  label: string;
  value: string;
  copyLabel: string;
  onCopy: (label: string, value: string) => void;
}

const PasteRow: React.FC<PasteRowProps> = ({ label, value, copyLabel, onCopy }) => (
  <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
    <Typography variant="caption" color="text.secondary" sx={{ width: 108, flexShrink: 0 }}>
      {label}
    </Typography>
    <Typography variant="body2" sx={{ fontFamily: 'monospace', overflowWrap: 'anywhere', minWidth: 0, flex: 1 }}>
      {value}
    </Typography>
    <Tooltip title={copyLabel}>
      <IconButton size="small" aria-label={copyLabel} onClick={() => onCopy(label, value)}>
        <ContentCopyRoundedIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  </Stack>
);

interface ServerCardProps {
  server: MediaServer;
  notify: MediaServerNotify;
  onEdit: () => void;
  onTest: () => void;
  onDelete: () => void;
  onDisconnect: () => void;
}

const ServerCard: React.FC<ServerCardProps> = ({ server, notify, onEdit, onTest, onDelete, onDisconnect }) => {
  const theme = useTheme();
  const { data: status } = useMediaServerStatus(server.id);
  const refresh = useRefreshMediaServer();
  const connect = useConnectMediaServer();
  const attention = SYNC_NEEDS_ATTENTION.includes(server.last_sync_status);
  const refreshable = canRefresh(server);
  const channelCount = status?.channel_count ?? null;

  const copy = async (label: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      notify(`${label} copied.`, 'success');
    } catch {
      notify(`Could not copy the ${label.toLowerCase()}.`, 'error');
    }
  };

  const runRefresh = async () => {
    try {
      const result = await refresh.mutateAsync(server.id);
      notify(result.message ?? `${server.name} is refreshing its guide.`, result.status === 'ok' ? 'success' : 'warning');
    } catch (err) {
      notify(describeMediaServerError(err), 'error');
    }
  };

  const runConnect = async () => {
    try {
      // Plex answers happily without a token or before its DVR exists, and comes
      // back not connected — say so instead of claiming success the card denies.
      const saved = await connect.mutateAsync(server.id);
      if (saved.connected) {
        notify(`${server.name} is connected.`, 'success');
        return;
      }
      notify(
        saved.kind === 'plex'
          ? `${server.name} answered, but Plex has no DVR using this tuner yet. Add it in Plex with the steps on this card, then connect again.`
          : `${server.name} answered, but it is not connected yet. Test the connection and try again.`,
        'warning'
      );
    } catch (err) {
      notify(describeMediaServerError(err), 'error');
    }
  };

  return (
    <Paper
      variant="outlined"
      role="group"
      aria-label={`Media server ${server.name}`}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        borderColor: theme.appTokens.surface.border,
        backgroundColor: theme.appTokens.surface.raised,
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
            {server.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
            {server.base_url}
          </Typography>
        </Box>
        <Chip size="small" label={KIND_LABEL[server.kind]} />
      </Stack>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip
          size="small"
          variant="outlined"
          color={server.connected ? 'success' : 'default'}
          icon={server.connected ? <CheckCircleOutlineRoundedIcon /> : <ErrorOutlineRoundedIcon />}
          label={server.connected ? 'Connected' : 'Not connected'}
        />
        <Chip
          size="small"
          variant="outlined"
          color={attention ? 'warning' : 'default'}
          icon={attention ? <WarningAmberRoundedIcon /> : undefined}
          label={SYNC_META[server.last_sync_status]}
        />
      </Stack>
      <Typography variant="body2" color="text.secondary">
        Last guide refresh {formatRelativeTime(server.last_sync_at)}
        {channelCount === null ? '' : ` · ${channelCount} channels in ${KIND_LABEL[server.kind]}`}
      </Typography>
      {server.last_sync_status === 'error' && server.last_error ? (
        <Typography variant="body2" color="error.main">
          {server.last_error}
        </Typography>
      ) : null}
      {status?.error ? (
        <Typography variant="body2" color="error.main">
          {status.error}
        </Typography>
      ) : null}
      {server.kind === 'plex' ? (
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="body2" color="text.secondary">
            Live TV &amp; DVR in Plex needs an active Plex Pass.
          </Typography>
          <List component="ol" dense sx={{ listStyleType: 'decimal', pl: 3, py: 0.5 }}>
            {(status?.steps ?? []).map((step) => (
              <ListItem key={step} sx={{ display: 'list-item', px: 0, py: 0.25 }} disableGutters>
                <Typography variant="body2">{step}</Typography>
              </ListItem>
            ))}
          </List>
          <Stack spacing={0.5}>
            {status?.paste.tuner_address ? (
              <PasteRow label="Tuner address" value={status.paste.tuner_address} copyLabel="Copy tuner address" onCopy={(l, v) => void copy(l, v)} />
            ) : null}
            {status?.paste.guide_url ? (
              <PasteRow label="Guide URL" value={status.paste.guide_url} copyLabel="Copy guide URL" onCopy={(l, v) => void copy(l, v)} />
            ) : null}
          </Stack>
        </Box>
      ) : null}
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 'auto', pt: 1 }}>
        <Tooltip title={refreshable ? '' : 'Add a Plex token to refresh automatically'}>
          <span>
            <Button
              size="small"
              variant="outlined"
              aria-label={`Refresh now ${server.name}`}
              disabled={!refreshable || refresh.isPending}
              onClick={() => void runRefresh()}
            >
              Refresh now
            </Button>
          </span>
        </Tooltip>
        {server.connected ? (
          <Button size="small" aria-label={`Disconnect ${server.name}`} onClick={onDisconnect}>
            Disconnect
          </Button>
        ) : (
          <Button size="small" variant="contained" aria-label={`Connect ${server.name}`} disabled={connect.isPending} onClick={() => void runConnect()}>
            Connect
          </Button>
        )}
        <Box sx={{ ml: 'auto' }}>
          <RowActionsMenu
            label={`More actions for ${server.name}`}
            actions={[
              { label: 'Edit', onClick: onEdit },
              { label: 'Test connection', onClick: onTest },
              { label: 'Delete', danger: true, onClick: onDelete },
            ]}
          />
        </Box>
      </Stack>
    </Paper>
  );
};

interface NumberRange {
  min: number;
  max: number;
}

/** The ranges `TunerSettingsUpdate` accepts; anything else comes back as a bare 422. */
const TUNER_COUNT_RANGE: NumberRange = { min: 1, max: 16 };
const MAX_CHANNELS_RANGE: NumberRange = { min: 1, max: 1000 };

/** The two numbers stay text while editing so a cleared field stays cleared instead of turning into 0. */
interface TunerFormState {
  friendly_name: string;
  tuner_count: string;
  max_channels: string;
  only_online: boolean;
}

const rangeError = (value: string, { min, max }: NumberRange): string | null => {
  const parsed = Number(value);
  const valid = value.trim() !== '' && Number.isInteger(parsed) && parsed >= min && parsed <= max;
  return valid ? null : `Enter a whole number between ${min} and ${max}.`;
};

const toForm = (settings: TunerSettings): TunerFormState => ({
  friendly_name: settings.friendly_name,
  tuner_count: String(settings.tuner_count),
  max_channels: String(settings.max_channels),
  only_online: settings.only_online,
});

/** Friendly name, stream cap and lineup size the tuner reports to Jellyfin and Plex. */
const TunerSettingsBlock: React.FC<{ notify: MediaServerNotify }> = ({ notify }) => {
  const { data } = useTunerSettings();
  const update = useUpdateTunerSettings();
  const [form, setForm] = useState<TunerFormState | null>(null);

  useEffect(() => {
    if (data) setForm(toForm(data));
  }, [data]);

  const countError = form ? rangeError(form.tuner_count, TUNER_COUNT_RANGE) : null;
  const channelsError = form ? rangeError(form.max_channels, MAX_CHANNELS_RANGE) : null;
  const canSave = form !== null && countError === null && channelsError === null;

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form || !canSave) return;
    try {
      await update.mutateAsync({
        friendly_name: form.friendly_name,
        tuner_count: Number(form.tuner_count),
        max_channels: Number(form.max_channels),
        only_online: form.only_online,
      });
      notify('Tuner settings saved.', 'success');
    } catch (err) {
      notify(describeMediaServerError(err), 'error');
    }
  };

  return (
    <Accordion disableGutters elevation={0} square sx={{ mt: 2, bgcolor: 'transparent', '&::before': { display: 'none' } }}>
      <AccordionSummary expandIcon={<ExpandMoreRoundedIcon />} sx={{ px: 0 }}>
        <Typography component="h3" variant="subtitle2">
          Tuner settings
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        <Stack component="form" spacing={2} onSubmit={(event: React.FormEvent) => void save(event)} aria-label="Tuner settings form">
          <TextField
            size="small"
            label="Tuner name"
            value={form?.friendly_name ?? ''}
            onChange={(event) => setForm((prev) => (prev ? { ...prev, friendly_name: event.target.value } : prev))}
            inputProps={{ 'aria-label': 'Tuner name' }}
            helperText="The name Jellyfin and Plex show for this tuner."
            fullWidth
          />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <TextField
              size="small"
              type="number"
              label="Streams at once"
              value={form?.tuner_count ?? ''}
              onChange={(event) => setForm((prev) => (prev ? { ...prev, tuner_count: event.target.value } : prev))}
              inputProps={{ 'aria-label': 'Streams at once', min: TUNER_COUNT_RANGE.min, max: TUNER_COUNT_RANGE.max, step: 1 }}
              error={countError !== null}
              helperText={countError ?? 'How many channels can play through the tuner at the same time.'}
              fullWidth
            />
            <TextField
              size="small"
              type="number"
              label="Most channels to publish"
              value={form?.max_channels ?? ''}
              onChange={(event) => setForm((prev) => (prev ? { ...prev, max_channels: event.target.value } : prev))}
              inputProps={{ 'aria-label': 'Most channels to publish', min: MAX_CHANNELS_RANGE.min, max: MAX_CHANNELS_RANGE.max, step: 1 }}
              error={channelsError !== null}
              helperText={channelsError ?? 'Plex stops saving channel maps at roughly 450-480 channels.'}
              fullWidth
            />
          </Stack>
          <FormControlLabel
            control={
              <Switch
                checked={form?.only_online ?? false}
                onChange={(event) => setForm((prev) => (prev ? { ...prev, only_online: event.target.checked } : prev))}
              />
            }
            label="Publish only channels that are online"
          />
          <Box>
            <Button type="submit" variant="contained" size="small" aria-label="Save tuner settings" disabled={!canSave || update.isPending}>
              Save
            </Button>
          </Box>
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
};

/** Saved Jellyfin/Plex servers, what they know about our tuner, and the tuner's own settings. */
const MediaServersSection: React.FC<MediaServersSectionProps> = ({ notify }) => {
  const { data: servers = [], isLoading } = useMediaServers();
  const remove = useDeleteMediaServer();
  const disconnect = useDisconnectMediaServer();
  const test = useTestMediaServer();
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [editing, setEditing] = useState<MediaServer | null>(null);
  const [adding, setAdding] = useState(false);

  const handleDelete = async (server: MediaServer) => {
    const ok = await confirm({
      title: `Delete ${server.name}?`,
      body:
        server.kind === 'jellyfin' && server.connected
          ? 'The server is removed from this list. This also removes the tuner and guide provider from Jellyfin.'
          : 'The server is removed from this list.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await remove.mutateAsync(server.id);
      notify(`Deleted ${server.name}.`, 'success');
    } catch (err) {
      notify(describeMediaServerError(err), 'error');
    }
  };

  const handleDisconnect = async (server: MediaServer) => {
    if (server.kind === 'jellyfin') {
      const ok = await confirm({
        title: `Disconnect ${server.name}?`,
        body: 'This removes the AceStream tuner and its guide provider from Jellyfin. Jellyfin will re-run Refresh Guide and drop those channels.',
        confirmLabel: 'Disconnect',
        danger: true,
      });
      if (!ok) return;
    }
    try {
      await disconnect.mutateAsync(server.id);
      notify(`Disconnected ${server.name}.`, 'success');
    } catch (err) {
      notify(describeMediaServerError(err), 'error');
    }
  };

  const handleTest = async (server: MediaServer) => {
    try {
      const probe = await test.mutateAsync({ kind: server.kind, base_url: server.base_url, id: server.id });
      const ok = probe.reachable && probe.authenticated;
      notify(ok ? `${server.name} answered${probe.version ? ` (version ${probe.version})` : ''}.` : probe.message, ok ? 'success' : 'error');
    } catch (err) {
      notify(describeMediaServerError(err), 'error');
    }
  };

  return (
    <ContentSection
      title="Media servers"
      description="Jellyfin and Plex pick up these channels as a tuner with its own guide."
      actions={
        <Button variant="contained" size="small" onClick={() => setAdding(true)}>
          Add media server
        </Button>
      }
    >
      {isLoading ? (
        <Typography variant="body2">Loading media servers…</Typography>
      ) : servers.length === 0 ? (
        <EmptyState title="No media servers yet" description="Add Jellyfin or Plex to watch these channels there with a full guide." />
      ) : (
        <Grid container spacing={2}>
          {servers.map((server) => (
            <Grid item xs={12} md={6} key={server.id}>
              <ServerCard
                server={server}
                notify={notify}
                onEdit={() => setEditing(server)}
                onTest={() => void handleTest(server)}
                onDelete={() => void handleDelete(server)}
                onDisconnect={() => void handleDisconnect(server)}
              />
            </Grid>
          ))}
        </Grid>
      )}
      <TunerSettingsBlock notify={notify} />
      <MediaServerDialog
        open={adding || editing !== null}
        server={editing}
        onClose={() => {
          setAdding(false);
          setEditing(null);
        }}
        notify={notify}
      />
      {confirmDialog}
    </ContentSection>
  );
};

export default MediaServersSection;

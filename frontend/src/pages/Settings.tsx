import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  FormHelperText,
  IconButton,
  InputAdornment,
  Snackbar,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon, Visibility as VisibilityIcon, VisibilityOff as VisibilityOffIcon } from '@mui/icons-material';
import {
  useBaseUrl,
  useUpdateBaseUrl,
  useAceEngineUrl,
  useUpdateAceEngineUrl,
  useRescrapeInterval,
  useUpdateRescrapeInterval,
  useEpgRefreshInterval,
  useUpdateEpgRefreshInterval,
  useAddPid,
  useUpdateAddPid,
  useAcestreamStatus,
} from '../hooks/useConfig';
import { useBaseUrls, useCreateBaseUrl, usePatchBaseUrl, useDeleteBaseUrl } from '../hooks/useBaseUrls';
import { StreamBaseUrl } from '../services/baseUrlService';
import { ApiError } from '../services/apiErrors';
import { configService } from '../services/configService';
import { getApiToken, setApiToken as storeApiToken, clearApiToken as removeStoredApiToken, isApiTokenRequired, resetApiTokenRequired } from '../services/apiToken';
import { getErrorMessage } from '../utils/errorUtils';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { useConfirm } from '../components/ConfirmDialog';

type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string, severity: FeedbackSeverity) => void;

const describeSaveError = (error: unknown, attemptedName: string, fallback: string): string => {
  if (error instanceof ApiError && error.status === 409) {
    return `A link format named "${attemptedName}" already exists. Choose a different name.`;
  }
  if (error instanceof ApiError && error.message) {
    return error.message;
  }
  return fallback;
};

interface StreamLinkFormatsSectionProps {
  notify: Notify;
}

/**
 * "Stream link formats": the named base URL entries used when generating playlist links.
 * The legacy `base_url` setting shows as a built-in "Default" row (editable in place) until a
 * named entry is marked default.
 */
const StreamLinkFormatsSection: React.FC<StreamLinkFormatsSectionProps> = ({ notify }) => {
  const { confirm, dialog: confirmDialog } = useConfirm();
  const baseUrlsQuery = useBaseUrls();
  const createBaseUrlMutation = useCreateBaseUrl();
  const patchBaseUrlMutation = usePatchBaseUrl();
  const deleteBaseUrlMutation = useDeleteBaseUrl();
  const legacyBaseUrlQuery = useBaseUrl();
  const updateLegacyBaseUrlMutation = useUpdateBaseUrl();

  const [addOpen, setAddOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPattern, setNewPattern] = useState('');
  const [newIsDefault, setNewIsDefault] = useState(false);
  const [editingEntry, setEditingEntry] = useState<StreamBaseUrl | 'builtin' | null>(null);
  const [editName, setEditName] = useState('');
  const [editPattern, setEditPattern] = useState('');

  const entries = baseUrlsQuery.data ?? [];
  const hasNamedDefault = entries.some((entry) => entry.is_default);
  const isMutating =
    createBaseUrlMutation.isPending || patchBaseUrlMutation.isPending || deleteBaseUrlMutation.isPending || updateLegacyBaseUrlMutation.isPending;

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    const pattern = newPattern.trim();
    if (!name || !pattern) return;
    createBaseUrlMutation.mutate(
      { name, pattern, is_default: newIsDefault },
      {
        onSuccess: () => {
          setNewName('');
          setNewPattern('');
          setNewIsDefault(false);
          setAddOpen(false);
          notify(`Link format "${name}" added`, 'success');
        },
        onError: (error) => notify(describeSaveError(error, name, 'Failed to add the link format'), 'error'),
      }
    );
  };

  const handleMakeDefault = (entry: StreamBaseUrl) => {
    patchBaseUrlMutation.mutate(
      { id: entry.id, data: { is_default: true } },
      {
        onSuccess: () => notify(`"${entry.name}" is now the default link format`, 'success'),
        onError: (error) => notify(describeSaveError(error, entry.name, 'Failed to change the default link format'), 'error'),
      }
    );
  };

  const handleDelete = async (entry: StreamBaseUrl) => {
    const ok = await confirm({
      title: `Delete the link format “${entry.name}”?`,
      body: 'Playlists that were built with this format fall back to the default one.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    deleteBaseUrlMutation.mutate(entry.id, {
      onSuccess: () => notify(`Link format "${entry.name}" deleted`, 'success'),
      onError: (error) => notify(describeSaveError(error, entry.name, 'Failed to delete the link format'), 'error'),
    });
  };

  const openEditDialog = (entry: StreamBaseUrl | 'builtin') => {
    setEditingEntry(entry);
    setEditName(entry === 'builtin' ? 'Default' : entry.name);
    setEditPattern(entry === 'builtin' ? legacyBaseUrlQuery.data ?? '' : entry.pattern);
  };

  const closeEditDialog = () => setEditingEntry(null);

  const handleEditSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEntry) return;
    const name = editName.trim();
    const pattern = editPattern.trim();
    if (!pattern || (editingEntry !== 'builtin' && !name)) return;
    if (editingEntry === 'builtin') {
      updateLegacyBaseUrlMutation.mutate(pattern, {
        onSuccess: () => {
          closeEditDialog();
          notify('Default link format updated', 'success');
        },
        onError: (error) => notify(getErrorMessage(error), 'error'),
      });
      return;
    }
    patchBaseUrlMutation.mutate(
      { id: editingEntry.id, data: { name, pattern } },
      {
        onSuccess: () => {
          closeEditDialog();
          notify(`Link format "${name}" updated`, 'success');
        },
        onError: (error) => notify(describeSaveError(error, name, 'Failed to update the link format'), 'error'),
      }
    );
  };

  const renderRow = (key: string | number, name: string, pattern: string, isDefault: boolean, actions: React.ReactNode) => (
    <Box
      key={key}
      sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 1, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, py: 0.75 }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Box sx={{ typography: 'body2', fontWeight: 600, wordBreak: 'break-word' }}>{name}</Box>
          {isDefault ? <Chip label="Default" color="primary" size="small" /> : null}
        </Box>
        <Box sx={{ typography: 'body2', color: 'text.secondary', fontFamily: 'monospace', wordBreak: 'break-all' }}>{pattern}</Box>
      </Box>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0 }}>
        {actions}
      </Stack>
    </Box>
  );

  return (
    <ContentSection
      title="Stream link formats"
      description="How each channel link is written in the playlist. Pick the one your player understands; the Default is used unless the playlist asks for another."
      actions={
        <Button variant="outlined" size="small" onClick={() => setAddOpen(true)}>
          Add format
        </Button>
      }
    >
      <Stack spacing={1.5}>
        {baseUrlsQuery.isLoading ? (
          <Box display="flex" alignItems="center">
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Box component="span">Loading link formats...</Box>
          </Box>
        ) : baseUrlsQuery.error ? (
          <Alert severity="warning">Could not load the saved link formats. Try reloading the page.</Alert>
        ) : (
          <Stack spacing={0.5} divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
            {!hasNamedDefault
              ? renderRow(
                  'builtin',
                  'Default',
                  legacyBaseUrlQuery.data ?? 'acestream://',
                  true,
                  <Tooltip title="Edit the default format">
                    <IconButton size="small" aria-label="Edit default link format" onClick={() => openEditDialog('builtin')} disabled={isMutating}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )
              : null}
            {entries.map((entry) =>
              renderRow(
                entry.id,
                entry.name,
                entry.pattern,
                Boolean(entry.is_default),
                <>
                  {!entry.is_default ? (
                    <Button size="small" variant="outlined" onClick={() => handleMakeDefault(entry)} disabled={isMutating}>
                      Make default
                    </Button>
                  ) : null}
                  <IconButton size="small" aria-label={`Edit base URL ${entry.name}`} onClick={() => openEditDialog(entry)} disabled={isMutating}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" aria-label={`Delete base URL ${entry.name}`} onClick={() => handleDelete(entry)} disabled={isMutating}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </>
              )
            )}
          </Stack>
        )}
        <Typography variant="body2" color="text.secondary">
          A format without placeholders is a prefix put before the channel id (like <code>acestream://</code>). A format with{' '}
          <code>{'{channel_id}'}</code> is a template and may also use <code>{'{pid}'}</code>, for example{' '}
          <code>{'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}'}</code>.
        </Typography>
      </Stack>

      <Dialog open={addOpen} onClose={() => setAddOpen(false)} fullWidth maxWidth="sm">
        <form onSubmit={handleAddSubmit}>
          <DialogTitle>Add link format</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label="Name" fullWidth value={newName} onChange={(e) => setNewName(e.target.value)} helperText="A short label, e.g. VLC or Ace player" />
              <TextField
                label="Pattern"
                fullWidth
                value={newPattern}
                onChange={(e) => setNewPattern(e.target.value)}
                helperText={'A prefix like acestream://, or a template using {channel_id} and optionally {pid}'}
              />
              <FormControlLabel control={<Checkbox checked={newIsDefault} onChange={(e) => setNewIsDefault(e.target.checked)} />} label="Set as default" />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAddOpen(false)} color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained" color="primary" disabled={!newName.trim() || !newPattern.trim() || createBaseUrlMutation.isPending}>
              {createBaseUrlMutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Add base URL'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <Dialog open={Boolean(editingEntry)} onClose={closeEditDialog} fullWidth maxWidth="sm">
        <form onSubmit={handleEditSave}>
          <DialogTitle>{editingEntry === 'builtin' ? 'Edit default link format' : 'Edit link format'}</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              {editingEntry !== 'builtin' ? <TextField label="Name" fullWidth value={editName} onChange={(e) => setEditName(e.target.value)} /> : null}
              <TextField
                label="Pattern"
                fullWidth
                value={editPattern}
                onChange={(e) => setEditPattern(e.target.value)}
                helperText={'A prefix like acestream://, or a template using {channel_id} and optionally {pid}'}
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeEditDialog} color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained" color="primary" disabled={!editPattern.trim() || (editingEntry !== 'builtin' && !editName.trim()) || isMutating}>
              Save changes
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      {confirmDialog}
    </ContentSection>
  );
};

interface IntervalFieldProps {
  id: string;
  label: string;
  helper: string;
  value: number | '';
  saved: number | undefined;
  pending: boolean;
  onChange: (value: number | '') => void;
  onSave: () => void;
}

const IntervalField: React.FC<IntervalFieldProps> = ({ id, label, helper, value, saved, pending, onChange, onSave }) => (
  <Stack
    component="form"
    aria-label={`${label} form`}
    direction="row"
    spacing={1}
    alignItems="flex-start"
    onSubmit={(event: React.FormEvent) => {
      event.preventDefault();
      onSave();
    }}
  >
    <TextField
      id={id}
      label={label}
      type="number"
      size="small"
      value={value}
      onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
      InputProps={{ inputProps: { min: 1, max: 168 } }}
      helperText={helper}
      sx={{ width: 220 }}
    />
    <Button type="submit" variant="outlined" size="small" disabled={pending || value === '' || value === saved} sx={{ mt: 0.5 }}>
      {pending ? <CircularProgress size={18} color="inherit" /> : 'Save'}
    </Button>
  </Stack>
);

const Settings: React.FC = () => {
  const [aceEngineUrl, setAceEngineUrl] = useState('');
  const [rescrapeInterval, setRescrapeInterval] = useState<number | ''>(24);
  const [epgRefreshInterval, setEpgRefreshInterval] = useState<number | ''>(1);
  const [addPid, setAddPid] = useState(false);
  const [appid, setAppid] = useState(false);
  const [appIdError, setAppIdError] = useState('');
  const [appidLoading, setAppidLoading] = useState(true);
  const [appidSubmitting, setAppidSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ open: boolean; message: string; severity: FeedbackSeverity }>({ open: false, message: '', severity: 'success' });
  const [apiTokenInput, setApiTokenInput] = useState<string>(() => getApiToken() ?? '');
  const [showApiToken, setShowApiToken] = useState(false);
  const [apiTokenRequired, setApiTokenRequired] = useState<boolean>(() => isApiTokenRequired());

  const aceEngineUrlQuery = useAceEngineUrl();
  const rescrapeIntervalQuery = useRescrapeInterval();
  const epgRefreshIntervalQuery = useEpgRefreshInterval();
  const addPidQuery = useAddPid();
  const acestreamStatusQuery = useAcestreamStatus({ refetchInterval: 30000 });

  const updateAceEngineUrlMutation = useUpdateAceEngineUrl();
  const updateRescrapeIntervalMutation = useUpdateRescrapeInterval();
  const updateEpgRefreshIntervalMutation = useUpdateEpgRefreshInterval();
  const updateAddPidMutation = useUpdateAddPid();

  const notify: Notify = (message, severity) => setFeedback({ open: true, message, severity });

  useEffect(() => {
    setAppidLoading(true);
    setAppIdError('');
    configService
      .getAppId()
      .then((val) => setAppid(val))
      .catch(() => setAppIdError('Could not load the AppID setting. You can still try the switch.'))
      .finally(() => setAppidLoading(false));
  }, []);

  useEffect(() => {
    if (aceEngineUrlQuery.data) setAceEngineUrl(aceEngineUrlQuery.data);
  }, [aceEngineUrlQuery.data]);
  useEffect(() => {
    if (rescrapeIntervalQuery.data !== undefined) setRescrapeInterval(rescrapeIntervalQuery.data);
  }, [rescrapeIntervalQuery.data]);
  useEffect(() => {
    if (epgRefreshIntervalQuery.data !== undefined) setEpgRefreshInterval(epgRefreshIntervalQuery.data);
  }, [epgRefreshIntervalQuery.data]);
  useEffect(() => {
    if (addPidQuery.data !== undefined) setAddPid(addPidQuery.data);
  }, [addPidQuery.data]);

  const handleAceEngineUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateAceEngineUrlMutation.mutate(aceEngineUrl, {
      onSuccess: () => {
        notify('Engine URL saved', 'success');
        acestreamStatusQuery.refetch();
      },
      onError: (error) => notify(`Failed to save the engine URL: ${getErrorMessage(error)}`, 'error'),
    });
  };

  const handleRescrapeSave = () => {
    if (rescrapeInterval === '') return;
    updateRescrapeIntervalMutation.mutate(rescrapeInterval, {
      onSuccess: () => notify(`Sources will be scraped every ${rescrapeInterval} h`, 'success'),
      onError: (error) => notify(`Failed to save the scrape interval: ${getErrorMessage(error)}`, 'error'),
    });
  };

  const handleEpgRefreshSave = () => {
    if (epgRefreshInterval === '') return;
    updateEpgRefreshIntervalMutation.mutate(epgRefreshInterval, {
      onSuccess: () => notify(`EPG will refresh every ${epgRefreshInterval} h`, 'success'),
      onError: (error) => notify(`Failed to save the EPG refresh interval: ${getErrorMessage(error)}`, 'error'),
    });
  };

  const handleAddPidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAddPid(checked);
    updateAddPidMutation.mutate(checked, {
      onSuccess: () => notify(checked ? 'PID will be appended to stream links' : 'PID will no longer be appended', 'success'),
      onError: (error) => {
        setAddPid(!checked);
        notify(`Failed to save the PID setting: ${getErrorMessage(error)}`, 'error');
      },
    });
  };

  const handleAppidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAppid(checked);
    setAppidSubmitting(true);
    configService
      .updateAppId(checked)
      .then(() => {
        setAppIdError('');
        notify(checked ? 'AppID will be added to stream links' : 'AppID will no longer be added', 'success');
      })
      .catch(() => {
        setAppid(!checked);
        notify('Failed to update AppID setting', 'error');
      })
      .finally(() => setAppidSubmitting(false));
  };

  const handleApiTokenSave = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = apiTokenInput.trim();
    if (!trimmed) return;
    storeApiToken(trimmed);
    setApiTokenInput(trimmed);
    resetApiTokenRequired();
    setApiTokenRequired(false);
    notify('API token saved. It will be sent with future API requests.', 'success');
  };

  const handleApiTokenClear = () => {
    removeStoredApiToken();
    setApiTokenInput('');
    resetApiTokenRequired();
    setApiTokenRequired(false);
    notify('API token cleared', 'success');
  };

  const isLoading = aceEngineUrlQuery.isLoading || rescrapeIntervalQuery.isLoading || addPidQuery.isLoading || appidLoading;

  if (isLoading) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="60vh" gap={1.5}>
        <CircularProgress aria-label="Loading settings" />
        <Box component="p" sx={{ typography: 'sectionTitle', m: 0 }}>
          Loading settings
        </Box>
      </Box>
    );
  }

  const engineOnline = acestreamStatusQuery.data?.status === 'online';

  return (
    <Box>
      <PageHeader title="Settings" subtitle="Engine, stream links, automation and API access." />

      <ContentSection
        title="Engine"
        actions={
          <Button variant="outlined" size="small" onClick={() => acestreamStatusQuery.refetch()} disabled={acestreamStatusQuery.isFetching}>
            Refresh status
          </Button>
        }
      >
        <Stack spacing={2}>
          <Stack direction="row" spacing={1.5} alignItems="center" role="status" aria-label="Engine status">
            {acestreamStatusQuery.isLoading ? (
              <CircularProgress size={18} />
            ) : (
              <Chip label={acestreamStatusQuery.error ? 'Unknown' : engineOnline ? 'Online' : 'Offline'} color={acestreamStatusQuery.error ? 'default' : engineOnline ? 'success' : 'error'} variant="outlined" sx={{ fontWeight: 600, minWidth: 90 }} />
            )}
            <Typography variant="body2" color="text.secondary">
              {acestreamStatusQuery.error
                ? `Could not check the engine: ${getErrorMessage(acestreamStatusQuery.error)}`
                : acestreamStatusQuery.data?.message || 'Checking the engine…'}
            </Typography>
          </Stack>
          <form onSubmit={handleAceEngineUrlSubmit}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'flex-start' }}>
              <TextField
                label="Acestream Engine URL"
                size="small"
                value={aceEngineUrl}
                onChange={(e) => setAceEngineUrl(e.target.value)}
                helperText="Where the backend reaches the engine, e.g. http://localhost:6878"
                sx={{ flex: 1, maxWidth: 480 }}
              />
              <Button type="submit" variant="contained" size="small" disabled={updateAceEngineUrlMutation.isPending || aceEngineUrl === aceEngineUrlQuery.data} sx={{ mt: 0.5 }}>
                {updateAceEngineUrlMutation.isPending ? <CircularProgress size={18} color="inherit" /> : 'Save engine URL'}
              </Button>
            </Stack>
          </form>
        </Stack>
      </ContentSection>

      <StreamLinkFormatsSection notify={notify} />

      <ContentSection title="Automation" description="Background jobs run on these schedules. Changes apply right away.">
        <Stack spacing={2.5}>
          <IntervalField
            id="rescrape-interval"
            label="Scrape sources every (hours)"
            helper="1 to 168 hours"
            value={rescrapeInterval}
            saved={rescrapeIntervalQuery.data}
            pending={updateRescrapeIntervalMutation.isPending}
            onChange={setRescrapeInterval}
            onSave={handleRescrapeSave}
          />
          <IntervalField
            id="epg-refresh-interval"
            label="Refresh EPG every (hours)"
            helper="1 to 168 hours"
            value={epgRefreshInterval}
            saved={epgRefreshIntervalQuery.data}
            pending={updateEpgRefreshIntervalMutation.isPending}
            onChange={setEpgRefreshInterval}
            onSave={handleEpgRefreshSave}
          />
          <Box>
            <FormControlLabel control={<Switch checked={addPid} onChange={handleAddPidChange} disabled={updateAddPidMutation.isPending} />} label="Append PID to stream links" />
            <FormHelperText sx={{ ml: 0 }}>Some players need a PID on each acestream:// link to keep streams apart.</FormHelperText>
          </Box>
          <Box>
            {appIdError ? (
              <Alert severity="warning" sx={{ mb: 1 }}>
                {appIdError}
              </Alert>
            ) : null}
            <FormControlLabel control={<Switch checked={appid} onChange={handleAppidChange} disabled={appidSubmitting} />} label="Use AppID in stream links" />
            <FormHelperText sx={{ ml: 0 }}>Adds the app id to acestream:// links for players that require it (rare).</FormHelperText>
          </Box>
        </Stack>
      </ContentSection>

      <ContentSection title="API access" description="Only needed when the server sets API_TOKEN. The token is stored in this browser and sent with every request.">
        <Stack spacing={2} sx={{ maxWidth: 520 }}>
          {apiTokenRequired ? (
            <Alert severity="warning">The server rejected a request because a valid token is missing. Enter the token below to restore access.</Alert>
          ) : null}
          <form onSubmit={handleApiTokenSave}>
            <Stack spacing={2}>
              <TextField
                id="api-token"
                label="API token"
                size="small"
                type={showApiToken ? 'text' : 'password'}
                fullWidth
                value={apiTokenInput}
                onChange={(e) => setApiTokenInput(e.target.value)}
                autoComplete="off"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton aria-label={showApiToken ? 'Hide API token' : 'Show API token'} onClick={() => setShowApiToken((current) => !current)} edge="end" size="small">
                        {showApiToken ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              <Stack direction="row" spacing={1}>
                <Button type="submit" variant="contained" size="small" disabled={!apiTokenInput.trim()}>
                  Save token
                </Button>
                <Button variant="outlined" color="inherit" size="small" onClick={handleApiTokenClear}>
                  Clear token
                </Button>
              </Stack>
            </Stack>
          </form>
        </Stack>
      </ContentSection>

      <Snackbar open={feedback.open} autoHideDuration={6000} onClose={() => setFeedback((current) => ({ ...current, open: false }))}>
        <Alert onClose={() => setFeedback((current) => ({ ...current, open: false }))} severity={feedback.severity} variant="filled" sx={{ width: '100%' }}>
          {feedback.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;

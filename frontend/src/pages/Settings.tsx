import ScheduleAnchorFields from '../components/ScheduleAnchorFields';
import StreamLinkFormatsSection from '../components/StreamLinkFormatsSection';
import CheckEngineFields from '../components/CheckEngineFields';
import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import PlaybackRoutingFields from '../components/player/PlaybackRoutingFields';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Chip,
  FormControlLabel,
  FormHelperText,
  IconButton,
  InputAdornment,
  Snackbar,
  Stack,
  Switch,
  Tabs,
  Tab,
  TextField,
  Typography,
} from '@mui/material';
import { Visibility as VisibilityIcon, VisibilityOff as VisibilityOffIcon } from '@mui/icons-material';
import {
  useChannelStatusInterval,
  useUpdateChannelStatusInterval,
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
import { configService } from '../services/configService';
import { getApiToken, setApiToken as storeApiToken, clearApiToken as removeStoredApiToken, isApiTokenRequired, resetApiTokenRequired } from '../services/apiToken';
import { getErrorMessage } from '../utils/errorUtils';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string, severity: FeedbackSeverity) => void;
interface IntervalFieldProps {
  max?: number;
  id: string;
  label: string;
  helper: string;
  value: number | '';
  saved: number | undefined;
  pending: boolean;
  onChange: (value: number | '') => void;
  onSave: () => void;
}

const IntervalField: React.FC<IntervalFieldProps> = ({ max = 168, id, label, helper, value, saved, pending, onChange, onSave }) => (
  <Stack
    component="form"
    aria-label={`${label} form`}
    direction={{ xs: 'column', sm: 'row' }}
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
      InputProps={{ inputProps: { min: 1, max, step: 1 } }}
      helperText={helper}
      sx={{ width: { xs: '100%', sm: 280 } }}
    />
    <Button type="submit" variant="outlined" size="small" disabled={pending || value === '' || !Number.isInteger(value) || value < 1 || value > max || value === saved} sx={{ mt: 0.5 }}>
      {pending ? <CircularProgress size={18} color="inherit" /> : 'Save'}
    </Button>
  </Stack>
);

const Settings: React.FC = () => {
  const [params, setParams] = useSearchParams();
  const sections = ['playback', 'automation', 'links', 'access'];
  const section = sections.includes(params.get('tab') ?? '') ? params.get('tab')! : 'playback';
  const panelProps = (name: string) => ({ role: 'tabpanel', id: `settings-panel-${name}`, 'aria-labelledby': `settings-tab-${name}`, hidden: section !== name });
  const [channelStatusInterval, setChannelStatusInterval] = useState<number | ''>(60);
  const channelStatusIntervalQuery = useChannelStatusInterval();
  const updateChannelStatusIntervalMutation = useUpdateChannelStatusInterval();
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
    if (aceEngineUrlQuery.data !== undefined) setAceEngineUrl(aceEngineUrlQuery.data);
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

  useEffect(() => {
    if (channelStatusIntervalQuery.data !== undefined) setChannelStatusInterval(channelStatusIntervalQuery.data);
  }, [channelStatusIntervalQuery.data]);

  const handleChannelStatusSave = () => {
    if (channelStatusInterval === '') return;
    updateChannelStatusIntervalMutation.mutate(channelStatusInterval, {
      onSuccess: () => notify(`Streams will be checked every ${channelStatusInterval} min`, 'success'),
      onError: (error) => notify(`Failed to save the stream check interval: ${getErrorMessage(error)}`, 'error'),
    });
  };

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

  const isLoading = section === 'playback' ? aceEngineUrlQuery.isLoading
    : section === 'automation' ? rescrapeIntervalQuery.isLoading || epgRefreshIntervalQuery.isLoading || channelStatusIntervalQuery.isLoading
    : section === 'links' ? addPidQuery.isLoading || appidLoading : false;

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
      <PageHeader title="Settings" subtitle="Playback, scheduled jobs, playlist links and access from this browser." actions={<Button href="/startup" variant="outlined">Startup diagnostics</Button>} />

      <Tabs value={section} onChange={(_event, value: string) => { const next = new URLSearchParams(params); next.set('tab', value); setParams(next); }} variant="scrollable" scrollButtons="auto" allowScrollButtonsMobile aria-label="Settings sections" sx={{ mb: 2 }}>
        {sections.map((name, index) => <Tab key={name} value={name} id={`settings-tab-${name}`} aria-controls={`settings-panel-${name}`} label={['Playback', 'Automation', 'Stream links', 'API access'][index]} />)}
      </Tabs>
      <Box {...panelProps('playback')}>
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
              <Chip label={acestreamStatusQuery.error ? 'Unknown' : !aceEngineUrlQuery.data ? 'Not configured' : engineOnline ? 'Online' : 'Offline'} color={acestreamStatusQuery.error ? 'default' : !aceEngineUrlQuery.data ? 'default' : engineOnline ? 'success' : 'error'} variant="outlined" sx={{ fontWeight: 600, minWidth: 90 }} />
            )}
            <Typography variant="body2" color="text.secondary">
              {acestreamStatusQuery.error
                ? `Could not check the engine: ${getErrorMessage(acestreamStatusQuery.error)}`
                : !aceEngineUrlQuery.data ? 'An engine is optional. Without one, playback and stream checks are unavailable unless a dedicated checker is configured.' : engineOnline ? acestreamStatusQuery.data?.message || 'The engine is reachable.' : 'The backend cannot reach the engine. Check its address and make sure the service is running.'}
            </Typography>
          </Stack>
          <form onSubmit={handleAceEngineUrlSubmit}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'flex-start' }}>
              <TextField
                label="Acestream Engine URL"
                size="small"
                value={aceEngineUrl}
                onChange={(e) => setAceEngineUrl(e.target.value)}
                helperText="Optional. Leave blank when no playback engine is available."
                sx={{ flex: 1, maxWidth: 480 }}
              />
              <Button type="submit" variant="contained" size="small" disabled={updateAceEngineUrlMutation.isPending || aceEngineUrl === aceEngineUrlQuery.data} sx={{ mt: 0.5 }}>
                {updateAceEngineUrlMutation.isPending ? <CircularProgress size={18} color="inherit" /> : 'Save engine URL'}
              </Button>
            </Stack>
          </form>
          <PlaybackRoutingFields />
        </Stack>
      </ContentSection>

      <ContentSection title="Players and network" description="Manage the address other devices use, remote players, media servers and tuner limits in Integrations.">
        <Button component={RouterLink} to="/integrations" variant="outlined">Manage integrations</Button>
      </ContentSection>
      </Box>
      <Box {...panelProps('automation')}>

      <ContentSection title="Stream status checks"><CheckEngineFields /></ContentSection>

      <ContentSection title="Automation" description="Background jobs run on these schedules. Changes apply right away.">
        <Stack spacing={2.5}>
          {rescrapeIntervalQuery.isError || epgRefreshIntervalQuery.isError ? <Alert severity="error">Some schedules could not be loaded. Reload before changing them.</Alert> : null}
          <IntervalField
            id="rescrape-interval"
            label="Scrape sources every (hours)"
            helper="1 to 168 hours"
            value={rescrapeInterval}
            saved={rescrapeIntervalQuery.data}
            pending={updateRescrapeIntervalMutation.isPending || rescrapeIntervalQuery.isError}
            onChange={setRescrapeInterval}
            onSave={handleRescrapeSave}
          />
          <IntervalField
            id="epg-refresh-interval"
            label="Refresh EPG every (hours)"
            helper="1 to 168 hours"
            value={epgRefreshInterval}
            saved={epgRefreshIntervalQuery.data}
            pending={updateEpgRefreshIntervalMutation.isPending || epgRefreshIntervalQuery.isError}
            onChange={setEpgRefreshInterval}
            onSave={handleEpgRefreshSave}
          />
          {channelStatusIntervalQuery.isError ? <Alert severity="error">Could not load the stream check interval. Reload to try again.</Alert> : null}
          <IntervalField
            id="channel-status-interval"
            label="Stream check interval (minutes)"
            helper="Default: 60 minutes. Channel playback also checks its sources in the background."
            max={10080}
            value={channelStatusInterval}
            saved={channelStatusIntervalQuery.data}
            pending={updateChannelStatusIntervalMutation.isPending || channelStatusIntervalQuery.isLoading || channelStatusIntervalQuery.isError}
            onChange={setChannelStatusInterval}
            onSave={handleChannelStatusSave}
          />
          <ScheduleAnchorFields />

        </Stack>
      </ContentSection>

      </Box>
      <Box {...panelProps('links')}>
      <StreamLinkFormatsSection notify={notify} />
      <ContentSection title="Player compatibility" description="Optional additions for players that require them. Changes affect generated links.">
        <Stack spacing={2}>
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
      <Button component={RouterLink} to="/playlist">Open playlist builder</Button>
      <Button component={RouterLink} to="/integrations">Manage public address</Button>
      </Box>
      <Box {...panelProps('access')}>
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

      </Box>
      <Snackbar open={feedback.open} autoHideDuration={6000} onClose={() => setFeedback((current) => ({ ...current, open: false }))}>
        <Alert onClose={() => setFeedback((current) => ({ ...current, open: false }))} severity={feedback.severity} variant="filled" sx={{ width: '100%' }}>
          {feedback.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;

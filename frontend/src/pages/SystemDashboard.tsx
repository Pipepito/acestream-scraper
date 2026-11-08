import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { Alert,Box,Button,Chip,Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import DiagnosticsDownload from '../components/DiagnosticsDownload';
import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import ScheduledJobs from '../components/overview/ScheduledJobs';
import StoragePanel from '../components/overview/StoragePanel';
import RecordingOverview from '../components/recordings/RecordingOverview';
import ServicesPanel from '../components/ServicesPanel';
import StatusLine from '../components/StatusLine';
import { useHealth } from '../hooks/useConfig';
import { useBackgroundTaskStatus } from '../hooks/useDashboard';
import { useSystemServices } from '../hooks/useSystemServices';
import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { getErrorMessage } from '../utils/errorUtils';

const REFRESH_MS = 30_000;

/** Service administration stays independent of catalogue availability. */
const SystemDashboard: React.FC = () => {
  const tUi = useUiText();
  const theme = useTheme();
  const services = useSystemServices({ refetchInterval: REFRESH_MS });
  const tasks = useBackgroundTaskStatus(REFRESH_MS);
  const health = useHealth({ refetchInterval: REFRESH_MS });

  const engine = services.data?.services?.find((s) => s.name === 'acestream');
  const attention = services.data?.services?.filter((s) => s.enabled && !s.stopped_by_user && (s.state === 'stopped' || s.state === 'unhealthy')) ?? [];
  // The engine the app talks to may live outside this container: trust the backend's probe, not the service list.
  const engineProbe = health.data?.acestream;
  const engineOnline = engineProbe ? engineProbe.status === 'online' : Boolean(engine?.running);
  const engineExternal = engineOnline && Boolean(engine) && !engine?.running;
  const engineStopped = Boolean(engine?.stopped_by_user) && !engineOnline;
  const configuredEngineUrl = health.data?.settings?.ace_engine_url;
  const engineConfigured = typeof configuredEngineUrl === 'string'
    ? Boolean(configuredEngineUrl.trim())
    : Boolean(engine?.endpoint || engine?.enabled);
  const statusUnavailable = Boolean(health.error || services.error || !health.data || !services.data || !engineProbe || (engineConfigured && !engineStopped && engineProbe.status === 'unknown'));
  const needsAttention = attention.length > 0 || (engineConfigured && !engineOnline && !engineStopped);

  const refetchAll = () => {
    void health.refetch();
    void services.refetch();
    void tasks.refetch();
  };

  const statusTone = theme.appTokens.status[needsAttention ? 'warning' : 'success'];
  const chip = statusUnavailable ? <Chip label={tUi("Status unavailable")} variant="outlined" /> : (
    <Chip
      icon={needsAttention ? <WarningAmberIcon /> : <CheckCircleOutlineIcon />}
      label={needsAttention ? tUi("Services need attention") : tUi("Services healthy")}
      variant="outlined"
      sx={{ color: statusTone.text, bgcolor: statusTone.bg, borderColor: statusTone.border, '& .MuiChip-icon': { color: statusTone.icon } }}
    />
  );

  return (
    <Box>
      <PageHeader title={tUi("System status")} subtitle={tUi("Services, storage and scheduled maintenance.")} actions={chip} />

      <Box component="nav" aria-label={tUi("System tools")} sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
        <Button component={RouterLink} to="/system/runtime">{tUi("Advanced connection settings")}</Button>
        <Button component={RouterLink} to="/changelog">{tUi("Changelog")}</Button>
      </Box>

      <StatusLine
        aria-label={tUi("System status summary")}
        items={[
          {
            label: uiText("Engine"),
            value: statusUnavailable ? uiText("Unavailable") : engineOnline ? (engineExternal ? 'online (external)' : engine?.version ?? 'online') : !engineConfigured ? 'not configured' : engineStopped ? 'stopped by you' : 'not reachable',
            tone: statusUnavailable ? 'default' : engineOnline ? 'success' : !engineConfigured || engineStopped ? 'default' : 'error',
          },
          { label: uiText("Application version"), value: health.error ? uiText("Unavailable") : health.data?.version ?? 'Loading…' },
        ]}
        action={
          <Button size="small" variant="outlined" onClick={refetchAll}>
            {tUi("Refresh")}</Button>
        }
      />

      {health.error ? <Alert severity="warning" sx={{ mb: 2 }} action={<Button color="inherit" onClick={() => void health.refetch()}>{tUi("Retry health")}</Button>}>
        {tUi("Could not load system health:")}{' '}{getErrorMessage(health.error)}
      </Alert> : !health.data ? <Typography role="status">{tUi("Checking system health…")}</Typography> : null}

      {!services.error && attention.length > 0 ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {attention.map((s) => tUi("{{value0}}: {{value1}}", { value0: s.label, value1: s.message })).join(' · ')}
        </Alert>
      ) : null}

      <ContentSection title={tUi("Services")} description={tUi("What this image ships, what is switched on, and whether each service answers. Start, stop or restart the engine without recreating the container.")}>
        <ServicesPanel pollIntervalMs={REFRESH_MS} />
        <DiagnosticsDownload />
      </ContentSection>

      <RecordingOverview system />
      <StoragePanel />

      <Box id="scheduled-jobs" sx={{ scrollMarginTop: 90 }}><ContentSection actions={<Button component={RouterLink} to="/settings?tab=automation">{tUi("Edit schedules")}</Button>} title={tUi("Scheduled jobs")} description={tUi("What ran last, what it did, and when it runs again.")}>
        {tasks.error ? (
          <Alert severity="error" action={<Button color="inherit" onClick={() => void tasks.refetch()}>{tUi("Retry jobs")}</Button>}>{tUi("Could not load the scheduler status:")}{' '}{getErrorMessage(tasks.error)}</Alert>
        ) : !tasks.data ? <Typography role="status">{tUi("Loading scheduled jobs…")}</Typography> : (
          <ScheduledJobs tasks={tasks.data ?? []} />
        )}
      </ContentSection></Box>
    </Box>
  );
};

export default SystemDashboard;

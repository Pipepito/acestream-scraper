import RecordingOverview from '../components/recordings/RecordingOverview';
import { Link as RouterLink } from 'react-router-dom';
import React from 'react';
import { useTheme } from '@mui/material/styles';
import { Alert, Box, Button, Chip, Typography } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import ServicesPanel from '../components/ServicesPanel';
import DiagnosticsDownload from '../components/DiagnosticsDownload';
import StatusLine from '../components/StatusLine';
import StoragePanel from '../components/overview/StoragePanel';
import ScheduledJobs from '../components/overview/ScheduledJobs';
import { useSystemServices } from '../hooks/useSystemServices';
import { useHealth } from '../hooks/useConfig';
import { useBackgroundTaskStatus } from '../hooks/useDashboard';
import { normalizeApiError } from '../services/apiErrors';

const REFRESH_MS = 30_000;

/** Service administration stays independent of catalogue availability. */
const SystemDashboard: React.FC = () => {
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
  const chip = statusUnavailable ? <Chip label="Status unavailable" variant="outlined" /> : (
    <Chip
      icon={needsAttention ? <WarningAmberIcon /> : <CheckCircleOutlineIcon />}
      label={needsAttention ? 'Services need attention' : 'Services healthy'}
      variant="outlined"
      sx={{ color: statusTone.text, bgcolor: statusTone.bg, borderColor: statusTone.border, '& .MuiChip-icon': { color: statusTone.icon } }}
    />
  );

  return (
    <Box>
      <PageHeader title="System status" subtitle="Services, storage and scheduled maintenance." actions={chip} />

      <StatusLine
        aria-label="System status summary"
        items={[
          {
            label: 'Engine',
            value: statusUnavailable ? 'Unavailable' : engineOnline ? (engineExternal ? 'online (external)' : engine?.version ?? 'online') : !engineConfigured ? 'not configured' : engineStopped ? 'stopped by you' : 'not reachable',
            tone: statusUnavailable ? 'default' : engineOnline ? 'success' : !engineConfigured || engineStopped ? 'default' : 'error',
          },
          { label: 'Application version', value: health.error ? 'Unavailable' : health.data?.version ?? 'Loading…' },
        ]}
        action={
          <Button size="small" variant="outlined" onClick={refetchAll}>
            Refresh
          </Button>
        }
      />

      {health.error ? <Alert severity="warning" sx={{ mb: 2 }} action={<Button color="inherit" onClick={() => void health.refetch()}>Retry health</Button>}>
        Could not load system health: {normalizeApiError(health.error).message}
      </Alert> : !health.data ? <Typography role="status">Checking system health…</Typography> : null}

      {!services.error && attention.length > 0 ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {attention.map((s) => `${s.label}: ${s.message}`).join(' · ')}
        </Alert>
      ) : null}

      <ContentSection title="Services" description="What this image ships, what is switched on, and whether each service answers. Start, stop or restart the engine without recreating the container.">
        <ServicesPanel pollIntervalMs={REFRESH_MS} />
        <DiagnosticsDownload />
      </ContentSection>

      <RecordingOverview system />
      <StoragePanel />

      <Box id="scheduled-jobs" sx={{ scrollMarginTop: 90 }}><ContentSection actions={<Button component={RouterLink} to="/settings?tab=automation">Edit schedules</Button>} title="Scheduled jobs" description="What ran last, what it did, and when it runs again.">
        {tasks.error ? (
          <Alert severity="error" action={<Button color="inherit" onClick={() => void tasks.refetch()}>Retry jobs</Button>}>Could not load the scheduler status: {normalizeApiError(tasks.error).message}</Alert>
        ) : !tasks.data ? <Typography role="status">Loading scheduled jobs…</Typography> : (
          <ScheduledJobs tasks={tasks.data ?? []} />
        )}
      </ContentSection></Box>
    </Box>
  );
};

export default SystemDashboard;

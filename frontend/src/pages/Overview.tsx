import React from 'react';
import { Alert, Box, Button, Chip, CircularProgress } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import ServicesPanel from '../components/ServicesPanel';
import StatusLine from '../components/StatusLine';
import InventoryTotals from '../components/overview/InventoryTotals';
import ScheduledJobs from '../components/overview/ScheduledJobs';
import { useSystemServices } from '../hooks/useSystemServices';
import { useHealth, useStats, useTvChannelStats } from '../hooks/useConfig';
import { useBackgroundTaskStatus } from '../hooks/useDashboard';
import { formatRelativeTime } from '../utils/format';
import { normalizeApiError } from '../services/apiErrors';

const REFRESH_MS = 30_000;

/**
 * The landing page: is it running, what is loaded, what the scheduler did and
 * will do. Everything shown is a measured fact; nothing is prose.
 */
const Overview: React.FC = () => {
  const services = useSystemServices({ refetchInterval: REFRESH_MS });
  const stats = useStats({ refetchInterval: REFRESH_MS });
  const tvStats = useTvChannelStats({ refetchInterval: REFRESH_MS });
  const tasks = useBackgroundTaskStatus(REFRESH_MS);
  const health = useHealth({ refetchInterval: REFRESH_MS });

  const engine = services.data?.services.find((s) => s.name === 'acestream');
  const attention = services.data?.services.filter((s) => s.enabled && (s.state === 'stopped' || s.state === 'unhealthy')) ?? [];
  // The engine the app talks to may live outside this container: trust the backend's probe, not the service list.
  const engineProbe = health.data?.acestream;
  const engineOnline = engineProbe ? engineProbe.status === 'online' : Boolean(engine?.running);
  const engineExternal = engineOnline && Boolean(engine) && !engine?.running;
  const needsAttention = attention.length > 0 || !engineOnline;

  const lastScrape = tasks.data?.find((t) => t.task_name === 'url_scraping')?.last_run ?? null;
  const lastEpg = tasks.data?.find((t) => t.task_name === 'epg_refresh')?.last_run ?? null;

  const refetchAll = () => {
    void health.refetch();
    void services.refetch();
    void stats.refetch();
    void tvStats.refetch();
    void tasks.refetch();
  };

  if (services.isLoading || stats.isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }} role="status" aria-label="Loading overview">
        <CircularProgress />
      </Box>
    );
  }

  if (stats.error || services.error) {
    return (
      <Box>
        <PageHeader title="Overview" />
        <Alert
          severity="error"
          action={
            <Button color="inherit" size="small" onClick={refetchAll}>
              Retry
            </Button>
          }
        >
          Could not load the overview: {normalizeApiError(stats.error ?? services.error).message}
        </Alert>
      </Box>
    );
  }

  const chip = needsAttention ? (
    <Chip icon={<WarningAmberIcon />} color="warning" label="ATTENTION" sx={{ fontSize: '1rem', py: 2, px: 1 }} />
  ) : (
    <Chip icon={<CheckCircleOutlineIcon />} color="success" label="HEALTHY" sx={{ fontSize: '1rem', py: 2, px: 1 }} />
  );

  return (
    <Box>
      <PageHeader title="Overview" subtitle="Is it running, what is loaded, and what runs next." actions={chip} />

      <StatusLine
        aria-label="Overview summary"
        items={[
          {
            label: 'Engine',
            value: engineOnline ? (engineExternal ? 'online (external)' : engine?.version ?? 'online') : 'not reachable',
            tone: engineOnline ? 'success' : 'error',
          },
          ...(stats.data
            ? [{ label: 'Streams', value: `${stats.data.channels.total}, ${stats.data.channels.online} online` }]
            : []),
          ...(tvStats.data ? [{ label: 'TV channels', value: String(tvStats.data.total) }] : []),
          ...(stats.data ? [{ label: 'Guide', value: `${stats.data.epg.channels} channels` }] : []),
          { label: 'Last scrape', value: formatRelativeTime(lastScrape), tone: lastScrape ? 'default' : 'warning' },
          { label: 'Last EPG refresh', value: formatRelativeTime(lastEpg), tone: lastEpg ? 'default' : 'warning' },
        ]}
        action={
          <Button size="small" variant="outlined" onClick={refetchAll}>
            Refresh
          </Button>
        }
      />

      {attention.length > 0 ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {attention.map((s) => `${s.label}: ${s.message}`).join(' · ')}
        </Alert>
      ) : null}

      <ContentSection title="Services" description="What this image ships, what is switched on, and whether each service answers. Restart a supervised service without recreating the container.">
        <ServicesPanel pollIntervalMs={REFRESH_MS} />
      </ContentSection>

      <ContentSection title="Inventory" description="What is loaded right now.">
        {stats.data ? <InventoryTotals stats={stats.data} tvStats={tvStats.data} /> : null}
      </ContentSection>

      <ContentSection title="Scheduled jobs" description="What ran last, what it did, and when it runs again.">
        {tasks.error ? (
          <Alert severity="error">Could not load the scheduler status: {normalizeApiError(tasks.error).message}</Alert>
        ) : (
          <ScheduledJobs tasks={tasks.data ?? []} />
        )}
      </ContentSection>
    </Box>
  );
};

export default Overview;

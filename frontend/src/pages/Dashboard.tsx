import React, { useState } from 'react';
import {
  Typography,
  Box,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Pagination,
  Switch,
  FormControlLabel,
  Button,
  Stack,
  List,
  ListItem,
  ListItemText,
  Divider,
  Paper,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import Snackbar from '@mui/material/Snackbar';
import { Link as RouterLink } from 'react-router-dom';
import {
  useRecentActivity,
  useBackgroundTaskStatus,
  useActiveStreams,
  useWarpStatus,
  useDashboardConfig,
  useUpdateDashboardConfig,
} from '../hooks/useDashboard';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

interface ActivityEntry {
  id: number | string;
  message: string;
  type: string;
  timestamp: string;
  user?: string;
  details?: unknown;
}

interface ActivityResponse {
  results: ActivityEntry[];
  total_pages: number;
}

interface ActivityApiResponse {
  results?: ActivityEntry[];
  items?: ActivityEntry[];
  total_pages?: number;
  total?: number;
  page_size?: number;
}

interface BackgroundTask {
  id?: string;
  task_name?: string;
  last_run?: string;
  next_run?: string;
  status?: string;
  last_error?: string | null;
}

interface DashboardConfig {
  retention_days: number;
  auto_refresh_interval: number;
}

const Dashboard: React.FC = () => {
  const { data: dashboardConfig, isLoading: configLoading } = useDashboardConfig();
  const updateDashboardConfig = useUpdateDashboardConfig();
  const [retentionDays, setRetentionDays] = useState<number>(dashboardConfig?.retention_days ?? 7);
  const [activityType, setActivityType] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(() => {
    const stored = localStorage.getItem('dashboard-auto-refresh');
    return stored === null ? true : stored === 'true';
  });
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(dashboardConfig?.auto_refresh_interval ?? 60);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });

  React.useEffect(() => {
    if (dashboardConfig) {
      const typedConfig = dashboardConfig as DashboardConfig;
      setRetentionDays(typedConfig.retention_days);
      setAutoRefreshInterval(typedConfig.auto_refresh_interval);
    }
  }, [dashboardConfig]);

  const [activityPage, setActivityPage] = useState(1);
  const {
    data: activityRaw,
    isLoading: activityLoading,
    error: activityError,
    refetch: refetchActivity,
  } = useRecentActivity({ days: retentionDays, type: activityType, page: activityPage, page_size: 10 });
  const {
    data: backgroundRaw,
    isLoading: tasksLoading,
    error: tasksError,
    refetch: refetchTasks,
  } = useBackgroundTaskStatus();
  const { data: streams, isLoading: streamsLoading, error: streamsError, refetch: refetchStreams } = useActiveStreams();
  const { data: warp, isLoading: warpLoading, error: warpError, refetch: refetchWarp } = useWarpStatus();

  const rawActivity = (activityRaw as ActivityApiResponse | undefined) ?? {};
  const activityResults = rawActivity.results ?? rawActivity.items ?? [];
  const activityTotalPages = rawActivity.total_pages ?? Math.max(1, Math.ceil((rawActivity.total ?? activityResults.length) / (rawActivity.page_size ?? 10)));
  const activityData: ActivityResponse = { results: activityResults, total_pages: activityTotalPages };
  const backgroundTasks = (backgroundRaw as BackgroundTask[] | undefined) ?? [];

  React.useEffect(() => {
    if (!autoRefresh) {
      return;
    }

    const interval = setInterval(() => {
      refetchActivity();
      refetchTasks();
      refetchStreams();
      refetchWarp();
    }, autoRefreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, autoRefreshInterval, refetchActivity, refetchTasks, refetchStreams, refetchWarp]);

  const handleRetentionChange = (event: SelectChangeEvent<number>) => {
    const value = Number(event.target.value);
    setRetentionDays(value);
    updateDashboardConfig.mutate(
      { retention_days: value },
      {
        onSuccess: () => setSnackbar({ open: true, message: 'Retention updated', severity: 'success' }),
        onError: () => setSnackbar({ open: true, message: 'Failed to update retention', severity: 'error' }),
      }
    );
  };

  const handleActivityTypeChange = (event: SelectChangeEvent<string>) => {
    setActivityType(event.target.value);
    setActivityPage(1);
  };

  const handleAutoRefreshIntervalChange = (event: SelectChangeEvent<number>) => {
    const value = Number(event.target.value);
    setAutoRefreshInterval(value);
    updateDashboardConfig.mutate(
      { auto_refresh_interval: value },
      {
        onSuccess: () => setSnackbar({ open: true, message: 'Auto-refresh interval updated', severity: 'success' }),
        onError: () => setSnackbar({ open: true, message: 'Failed to update auto-refresh interval', severity: 'error' }),
      }
    );
  };

  const handleAutoRefreshToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAutoRefresh(event.target.checked);
    localStorage.setItem('dashboard-auto-refresh', String(event.target.checked));
  };

  if (configLoading || activityLoading || tasksLoading || streamsLoading || warpLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (activityError || tasksError || streamsError || warpError) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {activityError ? `Activity error: ${String(activityError)}` : ''}
          {tasksError ? ` Task error: ${String(tasksError)}` : ''}
          {streamsError ? ` Streams error: ${String(streamsError)}` : ''}
          {warpError ? ` Warp error: ${String(warpError)}` : ''}
        </Alert>
        <Button
          variant="contained"
          onClick={() => {
            refetchActivity();
            refetchTasks();
            refetchStreams();
            refetchWarp();
          }}
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Check readiness and move to the next workflow."
        primaryActions={
          <Stack component="nav" aria-label="Dashboard primary actions" direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ width: '100%' }}>
            <Button component={RouterLink} to="/epg" variant="contained">
              EPG
            </Button>
            <Button component={RouterLink} to="/scraper" variant="outlined">
              Open Scraper
            </Button>
            <Button component={RouterLink} to="/acestream-channels" variant="outlined">
              Channels
            </Button>
          </Stack>
        }
      />

      <ContentSection title="Dashboard tools" description="Filter activity and adjust refresh behavior.">
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} flexWrap="wrap">
          <FormControl sx={{ minWidth: 140 }}>
            <InputLabel>Retention</InputLabel>
            <Select value={retentionDays} label="Retention" onChange={handleRetentionChange}>
              {[0, 1, 3, 7, 14, 30].map((days) => (
                <MenuItem key={days} value={days}>
                  {days} days
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 180 }}>
            <InputLabel>Auto-Refresh</InputLabel>
            <Select value={autoRefreshInterval} label="Auto-Refresh" onChange={handleAutoRefreshIntervalChange}>
              {[10, 30, 60, 120, 300, 600].map((seconds) => (
                <MenuItem key={seconds} value={seconds}>
                  {seconds} sec
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl sx={{ minWidth: 180 }}>
            <InputLabel>Activity Type</InputLabel>
            <Select value={activityType} label="Activity Type" onChange={handleActivityTypeChange}>
              <MenuItem value="">All</MenuItem>
              <MenuItem value="scrape">Scrape</MenuItem>
              <MenuItem value="epg">EPG</MenuItem>
              <MenuItem value="system">System</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel control={<Switch checked={autoRefresh} onChange={handleAutoRefreshToggle} />} label="Auto-Refresh" />
        </Stack>
      </ContentSection>

      <ContentSection title="System readiness" description="Check the current state, then choose the next workflow.">
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Stack spacing={2}>
            <Alert severity={(warp as { error?: string | null } | undefined)?.error ? 'warning' : 'success'}>
              {(warp as { error?: string | null; status?: string } | undefined)?.error
                ? `Attention needed: WARP reports ${(warp as { status?: string } | undefined)?.status ?? 'unknown status'}. ${(warp as { error?: string }).error}`
                : `Protected connection active: WARP is ${(warp as { status?: string } | undefined)?.status ?? 'unknown'}.`}
            </Alert>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} divider={<Divider flexItem orientation="vertical" sx={{ display: { xs: 'none', md: 'block' } }} />}>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="sectionTitle">Stream capacity</Typography>
                <Typography variant="h4" sx={{ mt: 1 }}>
                  {(streams as { count?: number } | undefined)?.count ?? 0}
                </Typography>
                <Typography variant="helperText" sx={{ mt: 1 }}>
                  {(streams as { count?: number } | undefined)?.count ?? 0} streams available right now from{' '}
                  {(streams as { source?: string } | undefined)?.source ?? 'N/A'}.
                </Typography>
              </Box>

              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="sectionTitle">Protected routing</Typography>
                <Typography variant="body1" sx={{ mt: 1, fontWeight: 600 }}>
                  WARP status: {(warp as { status?: string } | undefined)?.status ?? 'N/A'}
                </Typography>
                <Typography variant="helperText" sx={{ mt: 1 }}>
                  {(warp as { error?: string | null } | undefined)?.error
                    ? `Traffic protection needs review before running more tasks. ${String((warp as { error?: string }).error)}`
                    : 'Protected connection active so scraper and EPG jobs can keep using the routed path.'}
                </Typography>
              </Box>

              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="sectionTitle">Scheduler follow-through</Typography>
                <Typography variant="h4" sx={{ mt: 1 }}>
                  {backgroundTasks.length}
                </Typography>
                <Typography variant="helperText" sx={{ mt: 1 }}>
                  Latest run: {backgroundTasks[0]?.last_run || 'N/A'}.
                </Typography>
              </Box>
            </Stack>
          </Stack>
        </Paper>
      </ContentSection>

      <ContentSection title="Recent Activity">
        <List>
          {activityData.results.length > 0 ? (
            activityData.results.map((entry) => (
              <React.Fragment key={entry.id}>
                <ListItem alignItems="flex-start">
                  <ListItemText
                    primary={entry.message}
                    secondary={
                      <>
                        <Typography component="span" variant="body2" color="text.secondary">
                          {entry.type} - {new Date(entry.timestamp).toLocaleString()}
                          {entry.user ? ` - ${entry.user}` : ''}
                        </Typography>
                        {entry.details ? (
                          <Box component="span" sx={{ display: 'block', mt: 0.5, fontSize: '0.82rem', color: 'text.secondary' }}>
                            {JSON.stringify(entry.details)}
                          </Box>
                        ) : null}
                      </>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))
          ) : (
            <ListItem>
              <ListItemText primary="No recent activity data available" />
            </ListItem>
          )}
        </List>
        {activityData.total_pages > 1 ? (
          <Box display="flex" justifyContent="center" mt={2}>
            <Pagination count={activityData.total_pages} page={activityPage} onChange={(_, nextPage) => setActivityPage(nextPage)} color="primary" />
          </Box>
        ) : null}
      </ContentSection>

      <ContentSection title="Background Tasks">
        <List>
          {backgroundTasks.length > 0 ? (
            backgroundTasks.map((task) => (
              <React.Fragment key={task.task_name || task.id}>
                <ListItem alignItems="flex-start">
                  <ListItemText
                    primary={task.task_name || task.id || 'Unnamed task'}
                    secondary={
                      <>
                        <Typography component="span" variant="body2" color="text.secondary">
                          Last run {task.last_run || 'N/A'} - Next run {task.next_run || 'N/A'} - Status {task.status || 'N/A'}
                        </Typography>
                        {task.last_error ? (
                          <Box component="span" sx={{ display: 'block', mt: 0.5, fontSize: '0.82rem', color: 'error.main' }}>
                            Error: {task.last_error}
                          </Box>
                        ) : null}
                      </>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))
          ) : (
            <ListItem>
              <ListItemText primary="No background task data available" />
            </ListItem>
          )}
        </List>
      </ContentSection>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3500}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;

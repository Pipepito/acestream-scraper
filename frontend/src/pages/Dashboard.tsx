import React, { useState } from 'react';
import {
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
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
  Chip,
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

  const activityData = (activityRaw as ActivityResponse | undefined) ?? { results: [], total_pages: 1 };
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
        subtitle="Track operational status, recent activity, and background jobs."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button component={RouterLink} to="/scraper" variant="outlined">
              Open Scraper
            </Button>
            <Button component={RouterLink} to="/acestream-channels" variant="outlined">
              Channels
            </Button>
            <Button component={RouterLink} to="/epg" variant="contained">
              EPG
            </Button>
          </Stack>
        }
      />

      <ContentSection title="Controls" description="Tune refresh cadence and activity retention.">
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

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Streams
              </Typography>
              <Typography variant="h4">{(streams as { count?: number } | undefined)?.count ?? 0}</Typography>
              <Typography sx={{ mt: 1 }} color="text.secondary">
                Source: {(streams as { source?: string } | undefined)?.source ?? 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                WARP Status
              </Typography>
              <Typography variant="h6">{(warp as { status?: string } | undefined)?.status ?? 'N/A'}</Typography>
              {(warp as { error?: string | null } | undefined)?.error ? (
                <Chip sx={{ mt: 1 }} color="warning" label={`Error: ${(warp as { error?: string }).error}`} />
              ) : null}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Background Tasks
              </Typography>
              <Typography variant="h4">{backgroundTasks.length}</Typography>
              <Typography sx={{ mt: 1 }} color="text.secondary">
                Latest run: {backgroundTasks[0]?.last_run || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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
                          {entry.type} | {new Date(entry.timestamp).toLocaleString()}
                          {entry.user ? ` | User: ${entry.user}` : ''}
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
                          Last run: {task.last_run || 'N/A'} | Next run: {task.next_run || 'N/A'} | Status: {task.status || 'N/A'}
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
        message={snackbar.message}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ContentProps={{
          style: {
            backgroundColor: snackbar.severity === 'success' ? '#2e7d32' : '#d32f2f',
            color: '#fff',
          },
        }}
      />
    </Box>
  );
};

export default Dashboard;


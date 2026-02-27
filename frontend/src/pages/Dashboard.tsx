import React, { useState } from 'react';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Pagination,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  PlayArrow,
  Update,
  TvOutlined,
  LinkOutlined,
  CheckCircleOutline,
  ErrorOutline
} from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import { useRecentActivity, useBackgroundTaskStatus, useActiveStreams, useWarpStatus, useDashboardConfig, useUpdateDashboardConfig } from '../hooks/useDashboard';
import type { SelectChangeEvent } from '@mui/material';
import Snackbar from '@mui/material/Snackbar';

const Dashboard: React.FC = () => {
  // Dashboard config state
  const { data: dashboardConfig, isLoading: configLoading } = useDashboardConfig();
  const updateDashboardConfig = useUpdateDashboardConfig();
  const [retentionDays, setRetentionDays] = useState<number>(dashboardConfig?.retention_days ?? 7);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(() => {
    const stored = localStorage.getItem('dashboard-auto-refresh');
    return stored === null ? true : stored === 'true';
  });
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(dashboardConfig?.auto_refresh_interval ?? 60);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success'|'error' }>({ open: false, message: '', severity: 'success' });

  // Sync local state with dashboardConfig
  React.useEffect(() => {
    if (dashboardConfig) {
      setRetentionDays(dashboardConfig.retention_days);
      setAutoRefreshInterval(dashboardConfig.auto_refresh_interval);
    }
  }, [dashboardConfig]);

  // Activity log state
  const [activityPage, setActivityPage] = useState(1);
  const [activityType, setActivityType] = useState<string>('');
  const { data: activityData, isLoading: activityLoading, error: activityError, refetch: refetchActivity } = useRecentActivity({ days: retentionDays, type: activityType, page: activityPage, page_size: 10 });

  // Background tasks, streams, warp
  const { data: backgroundTasks, isLoading: tasksLoading, error: tasksError, refetch: refetchTasks } = useBackgroundTaskStatus();
  const { data: streams, isLoading: streamsLoading, error: streamsError, refetch: refetchStreams } = useActiveStreams();
  const { data: warp, isLoading: warpLoading, error: warpError, refetch: refetchWarp } = useWarpStatus();

  // Auto-refresh logic (simple interval)
  React.useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      refetchActivity();
      refetchTasks();
      refetchStreams();
      refetchWarp();
    }, autoRefreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefresh, autoRefreshInterval, refetchActivity, refetchTasks, refetchStreams, refetchWarp]);

  // Handlers
  const handleRetentionChange = (e: SelectChangeEvent<number>) => {
    const value = Number(e.target.value);
    setRetentionDays(value);
    updateDashboardConfig.mutate(
      { retention_days: value },
      {
        onSuccess: () => setSnackbar({ open: true, message: 'Retention updated', severity: 'success' }),
        onError: () => setSnackbar({ open: true, message: 'Failed to update retention', severity: 'error' })
      }
    );
  };
  const handleAutoRefreshIntervalChange = (e: SelectChangeEvent<number>) => {
    const value = Number(e.target.value);
    setAutoRefreshInterval(value);
    updateDashboardConfig.mutate(
      { auto_refresh_interval: value },
      {
        onSuccess: () => setSnackbar({ open: true, message: 'Auto-refresh interval updated', severity: 'success' }),
        onError: () => setSnackbar({ open: true, message: 'Failed to update auto-refresh interval', severity: 'error' })
      }
    );
  };
  const handleAutoRefreshToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAutoRefresh(e.target.checked);
    localStorage.setItem('dashboard-auto-refresh', String(e.target.checked));
  };

  // Loading and error states
  if (configLoading || activityLoading || tasksLoading || streamsLoading || warpLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }
  if (activityError || tasksError || streamsError || warpError) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {activityError ? `Activity error: ${activityError.toString()}` : ''}
          {tasksError ? ` Task error: ${tasksError.toString()}` : ''}
          {streamsError ? ` Streams error: ${streamsError.toString()}` : ''}
          {warpError ? ` Warp error: ${warpError.toString()}` : ''}
        </Alert>
        <Button variant="contained" onClick={() => { refetchActivity(); refetchTasks(); refetchStreams(); refetchWarp(); }}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      {/* Controls */}
      <Box sx={{ mb: 3 }}>
        <FormControl sx={{ mr: 2, minWidth: 120 }}>
          <InputLabel>Retention</InputLabel>
          <Select value={retentionDays} label="Retention" onChange={handleRetentionChange}>
            {[0, 1, 3, 7, 14, 30].map(d => <MenuItem key={d} value={d}>{d} days</MenuItem>)}
          </Select>
        </FormControl>
        <FormControl sx={{ mr: 2, minWidth: 160 }}>
          <InputLabel>Auto-Refresh</InputLabel>
          <Select value={autoRefreshInterval} label="Auto-Refresh" onChange={handleAutoRefreshIntervalChange}>
            {[10, 30, 60, 120, 300, 600].map(s => <MenuItem key={s} value={s}>{s} sec</MenuItem>)}
          </Select>
        </FormControl>
        <FormControlLabel control={<Switch checked={autoRefresh} onChange={handleAutoRefreshToggle} />} label="Auto-Refresh" />
      </Box>
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Streams
              </Typography>
              <Typography variant="h4" component="div">
                {streams?.count ?? 0}
              </Typography>
              <Typography sx={{ mt: 1 }} color="textSecondary">
                Source: {streams?.source ?? 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Warp Status
              </Typography>
              <Typography variant="h6" component="div">
                {warp?.status ?? 'N/A'}
              </Typography>
              <Typography sx={{ mt: 1 }} color="textSecondary">
                {warp?.error ? `Error: ${warp.error}` : ''}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        {/* Add more cards as needed */}
      </Grid>
      {/* Activity Log */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Recent Activity
        </Typography>
        <List>
          {activityData?.results?.length > 0 ? activityData.results.map((entry: any) => (
            <React.Fragment key={entry.id}>
              <ListItem alignItems="flex-start">
                <ListItemText
                  primary={entry.message}
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="textSecondary">
                        {entry.type} | {new Date(entry.timestamp).toLocaleString()} {entry.user ? `| User: ${entry.user}` : ''}
                      </Typography>
                      {entry.details && (
                        <Box component="span" sx={{ ml: 1, fontSize: '0.9em', color: 'text.secondary' }}>
                          {JSON.stringify(entry.details)}
                        </Box>
                      )}
                    </>
                  }
                />
              </ListItem>
              <Divider />
            </React.Fragment>
          )) : (
            <ListItem>
              <ListItemText primary="No recent activity data available" />
            </ListItem>
          )}
        </List>
        {/* Pagination */}
        {activityData?.total_pages > 1 && (
          <Box display="flex" justifyContent="center" mt={2}>
            <Pagination
              count={activityData.total_pages}
              page={activityPage}
              onChange={(_, page) => setActivityPage(page)}
              color="primary"
            />
          </Box>
        )}
      </Paper>
      {/* Background Tasks */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Background Tasks
        </Typography>
        <List>
          {Array.isArray(backgroundTasks) && backgroundTasks.length > 0 ? backgroundTasks.map((task: any) => (
            <React.Fragment key={task.task_name || task.id}>
              <ListItem alignItems="flex-start">
                <ListItemText
                  primary={task.task_name || task.id}
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="textSecondary">
                        Last run: {task.last_run || 'N/A'} | Next run: {task.next_run || 'N/A'} | Status: {task.status || 'N/A'}
                      </Typography>
                      {task.last_error && (
                        <Box component="span" sx={{ ml: 1, color: 'error.main', fontSize: '0.9em' }}>
                          Error: {task.last_error}
                        </Box>
                      )}
                      {task.last_result && (
                        <Box component="span" sx={{ ml: 1, fontSize: '0.9em', color: 'text.secondary' }}>
                          Result: {JSON.stringify(task.last_result)}
                        </Box>
                      )}
                    </>
                  }
                />
              </ListItem>
              <Divider />
            </React.Fragment>
          )) : (
            <ListItem>
              <ListItemText primary="No background task data available" />
            </ListItem>
          )}
        </List>
      </Paper>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ContentProps={{
          style: { backgroundColor: snackbar.severity === 'success' ? '#43a047' : '#d32f2f', color: '#fff' }
        }}
      />
    </Box>
  );
};

export default Dashboard;

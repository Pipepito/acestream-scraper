import React from 'react';
import {
  Box,
  Typography,
  Divider,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
} from '@mui/material';
import { useHealth, useStats } from '../hooks/useConfig';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const Health: React.FC = () => {
  // Queries
  const { data: healthData, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth({
    refetchInterval: 60000 // Refetch every minute
  });

  const { data: statsData, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useStats({
    refetchInterval: 60000 // Refetch every minute
  });

  // Helper function to render health status
  const renderHealthStatus = () => {
    if (!healthData) return null;

    const { status } = healthData;
    let icon;
    let color;

    switch (status) {
      case 'healthy':
        icon = <CheckCircleOutlineIcon />;
        color = 'success';
        break;
      case 'degraded':
        icon = <WarningAmberIcon />;
        color = 'warning';
        break;
      default:
        icon = <ErrorOutlineIcon />;
        color = 'error';
    }

    return (
      <Chip
        icon={icon}
        label={status.toUpperCase()}
        color={color as any}
        sx={{ fontSize: '1rem', py: 2, px: 1 }}
      />
    );
  };

  // Render component state
  if (healthLoading || statsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (healthError || statsError) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {healthError ? `Health check error: ${healthError.toString()}` : ''}
          {statsError ? `Stats error: ${statsError.toString()}` : ''}
        </Alert>
        <Button variant="contained" onClick={() => {
          refetchHealth();
          refetchStats();
        }}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="Health"
        subtitle="Check system readiness, confirm engine connectivity, and review core service totals."
        actions={renderHealthStatus()}
      />

      <ContentSection
        title="Status overview"
        description="Start here to see whether the service is healthy and what needs attention right now."
        actions={
          <Button variant="outlined" onClick={() => { refetchHealth(); refetchStats(); }}>
            Refresh status
          </Button>
        }
      >
        <Stack spacing={2}>
          <Alert severity={healthData?.status === 'healthy' ? 'success' : healthData?.status === 'degraded' ? 'warning' : 'error'}>
            {healthData?.status ? `${healthData.status.toUpperCase()} · ${healthData.acestream.message}` : 'Status unknown'}
          </Alert>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                <List disablePadding>
                  <ListItem disableGutters secondaryAction={<Chip label={healthData?.acestream.status.toUpperCase()} color={healthData?.acestream.status === 'online' ? 'success' : healthData?.acestream.status === 'offline' ? 'error' : 'warning'} size="small" />}>
                    <ListItemText primary="Acestream Engine" secondary={healthData?.acestream.message || 'Status unknown'} />
                  </ListItem>
                  <Divider component="li" sx={{ my: 1.5 }} />
                  <ListItem disableGutters>
                    <ListItemText primary="Software Version" secondary={healthData?.version || 'Unknown'} />
                  </ListItem>
                </List>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>Configuration snapshot</Typography>
                <List dense disablePadding>
                  {healthData?.settings && Object.entries(healthData.settings).map(([key, value]) => (
                    <React.Fragment key={key}>
                      <ListItem disableGutters>
                        <ListItemText primary={key} secondary={value} />
                      </ListItem>
                      <Divider component="li" />
                    </React.Fragment>
                  ))}
                </List>
              </Paper>
            </Grid>
          </Grid>
        </Stack>
      </ContentSection>

      <ContentSection title="System totals" description="Review channel, URL, and EPG totals without digging into separate cards.">
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>Channel statistics</Typography>
              {statsData ? (
                <List dense disablePadding>
                  <ListItem disableGutters><ListItemText primary="Total Channels" secondary={statsData.channels.total.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Online Channels" secondary={statsData.channels.online.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Offline Channels" secondary={statsData.channels.offline.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Unknown Status" secondary={statsData.channels.unknown.toString()} /></ListItem>
                </List>
              ) : <Typography color="text.secondary">No channel statistics available</Typography>}
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>URL statistics</Typography>
              {statsData ? (
                <List dense disablePadding>
                  <ListItem disableGutters><ListItemText primary="Total URLs" secondary={statsData.urls.total.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Active URLs" secondary={statsData.urls.active.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Error URLs" secondary={statsData.urls.error.toString()} /></ListItem>
                </List>
              ) : <Typography color="text.secondary">No URL statistics available</Typography>}
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>EPG statistics</Typography>
              {statsData ? (
                <List dense disablePadding>
                  <ListItem disableGutters><ListItemText primary="EPG Sources" secondary={statsData.epg.sources.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="EPG Channels" secondary={statsData.epg.channels.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="EPG Programs" secondary={statsData.epg.programs.toString()} /></ListItem>
                </List>
              ) : <Typography color="text.secondary">No EPG statistics available</Typography>}
            </Paper>
          </Grid>
        </Grid>
      </ContentSection>
    </Box>
  );
};

export default Health;

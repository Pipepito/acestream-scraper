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
import { alpha, useTheme } from '@mui/material/styles';

const Health: React.FC = () => {
  const theme = useTheme();
  // Queries
  const { data: healthData, isLoading: healthLoading, error: healthError, refetch: refetchHealth } = useHealth({
    refetchInterval: 60000 // Refetch every minute
  });

  const { data: statsData, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useStats({
    refetchInterval: 60000 // Refetch every minute
  });

  const refreshAll = () => {
    refetchHealth();
    refetchStats();
  };

  const overallStatus = healthData?.status ?? 'unknown';
  const engineStatus = healthData?.acestream.status ?? 'unknown';
  const isReady = overallStatus === 'healthy' && engineStatus === 'online';
  const isDegraded = overallStatus === 'degraded';

  const readinessSummary = isReady
    ? 'Healthy and ready for scraper, playlist, channel, and EPG work.'
    : isDegraded
      ? 'Healthy enough to continue, but one or more systems need attention.'
      : 'The system needs review before you continue.';

  const nextStepCopy = isReady
    ? 'Continue with scraper, playlist, channel, or EPG work.'
    : isDegraded
      ? 'Review engine reachability and configuration before continuing.'
      : 'Stop and review engine connection and saved settings before proceeding.';

  // Helper function to render health status
  const renderHealthStatus = () => {
    if (!healthData) return null;

    const status = isReady ? 'healthy' : isDegraded ? 'degraded' : 'error';
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
        <Button variant="contained" onClick={refreshAll}>
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
          <Button variant="outlined" onClick={refreshAll}>
            Refresh status
          </Button>
        }
      >
        <Stack spacing={2}>
          <Paper
            variant="outlined"
            sx={{
              p: { xs: 2, md: 2.5 },
              borderColor: theme.appTokens.hero.border,
              bgcolor: theme.appTokens.hero.bg,
              backgroundImage: theme.appTokens.hero.spotlight,
            }}
          >
            <Stack spacing={1.5}>
              <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent }}>
                System readiness
              </Typography>
              <Typography variant="h4" sx={{ letterSpacing: '-0.03em' }}>
                {readinessSummary}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Use this summary to confirm whether the engine is reachable, whether configuration looks right, and where you should go next.
              </Typography>
              <Grid container spacing={1.5}>
                <Grid item xs={12} sm={6}>
                  <Paper variant="outlined" sx={{ p: 1.5, height: '100%' }}>
                    <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                      Overall system status
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {overallStatus}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Paper variant="outlined" sx={{ p: 1.5, height: '100%' }}>
                    <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                      Acestream engine status
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {engineStatus}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
              <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha(theme.appTokens.surface.panel, 0.9), border: `1px solid ${theme.appTokens.surface.border}` }}>
                <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                  Next step
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {nextStepCopy}
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Stack>
      </ContentSection>

      <ContentSection title="Operational details" description="Review the current engine/runtime response and the saved configuration snapshot.">
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" component="h3" sx={{ mb: 1.5 }}>Runtime details</Typography>
              <List disablePadding>
                <ListItem disableGutters>
                  <ListItemText primary="Acestream engine status" secondary={engineStatus} />
                </ListItem>
                <Divider component="li" sx={{ my: 1.5 }} />
                <ListItem disableGutters>
                  <ListItemText primary="Acestream engine message" secondary={healthData?.acestream.message || 'Status unknown'} />
                </ListItem>
                <Divider component="li" sx={{ my: 1.5 }} />
                <ListItem disableGutters>
                  <ListItemText primary="Software version" secondary={healthData?.version || 'Unknown'} />
                </ListItem>
              </List>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" component="h3" sx={{ mb: 1.5 }}>Configuration snapshot</Typography>
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
      </ContentSection>

      <ContentSection title="Supporting totals" description="Use grouped totals as supporting context while reviewing readiness and configuration.">
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>Channel totals</Typography>
              {statsData ? (
                <List dense disablePadding>
                  <ListItem disableGutters><ListItemText primary="Total Channels" secondary={statsData.channels.total.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Online Channels" secondary={statsData.channels.online.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Offline Channels" secondary={statsData.channels.offline.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Unknown Status" secondary={statsData.channels.unknown.toString()} /></ListItem>
                </List>
              ) : <Typography color="text.secondary">No channel totals available</Typography>}
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>URL totals</Typography>
              {statsData ? (
                <List dense disablePadding>
                  <ListItem disableGutters><ListItemText primary="Total URLs" secondary={statsData.urls.total.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Active URLs" secondary={statsData.urls.active.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="Error URLs" secondary={statsData.urls.error.toString()} /></ListItem>
                </List>
              ) : <Typography color="text.secondary">No URL totals available</Typography>}
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>EPG totals</Typography>
              {statsData ? (
                <List dense disablePadding>
                  <ListItem disableGutters><ListItemText primary="EPG Sources" secondary={statsData.epg.sources.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="EPG Channels" secondary={statsData.epg.channels.toString()} /></ListItem>
                  <ListItem disableGutters><ListItemText primary="EPG Programs" secondary={statsData.epg.programs.toString()} /></ListItem>
                </List>
              ) : <Typography color="text.secondary">No EPG totals available</Typography>}
            </Paper>
          </Grid>
        </Grid>
      </ContentSection>
    </Box>
  );
};

export default Health;

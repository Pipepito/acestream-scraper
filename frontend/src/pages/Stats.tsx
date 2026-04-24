import React from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { useStats } from '../hooks/useConfig';

const Stats: React.FC = () => {
  const theme = useTheme();
  const layout = theme.appTokens.layout.shell;
  const isPhone = useMediaQuery(`(max-width:${layout.phoneMaxWidth}px)`);
  const { data: statsData, isLoading, error, refetch } = useStats();

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {`Stats error: ${error.toString()}`}
        </Alert>
        <Button variant="contained" onClick={() => refetch()}>
          Retry
        </Button>
      </Box>
    );
  }

  const hasStats = Boolean(statsData);

  return (
    <Box>
      <PageHeader
        title="Stats"
        subtitle="Review inventory totals first so you can spot thin coverage, stale sources, or error-heavy areas before the next task."
        actions={
          <Button variant="outlined" onClick={() => refetch()}>
            Refresh stats
          </Button>
        }
      />

      <ContentSection
        title="Inventory snapshot"
        description="Use this summary to confirm how much channel, URL, and EPG data is currently available."
      >
        {hasStats ? (
          <Stack
            data-testid="stats-summary-metrics"
            direction={isPhone ? 'column' : 'row'}
            spacing={2}
          >
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 1 }}>
                Channels
              </Typography>
              <Typography variant="h4">{statsData.channels.total}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Review channel health next if online coverage looks lower than expected.
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 1 }}>
                URLs
              </Typography>
              <Typography variant="h4">{statsData.urls.total}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Check source activity if active URLs drop or error totals climb.
              </Typography>
            </Paper>
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 1 }}>
                EPG records
              </Typography>
              <Typography variant="h4">{statsData.epg.programs}</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Inspect EPG coverage when channel matching or program depth looks light.
              </Typography>
            </Paper>
          </Stack>
        ) : (
          <Typography color="text.secondary">Stats are not available yet. Refresh after the backend reports inventory data.</Typography>
        )}
      </ContentSection>

      <ContentSection
        title="Totals by source"
        description="Break the current inventory into channel, URL, and EPG totals without leaving the page."
      >
        {hasStats ? (
          <Stack
            data-testid="stats-breakdown-groups"
            direction={isPhone ? 'column' : 'row'}
            spacing={2}
          >
            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>
                Channel totals
              </Typography>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemText primary="Total channels" secondary={statsData.channels.total.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Online channels" secondary={statsData.channels.online.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Offline channels" secondary={statsData.channels.offline.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Unknown status" secondary={statsData.channels.unknown.toString()} />
                </ListItem>
              </List>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>
                URL totals
              </Typography>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemText primary="Total URLs" secondary={statsData.urls.total.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Active URLs" secondary={statsData.urls.active.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="Error URLs" secondary={statsData.urls.error.toString()} />
                </ListItem>
              </List>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
              <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>
                EPG totals
              </Typography>
              <List dense disablePadding>
                <ListItem disableGutters>
                  <ListItemText primary="EPG sources" secondary={statsData.epg.sources.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="EPG channels" secondary={statsData.epg.channels.toString()} />
                </ListItem>
                <ListItem disableGutters>
                  <ListItemText primary="EPG programs" secondary={statsData.epg.programs.toString()} />
                </ListItem>
              </List>
            </Paper>
          </Stack>
        ) : (
          <Typography color="text.secondary">Grouped totals will appear here after the backend reports inventory data.</Typography>
        )}
      </ContentSection>
    </Box>
  );
};

export default Stats;

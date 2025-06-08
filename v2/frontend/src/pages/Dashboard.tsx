import React from 'react';
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
  Divider
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
import { useChannelGroups } from '../hooks/usePlaylists';
import { useURLs } from '../hooks/useScrapers';
import { getErrorMessage } from '../utils/errorUtils';

/**
 * Dashboard page component - displays application overview and quick actions
 */
const Dashboard: React.FC = () => {
  // Fetch channel groups for stats
  const { 
    data: channelGroups = [],
    isLoading: loadingGroups 
  } = useChannelGroups();
  
  // Fetch URLs for stats
  const { 
    data: urls = [],
    isLoading: loadingUrls 
  } = useURLs();

  // Calculate stats
  const totalUrls = urls.length;
  const activeUrls = urls.filter(url => url.enabled).length;
  const totalGroups = channelGroups.length;
  
  // Mock stats - these would come from API in a real implementation
  const stats = {
    totalChannels: 325,
    onlineChannels: 287,
    offlineChannels: 38,
    lastScrape: new Date().toLocaleString()
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Channels
              </Typography>
              <Typography variant="h4" component="div">
                {stats.totalChannels}
              </Typography>
              <Typography sx={{ mt: 1 }} color="textSecondary">
                <TvOutlined fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                In {totalGroups} groups
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Online Channels
              </Typography>
              <Typography variant="h4" component="div" sx={{ color: 'success.main' }}>
                {stats.onlineChannels}
              </Typography>
              <Typography sx={{ mt: 1 }} color="textSecondary">
                <CheckCircleOutline fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5, color: 'success.main' }} />
                {Math.round((stats.onlineChannels / stats.totalChannels) * 100)}% success rate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Offline Channels
              </Typography>
              <Typography variant="h4" component="div" sx={{ color: 'error.main' }}>
                {stats.offlineChannels}
              </Typography>
              <Typography sx={{ mt: 1 }} color="textSecondary">
                <ErrorOutline fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5, color: 'error.main' }} />
                {Math.round((stats.offlineChannels / stats.totalChannels) * 100)}% failure rate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Scraper URLs
              </Typography>
              <Typography variant="h4" component="div">
                {totalUrls}
              </Typography>
              <Typography sx={{ mt: 1 }} color="textSecondary">
                <LinkOutlined fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                {activeUrls} active sources
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Quick Actions */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="contained" 
                  fullWidth
                  startIcon={<PlayArrow />}
                  component={RouterLink}
                  to="/playlist"
                >
                  Get Playlist
                </Button>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  fullWidth
                  startIcon={<Update />}
                >
                  Update All Sources
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <List>
              <ListItem>
                <ListItemText 
                  primary="Latest scrape completed" 
                  secondary={stats.lastScrape} 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="New channels found" 
                  secondary="18 channels added from zeronet:1FQLxNa..." 
                />
              </ListItem>
              <Divider />
              <ListItem>
                <ListItemText 
                  primary="Status check completed" 
                  secondary="23 minutes ago" 
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;

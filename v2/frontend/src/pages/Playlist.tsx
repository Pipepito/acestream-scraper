import React, { useState } from 'react';
import {
  Typography,
  Box,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  FormControlLabel,
  OutlinedInput,
  TextField,
  Button,
  Grid,
  Alert,
  Divider,
  Chip
} from '@mui/material';
import { Download, QrCode } from '@mui/icons-material';
import { useM3UPlaylist, useChannelGroups } from '../hooks/usePlaylists';
import { PlaylistFilters } from '../services/playlistService';
import { getErrorMessage } from '../utils/errorUtils';

/**
 * Playlist configuration and download page
 */
const Playlist: React.FC = () => {
  const [filters, setFilters] = useState<PlaylistFilters>({
    only_online: true,
    include_groups: [],
    exclude_groups: []
  });

  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  
  // Get available channel groups
  const { 
    data: channelGroups = [],
    isLoading: loadingGroups
  } = useChannelGroups();

  // Get M3U playlist URL based on current filters
  const playlistUrl = `/api/v1/playlists/m3u?${new URLSearchParams({
    ...filters.only_online !== undefined ? { only_online: String(filters.only_online) } : {},
    ...filters.search ? { search: filters.search } : {},
    ...search ? { search } : {},
    ...filters.include_groups ? filters.include_groups.map(g => `include_groups=${g}`).join('&') : '',
    ...filters.exclude_groups ? filters.exclude_groups.map(g => `exclude_groups=${g}`).join('&') : ''
  }).toString()}`;

  const handleIncludeGroupsChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setFilters({
      ...filters,
      include_groups: event.target.value as string[]
    });
  };

  const handleExcludeGroupsChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setFilters({
      ...filters,
      exclude_groups: event.target.value as string[]
    });
  };

  const handleOnlyOnlineChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({
      ...filters,
      only_online: event.target.checked
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Playlist Generator
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Generate M3U Playlist
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search Channels"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Enter channel name or keywords"
              margin="normal"
            />
            
            <FormControlLabel
              control={
                <Checkbox 
                  checked={filters.only_online ?? true}
                  onChange={handleOnlyOnlineChange}
                />
              }
              label="Only include online channels"
            />
            
            <Box sx={{ mt: 2 }}>
              <Button 
                variant="contained" 
                color="primary"
                onClick={() => setShowFilters(!showFilters)}
                sx={{ mr: 2 }}
              >
                {showFilters ? "Hide Advanced Filters" : "Show Advanced Filters"}
              </Button>
            </Box>
            
            {showFilters && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Advanced Filters
                </Typography>
                
                <FormControl fullWidth margin="normal">
                  <InputLabel>Include Groups</InputLabel>
                  <Select
                    multiple
                    value={filters.include_groups || []}
                    onChange={handleIncludeGroupsChange}
                    input={<OutlinedInput label="Include Groups" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(selected as string[]).map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                    disabled={loadingGroups}
                  >
                    {channelGroups.map((group) => (
                      <MenuItem key={group} value={group}>
                        <Checkbox checked={(filters.include_groups || []).indexOf(group) > -1} />
                        <ListItemText primary={group} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl fullWidth margin="normal">
                  <InputLabel>Exclude Groups</InputLabel>
                  <Select
                    multiple
                    value={filters.exclude_groups || []}
                    onChange={handleExcludeGroupsChange}
                    input={<OutlinedInput label="Exclude Groups" />}
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {(selected as string[]).map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                    disabled={loadingGroups}
                  >
                    {channelGroups.map((group) => (
                      <MenuItem key={group} value={group}>
                        <Checkbox checked={(filters.exclude_groups || []).indexOf(group) > -1} />
                        <ListItemText primary={group} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            )}
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Download Options
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              The generated playlist will work with any media player that supports Acestream links, 
              such as VLC or Kodi with the Acestream addon.
            </Alert>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Playlist URL:
              </Typography>
              <TextField
                fullWidth
                variant="outlined"
                value={playlistUrl}
                InputProps={{
                  readOnly: true,
                }}
                size="small"
              />
            </Box>
            
            <Button
              variant="contained"
              color="primary"
              startIcon={<Download />}
              sx={{ mr: 2 }}
              href={playlistUrl}
              download="acestream_playlist.m3u"
            >
              Download M3U
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<QrCode />}
            >
              Show QR Code
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Usage Instructions
        </Typography>
        
        <Typography variant="body2" paragraph>
          1. Configure your playlist using the options above
        </Typography>
        
        <Typography variant="body2" paragraph>
          2. Download the M3U file or copy the playlist URL
        </Typography>
        
        <Typography variant="body2" paragraph>
          3. Import the M3U into your media player or IPTV client
        </Typography>
        
        <Divider sx={{ my: 2 }} />
        
        <Alert severity="warning">
          Make sure you have the Acestream engine installed and running on your device before playing the channels.
        </Alert>
      </Paper>
    </Box>
  );
};

export default Playlist;

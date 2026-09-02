import React, { useState } from 'react';
import {
  Box,
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
  Chip,
  SelectChangeEvent,
  Stack,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@mui/material';
import { Download, QrCode } from '@mui/icons-material';
import { QRCodeSVG } from 'qrcode.react';
import { useChannelGroups } from '../hooks/usePlaylists';
import { useBaseUrls } from '../hooks/useBaseUrls';
import { PlaylistFilters, playlistService } from '../services/playlistService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { alpha, useTheme } from '@mui/material/styles';

/**
 * Playlist configuration and download page
 */
const Playlist: React.FC = () => {
  const theme = useTheme();
  const [filters, setFilters] = useState<PlaylistFilters>({
    only_online: true,
    include_groups: [],
    exclude_groups: []
  });

  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [search, setSearch] = useState<string>('');
  const [selectedBaseUrlId, setSelectedBaseUrlId] = useState<number | ''>('');
  const [qrOpen, setQrOpen] = useState(false);

  // Get available channel groups
  const {
    data: channelGroups = [],
    isLoading: loadingGroups
  } = useChannelGroups();

  // Named stream base URLs (Settings > Stream base URLs)
  const {
    data: namedBaseUrls = [],
    isLoading: loadingBaseUrls
  } = useBaseUrls();

  // Get M3U playlist URL based on current filters (use absolute in dev, relative in prod)
  const playlistUrl = playlistService.getPlaylistDownloadUrl({
    ...filters,
    search: search || filters.search,
    base_url_id: selectedBaseUrlId === '' ? undefined : selectedBaseUrlId
  });
  // Players scan this from another device, so the QR must carry an absolute URL.
  const absolutePlaylistUrl = typeof window === 'undefined' ? playlistUrl : new URL(playlistUrl, window.location.origin).toString();

  const handleIncludeGroupsChange = (event: SelectChangeEvent<string[]>) => {
    setFilters({
      ...filters,
      include_groups: event.target.value as string[]
    });
  };

  const handleExcludeGroupsChange = (event: SelectChangeEvent<string[]>) => {
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

  const handleFavoritesOnlyChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({
      ...filters,
      favorites_only: event.target.checked
    });
  };

  return (
    <Box>
      <PageHeader
        title="Playlist"
        subtitle="Build a player-ready M3U link, then download or share it without exposing advanced controls too early."
      />

      <ContentSection
        title="Generate playlist"
        description="Choose the channels you want, keep the main path simple, and open advanced options only when you need them."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ width: { xs: '100%', sm: 'auto' } }}>
            <Button variant="contained" color="primary" startIcon={<Download />} href={playlistUrl} download="acestream_playlist.m3u">
              Download M3U
            </Button>
            <Button variant="outlined" startIcon={<QrCode />} onClick={() => setQrOpen(true)}>
              Show QR Code
            </Button>
          </Stack>
        }
      >
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Box
              sx={{
                p: { xs: 2, md: 2.5 },
                borderRadius: 2.5,
                bgcolor: theme.appTokens.hero.bg,
                border: `1px solid ${theme.appTokens.hero.border}`,
                backgroundImage: theme.appTokens.hero.spotlight,
              }}
            >
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <Box sx={{ minWidth: 0, maxWidth: 720 }}>
                  <Box sx={{ typography: 'statusMeta', color: theme.appTokens.hero.accent, mb: 1 }}>Playlist ready</Box>
                  <Box sx={{ typography: 'h4', letterSpacing: '-0.03em', mb: 1 }}>Download the playlist or share the link first.</Box>
                  <Box sx={{ typography: 'body2', color: 'text.secondary' }}>
                    Keep the main path simple: confirm the playlist URL, download the M3U, or share it before you open optional filtering controls.
                  </Box>
                </Box>
                <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha(theme.appTokens.surface.panel, 0.92), border: `1px solid ${theme.appTokens.surface.border}`, minWidth: { xs: '100%', sm: 260 } }}>
                  <Box sx={{ typography: 'statusMeta', color: 'text.secondary', mb: 0.5 }}>Primary path</Box>
                  <Box sx={{ typography: 'body2', fontWeight: 600 }}>Download the playlist or copy the URL, then import it into your player.</Box>
                </Box>
              </Box>
            </Box>
          </Grid>
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

            <FormControlLabel
              control={
                <Checkbox
                  checked={filters.favorites_only ?? false}
                  onChange={handleFavoritesOnlyChange}
                />
              }
              label="Only include favorite TV channels"
            />

            <FormControl fullWidth margin="normal">
              <InputLabel id="stream-base-url-label">Stream base URL</InputLabel>
              <Select
                labelId="stream-base-url-label"
                value={selectedBaseUrlId}
                onChange={(event) => {
                  const value = event.target.value;
                  setSelectedBaseUrlId(value === '' ? '' : Number(value));
                }}
                input={<OutlinedInput label="Stream base URL" />}
                disabled={loadingBaseUrls}
              >
                <MenuItem value="">Default</MenuItem>
                {namedBaseUrls.map((entry) => (
                  <MenuItem key={entry.id} value={entry.id}>
                    {entry.is_default ? `${entry.name} (default)` : entry.name}
                  </MenuItem>
                ))}
              </Select>
              <Box sx={{ typography: 'caption', color: 'text.secondary', mt: 0.5 }}>
                Pick a named link format from Settings, or keep Default to use the configured one.
              </Box>
            </FormControl>

            <Box sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                onClick={() => setShowFilters(!showFilters)}
              >
                {showFilters ? 'Hide advanced options' : 'Show advanced options'}
              </Button>
            </Box>

              <Collapse in={showFilters} mountOnEnter unmountOnExit>
                <Box sx={{ mt: 3 }}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Advanced options are optional. Use them only when the basic download or share path needs extra filtering.
                  </Alert>

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
            </Collapse>
          </Grid>

          <Grid item xs={12} md={6}>
            <Alert severity="info" sx={{ mb: 2 }}>
              The generated playlist will work with any media player that supports Acestream links,
              such as VLC or Kodi with the Acestream addon.
            </Alert>

            <Box sx={{ mb: 2 }}>
              <Box component="p" sx={{ typography: 'body2', mb: 1 }}>
                Playlist URL:
              </Box>
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
          </Grid>
        </Grid>
      </ContentSection>

      <ContentSection title="How to use this playlist" description="Follow the same three-step path each time so playback setup stays predictable.">
        <Box sx={{ typography: 'body2', mb: 2 }}>
          1. Configure your playlist using the options above
        </Box>

        <Box sx={{ typography: 'body2', mb: 2 }}>
          2. Download the M3U file or copy the playlist URL
        </Box>

        <Box sx={{ typography: 'body2', mb: 2 }}>
          3. Import the M3U into your media player or IPTV client
        </Box>

        <Divider sx={{ my: 2 }} />

        <Alert severity="warning">
          Make sure you have the Acestream engine installed and running on your device before playing the channels.
        </Alert>
      </ContentSection>

      <Dialog open={qrOpen} onClose={() => setQrOpen(false)} aria-labelledby="playlist-qr-title">
        <DialogTitle id="playlist-qr-title">Playlist QR code</DialogTitle>
        <DialogContent>
          <Stack spacing={2} alignItems="center" sx={{ pt: 1 }}>
            <QRCodeSVG value={absolutePlaylistUrl} size={224} marginSize={2} role="img" aria-label="QR code for the playlist URL" />
            <Typography variant="body2" sx={{ wordBreak: 'break-all', textAlign: 'center' }}>
              {absolutePlaylistUrl}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center' }}>
              Scan it from your player or IPTV app to import this playlist with the current options.
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQrOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Playlist;

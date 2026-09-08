import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Grid,
  IconButton,
  InputLabel,
  ListItemText,
  MenuItem,
  OutlinedInput,
  Select,
  Snackbar,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { ContentCopy, Download, ExpandLess, ExpandMore, QrCode } from '@mui/icons-material';
import StreamLinkFormatsSection from '../components/StreamLinkFormatsSection';
import { QRCodeSVG } from 'qrcode.react';
import { useChannelGroups, usePlaylistChannelSummary } from '../hooks/usePlaylists';
import { useBaseUrls } from '../hooks/useBaseUrls';
import { usePublicUrl } from '../hooks/useSystemServices';
import { PlaylistFilters, playlistService, getAbsolutePlaylistUrl } from '../services/playlistService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

/** Build the M3U link, then download it or hand it to a player. */
const Playlist: React.FC = () => {
  const [filters, setFilters] = useState<PlaylistFilters>({ only_online: false, include_groups: [], exclude_groups: [] });
  const [showGroups, setShowGroups] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedBaseUrlId, setSelectedBaseUrlId] = useState<number | ''>('');
  const [formatsOpen, setFormatsOpen] = useState(false);
  const [formatNotice, setFormatNotice] = useState<{message: string; severity: 'success' | 'error'} | null>(null);
  const [qrOpen, setQrOpen] = useState(false);
  const [copied, setCopied] = useState<'ok' | 'failed' | null>(null);

  const { data: channelGroups = [], isLoading: loadingGroups } = useChannelGroups();
  const { data: namedBaseUrls = [], isLoading: loadingBaseUrls, isError: baseUrlsError } = useBaseUrls();
  const { data: publicUrl } = usePublicUrl();
  const { data: summary } = usePlaylistChannelSummary();

  useEffect(() => {
    if (!loadingBaseUrls && !baseUrlsError && selectedBaseUrlId !== '' && !namedBaseUrls.some(entry => entry.id === selectedBaseUrlId)) setSelectedBaseUrlId('');
  }, [namedBaseUrls, loadingBaseUrls, baseUrlsError, selectedBaseUrlId]);
  const selectedFormat = namedBaseUrls.find(entry => selectedBaseUrlId === '' ? entry.is_default : entry.id === selectedBaseUrlId);

  const effectiveFilters: PlaylistFilters = {
    ...filters,
    search: search || undefined,
    base_url_id: selectedBaseUrlId === '' ? undefined : selectedBaseUrlId,
  };
  const playlistUrl = playlistService.getPlaylistDownloadUrl(effectiveFilters);
  const absolutePlaylistUrl = getAbsolutePlaylistUrl(effectiveFilters, publicUrl?.url);

  const handleGroups = (key: 'include_groups' | 'exclude_groups') => (event: SelectChangeEvent<string[]>) => {
    setFilters((prev) => ({ ...prev, [key]: event.target.value as string[] }));
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(absolutePlaylistUrl);
      setCopied('ok');
    } catch {
      setCopied('failed');
    }
  };

  const onlineHelp = summary
    ? `${summary.online} of ${summary.total_channels} channels are online right now`
    : 'Channels the last status check found online';

  const renderGroupSelect = (label: string, key: 'include_groups' | 'exclude_groups') => (
    <FormControl fullWidth size="small">
      <InputLabel id={`playlist-${key}-label`}>{label}</InputLabel>
      <Select
        labelId={`playlist-${key}-label`}
        multiple
        value={filters[key] || []}
        onChange={handleGroups(key)}
        input={<OutlinedInput label={label} />}
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
            <Checkbox checked={(filters[key] || []).includes(group)} size="small" />
            <ListItemText primary={group} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );

  return (
    <Box>
      <PageHeader title="Playlist" subtitle="One M3U link with your channels. Import it in your player and it stays up to date." />

      <ContentSection title="Your playlist">
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Stack spacing={2}>
              <Typography variant="sectionTitle" component="h3">
                Options
              </Typography>
              <TextField size="small" fullWidth label="Search channels" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Only include channels whose name contains…" />
              <Box>
                <FormControlLabel
                  control={<Checkbox checked={filters.only_online ?? false} onChange={(e) => setFilters((prev) => ({ ...prev, only_online: e.target.checked }))} />}
                  label="Only online channels"
                />
                <FormHelperText sx={{ mt: -0.5, ml: 4 }}>{onlineHelp}</FormHelperText>
              </Box>
              <FormControlLabel
                control={<Checkbox checked={filters.favorites_only ?? false} onChange={(e) => setFilters((prev) => ({ ...prev, favorites_only: e.target.checked }))} />}
                label="Favorite TV channels only"
              />
              <FormControl fullWidth size="small">
                <InputLabel id="stream-base-url-label" shrink>Stream link format</InputLabel>
                <Select<number | ''>
                  labelId="stream-base-url-label"
                  displayEmpty
                  renderValue={(value) => value === '' ? 'Default' : namedBaseUrls.find(entry => entry.id === value)?.name ?? 'Default'}
                  value={selectedBaseUrlId}
                  onChange={(event) => {
                    const value = event.target.value;
                    setSelectedBaseUrlId(value === '' ? '' : Number(value));
                  }}
                  input={<OutlinedInput label="Stream link format" notched />}
                  disabled={loadingBaseUrls}
                >
                  <MenuItem value="">Default</MenuItem>
                  {namedBaseUrls.map((entry) => (
                    <MenuItem key={entry.id} value={entry.id}>
                      {entry.is_default ? `${entry.name} (default)` : entry.name}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>Default uses your saved format, or acestream:// when none is saved.</FormHelperText>
              </FormControl>
              {selectedFormat ? <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}><strong>{selectedFormat.name}:</strong> {selectedFormat.pattern}</Typography> : null}
              {baseUrlsError ? <Alert severity="warning">Could not load stream link formats. Try reloading the page.</Alert> : null}
              <Button onClick={() => setFormatsOpen(value => !value)} aria-expanded={formatsOpen} aria-controls="playlist-formats" size="small">{namedBaseUrls.length ? 'Manage link formats' : 'Set up link formats'}</Button>
              <Box>
                <Button size="small" onClick={() => setShowGroups((value) => !value)} aria-expanded={showGroups} endIcon={showGroups ? <ExpandLess /> : <ExpandMore />}>
                  Group filters
                </Button>
                <Collapse in={showGroups} mountOnEnter unmountOnExit>
                  <Stack spacing={2} sx={{ mt: 1.5 }}>
                    {renderGroupSelect('Include groups', 'include_groups')}
                    {renderGroupSelect('Exclude groups', 'exclude_groups')}
                  </Stack>
                </Collapse>
              </Box>
            </Stack>
          </Grid>
          <Grid item xs={12} md={5}>
            <Stack spacing={1.5}>
              <Typography variant="sectionTitle" component="h3">
                Playlist link
              </Typography>
              <TextField
                fullWidth
                size="small"
                value={absolutePlaylistUrl}
                inputProps={{ readOnly: true, 'aria-label': 'Playlist URL', sx: { fontFamily: 'monospace', fontSize: 12.5 } }}
                InputProps={{
                  endAdornment: (
                    <Tooltip title="Copy link">
                      <IconButton size="small" aria-label="Copy playlist URL" onClick={handleCopy}>
                        <ContentCopy fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  ),
                }}
              />
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                <Button variant="contained" startIcon={<Download />} href={playlistUrl} download="acestream_playlist.m3u">
                  Download M3U
                </Button>
                <Button variant="outlined" startIcon={<QrCode />} onClick={() => setQrOpen(true)}>
                  Show QR code
                </Button>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Import this URL in VLC, Kodi or your IPTV app. The AceStream engine must be reachable from the player.
              </Typography>
            </Stack>
          </Grid>
        </Grid>
      </ContentSection>

      <Collapse in={formatsOpen} mountOnEnter unmountOnExit id="playlist-formats">
        <Alert severity="info" sx={{ mb: 2 }}>Formats are shared with copied stream links and supported remote-player actions. Changing the default affects all links that use it.</Alert>
        {formatNotice ? <Alert severity={formatNotice.severity} onClose={() => setFormatNotice(null)}>{formatNotice.message}</Alert> : null}
        <StreamLinkFormatsSection notify={(message, severity) => setFormatNotice({ message, severity })} />
      </Collapse>

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

      <Snackbar open={copied !== null} autoHideDuration={3000} onClose={() => setCopied(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={() => setCopied(null)} severity={copied === 'ok' ? 'success' : 'error'} sx={{ width: '100%' }}>
          {copied === 'ok' ? 'Playlist link copied.' : 'Unable to copy the link. Select it and copy by hand.'}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Playlist;

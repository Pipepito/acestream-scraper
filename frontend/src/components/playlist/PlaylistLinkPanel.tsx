import React, { useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, Snackbar, Stack, TextField, Tooltip, Typography } from '@mui/material';
import { ContentCopy, Download, QrCode } from '@mui/icons-material';
import { QRCodeSVG } from 'qrcode.react';
import type { PlaylistLink } from './usePlaylistLink';

interface PlaylistLinkPanelProps { link: PlaylistLink }

/** The generated playlist URL with copy, download and QR actions. Shared by the page and the dialog. */
const PlaylistLinkPanel: React.FC<PlaylistLinkPanelProps> = ({ link }) => {
  const { managed, playbackToken, creatingLink, linkError, createLink, playlistUrl, absolutePlaylistUrl } = link;
  const [qrOpen, setQrOpen] = useState(false);
  const [copied, setCopied] = useState<'ok' | 'failed' | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(absolutePlaylistUrl);
      setCopied('ok');
    } catch {
      setCopied('failed');
    }
  };

  return (
    <Stack spacing={1.5}>
      <Typography variant="sectionTitle" component="h3">
        Playlist link
      </Typography>
      {managed ? <Alert severity="info">Protected playlists use the server relay. Create a playback credential before copying or downloading a playlist for an external player; revoke shared links in Settings → Access.</Alert> : null}
      {managed && !playbackToken ? <Button disabled={creatingLink} onClick={() => void createLink()}>Create playback credential</Button> : null}
      {linkError ? <Alert severity="error">{linkError}</Alert> : null}
      <TextField
        fullWidth
        size="small"
        value={absolutePlaylistUrl}
        inputProps={{ readOnly: true, 'aria-label': 'Playlist URL', sx: { fontFamily: 'monospace', fontSize: 12.5 } }}
        InputProps={{
          endAdornment: (
            <Tooltip title="Copy link">
              <IconButton size="small" aria-label="Copy playlist URL" disabled={managed && !playbackToken} onClick={handleCopy}>
                <ContentCopy fontSize="small" />
              </IconButton>
            </Tooltip>
          ),
        }}
      />
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Button variant="contained" disabled={managed && !playbackToken} startIcon={<Download />} href={playlistUrl} download="acestream_playlist.m3u">
          Download M3U
        </Button>
        <Button variant="outlined" disabled={managed && !playbackToken} startIcon={<QrCode />} onClick={() => setQrOpen(true)}>
          Show QR code
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary">
        {managed ? 'Import this URL in VLC, Kodi or your IPTV app. The application must be reachable from the player.' : 'Import this URL in VLC, Kodi or your IPTV app. The AceStream engine must be reachable from the player.'}
      </Typography>

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
    </Stack>
  );
};

export default PlaylistLinkPanel;

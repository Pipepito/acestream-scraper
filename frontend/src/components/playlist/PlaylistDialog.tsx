import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Button, Collapse, Dialog, DialogActions, DialogContent, DialogTitle, Stack, useMediaQuery, useTheme } from '@mui/material';
import StreamLinkFormatsSection from '../StreamLinkFormatsSection';
import PlaylistLinkPanel from './PlaylistLinkPanel';
import PlaylistOptionsForm from './PlaylistOptionsForm';
import { usePlaylistLink } from './usePlaylistLink';

interface PlaylistDialogProps { open: boolean; onClose: () => void }

/** Mounted only while open so the playlist queries run on demand. */
const PlaylistDialogContent: React.FC = () => {
  const tUi = useUiText();
  const link = usePlaylistLink();
  const [formatsOpen, setFormatsOpen] = useState(false);
  const [formatNotice, setFormatNotice] = useState<{ message: string | (() => string); severity: 'success' | 'error' } | null>(null);
  return (
    <Stack spacing={3}>
      <PlaylistLinkPanel link={link} />
      <PlaylistOptionsForm link={link} formatsOpen={formatsOpen} onToggleFormats={() => setFormatsOpen((value) => !value)} formatsId="playlist-dialog-formats" />
      <Collapse in={formatsOpen} mountOnEnter unmountOnExit id="playlist-dialog-formats">
        <Alert severity="info" sx={{ mb: 2 }}>{tUi("Formats are shared with copied stream links and supported remote-player actions. Changing the default affects all links that use it.")}</Alert>
        {formatNotice ? <Alert severity={formatNotice.severity} onClose={() => setFormatNotice(null)}>{typeof formatNotice.message === 'function' ? formatNotice.message() : formatNotice.message}</Alert> : null}
        <StreamLinkFormatsSection notify={(message, severity) => setFormatNotice({ message, severity })} />
      </Collapse>
    </Stack>
  );
};

/** The whole playlist workflow from the TV dashboard: link first, then options, then the formats editor. */
const PlaylistDialog: React.FC<PlaylistDialogProps> = ({ open, onClose }) => {
  const tUi = useUiText();
  const fullScreen = useMediaQuery(useTheme().breakpoints.down('sm'));
  return (
    <Dialog open={open} onClose={onClose} fullScreen={fullScreen} maxWidth="md" fullWidth aria-labelledby="playlist-dialog-title">
      <DialogTitle id="playlist-dialog-title">{tUi("Your playlist")}</DialogTitle>
      <DialogContent>
        {open ? <PlaylistDialogContent /> : null}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 'max(16px, env(safe-area-inset-bottom))' }}>
        <Button variant="contained" onClick={onClose}>{tUi("Close")}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default PlaylistDialog;

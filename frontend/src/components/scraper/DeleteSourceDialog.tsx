import React, { useEffect, useId, useState } from 'react';
import { Button, Checkbox, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, FormControlLabel } from '@mui/material';
import type { ScrapedURL } from '../../services/scraperService';

interface DeleteSourceDialogProps {
  open: boolean;
  source: ScrapedURL | null;
  busy?: boolean;
  onClose: () => void;
  onConfirm: (deleteStreams: boolean) => void;
}

/** Deleting a source offers to remove its streams too; TV channels are never deleted. */
const DeleteSourceDialog: React.FC<DeleteSourceDialogProps> = ({ open, source, busy = false, onClose, onConfirm }) => {
  const titleId = useId();
  const [deleteStreams, setDeleteStreams] = useState(true);
  useEffect(() => { if (open) setDeleteStreams(true); }, [open]);
  const streams = source?.channels_found ?? 0;
  const assigned = source?.assigned_count ?? 0;
  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} aria-labelledby={titleId} maxWidth="xs" fullWidth>
      <DialogTitle id={titleId}>Delete this source?</DialogTitle>
      <DialogContent>
        <DialogContentText>The source and its schedule are removed. TV channels are kept.</DialogContentText>
        <FormControlLabel sx={{ mt: 1 }} control={<Checkbox checked={deleteStreams} disabled={busy || streams === 0} onChange={(_, value) => setDeleteStreams(value)} />}
          label={`Also remove its ${streams} stream${streams === 1 ? '' : 's'} (${assigned} linked to TV channels)`} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy}>Cancel</Button>
        <Button variant="contained" color="error" disabled={busy} onClick={() => onConfirm(deleteStreams && streams > 0)}
          startIcon={busy ? <CircularProgress size={16} color="inherit" /> : undefined}>Delete source</Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteSourceDialog;

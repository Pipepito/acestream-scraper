import React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@mui/material';
import { TVChannel } from '../types/tvChannelTypes';

interface TVChannelDeleteDialogProps {
  channel: TVChannel | null;
  onCancel: () => void;
  onConfirm: () => void;
}

const TVChannelDeleteDialog: React.FC<TVChannelDeleteDialogProps> = ({ channel, onCancel, onConfirm }) => (
  <Dialog open={channel !== null} onClose={onCancel} fullWidth maxWidth="xs">
    <DialogTitle>Delete TV Channel</DialogTitle>
    <DialogContent dividers>
      <Typography>
        Remove {channel?.name || 'this TV channel'} from the TV channel inventory? This cannot be undone.
      </Typography>
    </DialogContent>
    <DialogActions>
      <Button onClick={onCancel} variant="contained" data-action-priority="primary">
        Cancel
      </Button>
      <Button onClick={onConfirm} color="error" variant="outlined" data-action-priority="danger">
        Delete TV Channel
      </Button>
    </DialogActions>
  </Dialog>
);

export default TVChannelDeleteDialog;

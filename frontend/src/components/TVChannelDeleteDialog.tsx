import { useUiText } from '../i18n/useUiText';
import React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@mui/material';
import { useUnsavedChanges } from './UnsavedChanges';
import { TVChannel } from '../types/tvChannelTypes';

interface TVChannelDeleteDialogProps {
  channel: TVChannel | null;
  submitting?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}

const TVChannelDeleteDialog: React.FC<TVChannelDeleteDialogProps> = ({ channel, submitting = false, onCancel, onConfirm }) => { const tUi = useUiText(); useUnsavedChanges(false, channel !== null && submitting); return (
  <Dialog open={channel !== null} onClose={submitting ? undefined : onCancel} fullWidth maxWidth="xs">
    <DialogTitle>{tUi("Delete TV Channel")}</DialogTitle>
    <DialogContent dividers>
      <Typography>
        {tUi("Remove")}{' '}{channel?.name || 'this TV channel'} {tUi("from the TV channel inventory? This cannot be undone.")}</Typography>
    </DialogContent>
    <DialogActions>
      <Button disabled={submitting} onClick={onCancel} variant="contained" data-action-priority="primary">
        {tUi("Cancel")}</Button>
      <Button disabled={submitting} onClick={onConfirm} color="error" variant="outlined" data-action-priority="danger">
        {tUi("Delete TV Channel")}</Button>
    </DialogActions>
  </Dialog>
); };

export default TVChannelDeleteDialog;

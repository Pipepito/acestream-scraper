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
import { TVChannel } from '../types/tvChannelTypes';

interface TVChannelDeleteDialogProps {
  channel: TVChannel | null;
  onCancel: () => void;
  onConfirm: () => void;
}

const TVChannelDeleteDialog: React.FC<TVChannelDeleteDialogProps> = ({ channel, onCancel, onConfirm }) => { const tUi = useUiText(); return (
  <Dialog open={channel !== null} onClose={onCancel} fullWidth maxWidth="xs">
    <DialogTitle>{tUi("Delete TV Channel")}</DialogTitle>
    <DialogContent dividers>
      <Typography>
        {tUi("Remove")}{' '}{channel?.name || 'this TV channel'} {tUi("from the TV channel inventory? This cannot be undone.")}</Typography>
    </DialogContent>
    <DialogActions>
      <Button onClick={onCancel} variant="contained" data-action-priority="primary">
        {tUi("Cancel")}</Button>
      <Button onClick={onConfirm} color="error" variant="outlined" data-action-priority="danger">
        {tUi("Delete TV Channel")}</Button>
    </DialogActions>
  </Dialog>
); };

export default TVChannelDeleteDialog;

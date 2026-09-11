import React from 'react';
import ChannelActivityLog from './ChannelActivityLog';
import { Dialog, DialogTitle, DialogContent, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

interface ChannelActivityLogDialogProps {
  open: boolean;
  onClose: () => void;
  channelId: string;
}

const ChannelActivityLogDialog: React.FC<ChannelActivityLogDialogProps> = ({ open, onClose, channelId }) => (
  <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
    <DialogTitle>
      Channel Activity Log
      <IconButton
        aria-label="close"
        onClick={onClose}
        sx={{ position: 'absolute', right: 8, top: 8 }}
      >
        <CloseIcon />
      </IconButton>
    </DialogTitle>
    <DialogContent>
      <ChannelActivityLog channelId={channelId} />
    </DialogContent>
  </Dialog>
);

export default ChannelActivityLogDialog;

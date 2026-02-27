import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, MenuItem, FormControl, InputLabel, Select, Box, Alert
} from '@mui/material';

interface BatchAssignDialogProps {
  open: boolean;
  onClose: () => void;
  selectedChannels: any[];
  groups: string[];
  onAssign: (group: string) => Promise<void>;
}

const BatchAssignDialog: React.FC<BatchAssignDialogProps> = ({ open, onClose, selectedChannels, groups, onAssign }) => {
  const [group, setGroup] = useState('');
  const [error, setError] = useState<string|null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleAssign = async () => {
    setError(null);
    setLoading(true);
    try {
      await onAssign(group);
      setSuccess(true);
      setTimeout(() => { setSuccess(false); onClose(); }, 1000);
    } catch (err: any) {
      setError(err.message || 'Batch assign failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth fullScreen={window.innerWidth < 600}>
      <DialogTitle>Batch Assign Group</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>Assigned successfully!</Alert>}
        <Box mb={2}>
          <FormControl fullWidth>
            <InputLabel>Group</InputLabel>
            <Select
              value={group}
              label="Group"
              onChange={e => setGroup(e.target.value)}
            >
              {groups.map(g => <MenuItem key={g} value={g}>{g}</MenuItem>)}
            </Select>
          </FormControl>
        </Box>
        <Box>Selected Channels: {selectedChannels.length}</Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button onClick={handleAssign} variant="contained" disabled={loading || !group}>Assign</Button>
      </DialogActions>
    </Dialog>
  );
};

export default BatchAssignDialog;

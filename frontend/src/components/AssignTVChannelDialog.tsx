import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, MenuItem, Select, FormControl, InputLabel, CircularProgress, Alert } from '@mui/material';
import { PaginatedTVChannels } from '../hooks/useTVChannels';

interface AssignTVChannelDialogProps {
  open: boolean;
  onClose: () => void;
  tvChannels?: PaginatedTVChannels;
  onAssign: (tvChannelId: number) => void;
  loading?: boolean;
  error?: string | null;
}

const AssignTVChannelDialog: React.FC<AssignTVChannelDialogProps> = ({ open, onClose, tvChannels, onAssign, loading, error }) => {
  const [selectedId, setSelectedId] = useState<number | ''>('');

  const handleAssign = () => {
    if (selectedId) onAssign(selectedId);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Assign to TV Channel</DialogTitle>
      <DialogContent>
        <FormControl fullWidth margin="normal">
          <InputLabel id="tv-channel-select-label">TV Channel</InputLabel>
          <Select
            labelId="tv-channel-select-label"
            value={selectedId}
            label="TV Channel"
            onChange={e => setSelectedId(Number(e.target.value))}
            disabled={loading}
          >
            {(tvChannels?.items || []).map(tc => (
              <MenuItem key={tc.id} value={tc.id}>{tc.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button onClick={handleAssign} disabled={loading || !selectedId} variant="contained">
          {loading ? <CircularProgress size={20} /> : 'Assign'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AssignTVChannelDialog;

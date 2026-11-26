import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useId, useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, MenuItem, FormControl, InputLabel, Select, Box, Alert, useMediaQuery
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { getErrorDetail } from '../utils/errorUtils';

interface BatchAssignDialogProps {
  open: boolean;
  onClose: () => void;
  selectedChannels: any[];
  groups: string[];
  onAssign: (group: string) => Promise<void>;
}

const BatchAssignDialog: React.FC<BatchAssignDialogProps> = ({ open, onClose, selectedChannels, groups, onAssign }) => {
  const tUi = useUiText();
  const theme = useTheme();
  const isPhone = useMediaQuery(theme.breakpoints.down('sm'));
  const groupLabelId = useId();
  const [group, setGroup] = useState('');
  const [error, setError] = useState<string|null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!open) {
      setGroup('');
      setError(null);
      setLoading(false);
      setSuccess(false);
    }
  }, [open]);

  const handleClose = () => {
    if (loading) {
      return;
    }

    setGroup('');
    setError(null);
    setSuccess(false);
    onClose();
  };

  const handleAssign = async () => {
    setError(null);
    setLoading(true);
    try {
      await onAssign(group);
      setSuccess(true);
    } catch (err) {
      setError(getErrorDetail(err) || tUi('Batch assign failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth fullScreen={isPhone}>
      <DialogTitle>{tUi("Batch Assign Group")}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{tUi("Assigned successfully!")}</Alert>}
        <Box mb={2}>
          <FormControl fullWidth>
            <InputLabel id={groupLabelId}>{tUi("Group")}</InputLabel>
            <Select
              labelId={groupLabelId}
              value={group}
              label={tUi("Group")}
              onChange={e => setGroup(e.target.value)}
            >
              {groups.map(g => <MenuItem key={g} value={g}>{g}</MenuItem>)}
            </Select>
          </FormControl>
        </Box>
        <Box>{tUi("Selected Channels:")}{' '}{selectedChannels.length}</Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>{success ? tUi("Close") : tUi("Cancel")}</Button>
        <Button onClick={handleAssign} variant="contained" disabled={loading || success || !group}>{tUi("Assign")}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default BatchAssignDialog;

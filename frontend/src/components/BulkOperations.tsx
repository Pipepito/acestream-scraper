import React, { useRef, useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  TextField,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Switch,
  Alert,
  CircularProgress,
  useMediaQuery
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { ChannelUpdate } from '../types/channelTypes';
import { getErrorMessage } from '../utils/errorUtils';

interface BulkOperationsProps {
  open: boolean;
  onClose: () => void;
  selectedChannels: Array<{ id: string; name?: string }>;
  onBulkEdit: (updates: ChannelUpdate) => Promise<void>;
  onBulkDelete: (ids: string[]) => Promise<void>; // Accepts array of IDs for bulk delete
  onBulkActivate: (active: boolean) => Promise<void>;
}

const BulkOperations: React.FC<BulkOperationsProps> = ({
  open,
  onClose,
  selectedChannels,
  onBulkEdit,
  onBulkDelete,
  onBulkActivate
}) => {
  const theme = useTheme();
  const isPhone = useMediaQuery(theme.breakpoints.down('sm'));
  const [editFields, setEditFields] = useState({
    group: false,
    is_active: false
  });
  const [editValues, setEditValues] = useState({
    group: '',
    is_active: true
  });
  const [mode, setMode] = useState<'edit'|'delete'|'activate'|null>(null);
  const [loading, setLoading] = useState(false);
  const submitting = useRef(false);
  const [error, setError] = useState<string|null>(null);
  const [success, setSuccess] = useState<string|null>(null);
  const [operationResults, setOperationResults] = useState<{ id: string; status: 'pending'|'success'|'error'; message?: string }[]>([]);
  const [summary, setSummary] = useState<{ success: number; error: number }>({ success: 0, error: 0 });

  const resetDialogState = () => {
    setMode(null);
    setLoading(false);
    setError(null);
    setSuccess(null);
    setOperationResults([]);
    setSummary({ success: 0, error: 0 });
  };

  const handleFieldToggle = (field: string) => {
    setEditFields(prev => ({ ...prev, [field]: !prev[field as keyof typeof prev] }));
  };

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setEditValues(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleClose = () => {
    if (!loading) {
      resetDialogState();
      onClose();
    }
  };

  const runSelection = async (operation: () => Promise<void>) => {
    if (submitting.current) return;
    submitting.current = true;
    setLoading(true);
    setError(null);
    setSuccess(null);
    setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'pending' })));
    try {
      await operation();
      setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'success' })));
      setSummary({ success: selectedChannels.length, error: 0 });
      setSuccess('All operations completed successfully.');
    } catch (reason) {
      const message = getErrorMessage(reason);
      setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'error', message })));
      setSummary({ success: 0, error: selectedChannels.length });
      setError(`${selectedChannels.length} operation(s) failed, 0 succeeded.`);
    } finally {
      submitting.current = false;
      setLoading(false);
    }
  };

  const handleBulkEdit = async () => {
    const updates: ChannelUpdate = {};
    if (editFields.group) updates.group = editValues.group;
    if (editFields.is_active) updates.is_active = editValues.is_active;
    await runSelection(() => onBulkEdit(updates));
  };

  const handleBulkDelete = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    setOperationResults([]);
    setSummary({ success: 0, error: 0 });
    try {
      // Call bulk delete with all selected IDs
      await onBulkDelete(selectedChannels.map(ch => ch.id));
      setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'success' as const })));
      setSummary({ success: selectedChannels.length, error: 0 });
      setSuccess('All selected channels deleted successfully.');
    } catch (err) {
      // If error, mark all as failed
      setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'error' as const, message: getErrorMessage(err) })));
      setSummary({ success: 0, error: selectedChannels.length });
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleBulkActivate = async (active: boolean) => {
    await runSelection(() => onBulkActivate(active));
  };

  return (
    <Dialog aria-labelledby="bulk-operations-title" open={open} onClose={handleClose} maxWidth="sm" fullWidth fullScreen={isPhone}>
      <DialogTitle id="bulk-operations-title">Bulk Operations for {selectedChannels.length} Channels</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        <Box mb={2}>
          <Button variant="outlined" onClick={() => setMode('edit')} sx={{ mr: 1 }} disabled={loading}>Bulk Edit</Button>
          <Button variant="outlined" color="error" onClick={() => setMode('delete')} sx={{ mr: 1 }} disabled={loading}>Bulk Delete</Button>
          <Button variant="outlined" color="success" onClick={() => setMode('activate')} disabled={loading}>Bulk Activate/Deactivate</Button>
        </Box>
        {mode === 'edit' && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>Select fields to update:</Typography>
            <FormGroup>
              <Typography variant="body2" color="text.secondary">These changes apply to streams. Edit TV channel category, country and language in TV Channels.</Typography>
              <FormControlLabel control={<Checkbox checked={editFields.group} onChange={() => handleFieldToggle('group')} />} label="Group" />
              {editFields.group && <TextField name="group" label="Group" value={editValues.group} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
              <FormControlLabel control={<Checkbox checked={editFields.is_active} onChange={() => handleFieldToggle('is_active')} />} label="Active Status" />
              {editFields.is_active && <FormControlLabel control={<Switch checked={editValues.is_active} onChange={handleValueChange} name="is_active" color="primary" />} label="Active" />}
            </FormGroup>
          </Box>
        )}
        {mode === 'delete' && (
          <Box>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Are you sure you want to delete {selectedChannels.length} channels? This action cannot be undone.
            </Alert>
            <Box sx={{ maxHeight: 200, overflow: 'auto', mb: 2 }}>
              {selectedChannels.map(ch => (
                <Typography key={ch.id} variant="body2">• {ch.name || ch.id}</Typography>
              ))}
            </Box>
          </Box>
        )}
        {mode === 'activate' && (
          <Box>
            <Button variant="contained" color="success" onClick={() => handleBulkActivate(true)} disabled={loading} sx={{ mr: 1 }}>Activate All</Button>
            <Button variant="contained" color="warning" onClick={() => handleBulkActivate(false)} disabled={loading}>Deactivate All</Button>
          </Box>
        )}
        {operationResults.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2">Operation Results:</Typography>
            {operationResults.map(res => (
              <Box key={res.id} display="flex" alignItems="center" gap={1}>
                <Typography variant="body2">Channel ID: {res.id}</Typography>
                {res.status === 'pending' && <CircularProgress size={16} />}
                {res.status === 'success' && <Typography color="success.main">Success</Typography>}
                {res.status === 'error' && <Typography color="error.main">Error: {res.message}</Typography>}
              </Box>
            ))}
            <Typography variant="body2" mt={1}>Success: {summary.success} | Failed: {summary.error}</Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} color="inherit" disabled={loading}>Cancel</Button>
        {mode === 'edit' && <Button onClick={handleBulkEdit} color="primary" variant="contained" disabled={loading || Boolean(success) || !Object.values(editFields).some(Boolean)}>Update</Button>}
        {mode === 'delete' && <Button onClick={handleBulkDelete} color="error" variant="contained" disabled={loading || Boolean(success)}>Delete</Button>}
      </DialogActions>
      {loading && <Box display="flex" justifyContent="center" alignItems="center" p={2}><CircularProgress /></Box>}
    </Dialog>
  );
};

export default BulkOperations;

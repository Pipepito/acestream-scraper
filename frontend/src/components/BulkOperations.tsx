import React, { useState } from 'react';
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
  CircularProgress
} from '@mui/material';

interface BulkOperationsProps {
  open: boolean;
  onClose: () => void;
  selectedChannels: any[];
  onBulkEdit: (updates: any) => Promise<void>;
  onBulkDelete: (ids: any[]) => Promise<void>; // Accepts array of IDs for bulk delete
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
  const [editFields, setEditFields] = useState({
    category: false,
    country: false,
    language: false,
    is_active: false
  });
  const [editValues, setEditValues] = useState({
    category: '',
    country: '',
    language: '',
    is_active: true
  });
  const [mode, setMode] = useState<'edit'|'delete'|'activate'|null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);
  const [success, setSuccess] = useState<string|null>(null);
  const [operationResults, setOperationResults] = useState<{ id: any; status: 'pending'|'success'|'error'; message?: string }[]>([]);
  const [summary, setSummary] = useState<{ success: number; error: number }>({ success: 0, error: 0 });

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
    if (!loading) onClose();
  };

  const runPerChannel = async (fn: (channel: any) => Promise<any>) => {
    setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'pending' })));
    setSummary({ success: 0, error: 0 });
    setLoading(true);
    setError(null);
    setSuccess(null);
    let success = 0, error = 0;
    const results = await Promise.all(selectedChannels.map(async (ch, idx) => {
      try {
        await fn(ch);
        success++;
        return { id: ch.id, status: 'success' as const };
      } catch (err: any) {
        error++;
        const errorMsg = err?.message || 'Failed';
        return { id: ch.id, status: 'error' as const, message: errorMsg };
      }
    }));
    setOperationResults(results);
    setSummary({ success, error });
    setLoading(false);
    if (error === 0) {
      setSuccess('All operations completed successfully.');
      setTimeout(() => { setSuccess(null); onClose(); }, 1500);
    } else {
      setError(`${error} operation(s) failed, ${success} succeeded.`);
    }
  };

  const handleBulkEdit = async () => {
    setLoading(true);
    setError(null);
    try {
      const updates: any = {};
      Object.keys(editFields).forEach(field => {
        if (editFields[field as keyof typeof editFields]) {
          updates[field] = editValues[field as keyof typeof editValues];
        }
      });
      await runPerChannel(async (ch) => {
        await onBulkEdit({ ...updates, id: ch.id });
      });
    } catch (err: any) {
      setError(err.message || 'Bulk edit failed');
    } finally {
      setLoading(false);
    }
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
      setTimeout(() => { setSuccess(null); onClose(); }, 1500);
    } catch (err: any) {
      // If error, mark all as failed
      setOperationResults(selectedChannels.map(ch => ({ id: ch.id, status: 'error' as const, message: err?.message || 'Bulk delete failed' })));
      setSummary({ success: 0, error: selectedChannels.length });
      setError(err?.message || 'Bulk delete failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkActivate = async (active: boolean) => {
    setLoading(true);
    setError(null);
    try {
      await runPerChannel(async (ch) => {
        await onBulkActivate(active);
      });
    } catch (err: any) {
      setError(err.message || 'Bulk status update failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth fullScreen={window.innerWidth < 600}>
      <DialogTitle>Bulk Operations for {selectedChannels.length} Channels</DialogTitle>
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
              <FormControlLabel control={<Checkbox checked={editFields.category} onChange={() => handleFieldToggle('category')} />} label="Category" />
              {editFields.category && <TextField name="category" label="Category" value={editValues.category} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
              <FormControlLabel control={<Checkbox checked={editFields.country} onChange={() => handleFieldToggle('country')} />} label="Country" />
              {editFields.country && <TextField name="country" label="Country" value={editValues.country} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
              <FormControlLabel control={<Checkbox checked={editFields.language} onChange={() => handleFieldToggle('language')} />} label="Language" />
              {editFields.language && <TextField name="language" label="Language" value={editValues.language} onChange={handleValueChange} fullWidth sx={{ mb: 2 }} />}
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
        {mode === 'edit' && <Button onClick={handleBulkEdit} color="primary" variant="contained" disabled={loading}>Update</Button>}
        {mode === 'delete' && <Button onClick={handleBulkDelete} color="error" variant="contained" disabled={loading}>Delete</Button>}
      </DialogActions>
      {loading && <Box display="flex" justifyContent="center" alignItems="center" p={2}><CircularProgress /></Box>}
    </Dialog>
  );
};

export default BulkOperations;

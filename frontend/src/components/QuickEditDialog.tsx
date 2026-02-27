import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, Box, Alert, useMediaQuery, useTheme
} from '@mui/material';

interface QuickEditDialogProps {
  open: boolean;
  onClose: () => void;
  channel: any;
  onSave: (updates: any) => Promise<void>;
  fullScreen?: boolean;
}

const QuickEditDialog: React.FC<QuickEditDialogProps> = ({ open, onClose, channel, onSave, fullScreen }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [values, setValues] = useState({
    id: channel?.id || '',
    name: channel?.name || '',
    group: channel?.group || '',
    logo: channel?.logo || '',
    tvg_id: channel?.tvg_id || '',
    tvg_name: channel?.tvg_name || '',
    source_url: channel?.source_url || '',
    original_url: channel?.original_url || '',
    is_active: channel?.is_active ?? true,
    epg_update_protected: channel?.epg_update_protected ?? false,
  });
  const [error, setError] = useState<string|null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  React.useEffect(() => {
    setValues({
      id: channel?.id || '',
      name: channel?.name || '',
      group: channel?.group || '',
      logo: channel?.logo || '',
      tvg_id: channel?.tvg_id || '',
      tvg_name: channel?.tvg_name || '',
      source_url: channel?.source_url || '',
      original_url: channel?.original_url || '',
      is_active: channel?.is_active ?? true,
      epg_update_protected: channel?.epg_update_protected ?? false,
    });
  }, [channel]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setValues(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const handleSave = async () => {
    setError(null);
    setLoading(true);
    try {
      await onSave(values);
      setSuccess(true);
      setTimeout(() => { setSuccess(false); onClose(); }, 1000);
    } catch (err: any) {
      setError(err.message || 'Quick edit failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth fullScreen={fullScreen ?? isMobile}>
      <DialogTitle>Quick Edit Channel</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>Saved successfully!</Alert>}
        <Box mb={2}>
          <TextField name="name" label="Name" value={values.name} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <TextField
            name="id"
            label="Acestream ID (hash)"
            value={values.id}
            onChange={handleChange}
            fullWidth
            sx={{ mb: 2 }}
            required
            InputProps={{ readOnly: !!channel?.id }}
            helperText={!!channel?.id ? 'Acestream ID cannot be changed after creation.' : 'Required'}
          />
          <TextField name="group" label="Group" value={values.group} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <TextField name="logo" label="Logo URL" value={values.logo} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <TextField name="tvg_id" label="TVG ID" value={values.tvg_id} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <TextField name="tvg_name" label="TVG Name" value={values.tvg_name} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <TextField name="source_url" label="Source URL" value={values.source_url} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <TextField name="original_url" label="Original URL" value={values.original_url} onChange={handleChange} fullWidth sx={{ mb: 2 }} />
          <label>
            <input type="checkbox" name="is_active" checked={!!values.is_active} onChange={handleChange} /> Active
          </label>
          <Box component="span" sx={{ ml: 2 }}>
            <label>
              <input type="checkbox" name="epg_update_protected" checked={!!values.epg_update_protected} onChange={handleChange} /> EPG Update Protected
            </label>
          </Box>
          {/* Advanced/readonly fields */}
          <Box mt={2}>
            <TextField label="Last Seen" value={channel?.last_seen || ''} fullWidth sx={{ mb: 2 }} InputProps={{ readOnly: true }} />
            <TextField label="Last Checked" value={channel?.last_checked || ''} fullWidth sx={{ mb: 2 }} InputProps={{ readOnly: true }} />
            <TextField label="Check Error" value={channel?.check_error || ''} fullWidth sx={{ mb: 2 }} InputProps={{ readOnly: true }} />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button onClick={handleSave} variant="contained" disabled={loading}>Save</Button>
      </DialogActions>
    </Dialog>
  );
};

export default QuickEditDialog;

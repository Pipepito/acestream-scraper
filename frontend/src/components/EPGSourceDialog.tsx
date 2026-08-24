import React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Switch,
  TextField,
} from '@mui/material';
import { EPGSourceFormData } from '../hooks/useEPGSourceManagement';

interface EPGSourceDialogProps {
  open: boolean;
  isEdit: boolean;
  formData: EPGSourceFormData;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onClose: () => void;
  onSubmit: () => void;
}

const EPGSourceDialog: React.FC<EPGSourceDialogProps> = ({
  open,
  isEdit,
  formData,
  onChange,
  onClose,
  onSubmit,
}) => (
  <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
    <DialogTitle>
      {isEdit ? 'Edit EPG Source' : 'Add EPG Source'}
    </DialogTitle>
    <DialogContent>
      <TextField
        margin="dense"
        name="name"
        label="Name"
        fullWidth
        value={formData.name}
        onChange={onChange}
        sx={{ mb: 2 }}
      />
      <TextField
        margin="dense"
        name="url"
        label="URL"
        fullWidth
        value={formData.url}
        onChange={onChange}
        sx={{ mb: 2 }}
        placeholder="https://example.com/epg.xml"
      />
      <FormControlLabel
        control={
          <Switch
            name="enabled"
            checked={formData.enabled}
            onChange={onChange}
          />
        }
        label="Enabled"
      />
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>Cancel</Button>
      <Button
        onClick={onSubmit}
        variant="contained"
        color="primary"
        disabled={!formData.url || !formData.name}
      >
        {isEdit ? 'Update' : 'Add'}
      </Button>
    </DialogActions>
  </Dialog>
);

export default EPGSourceDialog;

import React from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import { TVChannelFormErrors } from '../hooks/useTVChannelForm';

interface TVChannelFormDialogProps {
  mode: 'create' | 'edit';
  open: boolean;
  formData: TVChannelCreate | TVChannelUpdate;
  formErrors: TVChannelFormErrors;
  submitting: boolean;
  dialogProps: {
    fullScreen: boolean;
    fullWidth?: boolean;
    maxWidth?: 'sm';
  };
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onClose: () => void;
  onSubmit: () => void;
}

const TVChannelFormDialog: React.FC<TVChannelFormDialogProps> = ({
  mode,
  open,
  formData,
  formErrors,
  submitting,
  dialogProps,
  onChange,
  onClose,
  onSubmit,
}) => (
  <Dialog open={open} onClose={onClose} {...dialogProps}>
    <DialogTitle>{mode === 'create' ? 'Add TV Channel' : 'Edit TV Channel'}</DialogTitle>
    <DialogContent dividers>
      {formErrors.submit ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {formErrors.submit}
        </Alert>
      ) : null}
      <Stack spacing={2.5} sx={{ py: 1 }}>
        <TextField
          name="name"
          label="Channel Name"
          fullWidth
          value={formData.name || ''}
          onChange={onChange}
          required
          error={Boolean(formErrors.name)}
          helperText={formErrors.name}
        />
        <TextField
          name="description"
          label="Description"
          fullWidth
          value={formData.description || ''}
          onChange={onChange}
          multiline
          rows={3}
          inputProps={{ maxLength: 1000 }}
        />

        <Box>
          <Typography variant="helperText" sx={{ display: 'block', mb: 1 }}>
            Optional details
          </Typography>
          <Stack spacing={2}>
            <TextField name="logo_url" label="Logo URL" fullWidth value={formData.logo_url || ''} onChange={onChange} />
            <TextField name="category" label="Category" fullWidth value={formData.category || ''} onChange={onChange} />
            <TextField name="country" label="Country" fullWidth value={formData.country || ''} onChange={onChange} />
            <TextField name="language" label="Language" fullWidth value={formData.language || ''} onChange={onChange} />
            {mode === 'edit' ? <TextField name="epg_id" label="EPG ID" fullWidth value={formData.epg_id || ''} onChange={onChange} /> : null}
            <TextField name="channel_number" label="Channel Number" type="number" fullWidth value={formData.channel_number || ''} onChange={onChange} />
          </Stack>
        </Box>

        <Stack spacing={1}>
          <FormControlLabel
            control={<Switch checked={formData.is_active === true} onChange={onChange} name="is_active" color="primary" />}
            label="Active"
          />
          <FormControlLabel
            control={<Switch checked={formData.is_favorite === true} onChange={onChange} name="is_favorite" color="primary" />}
            label="Favorite"
          />
        </Stack>
      </Stack>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>Cancel</Button>
      <Button onClick={onSubmit} variant="contained" color="primary" disabled={submitting}>
        {mode === 'create' ? 'Create' : 'Update'}
      </Button>
    </DialogActions>
  </Dialog>
);

export default TVChannelFormDialog;

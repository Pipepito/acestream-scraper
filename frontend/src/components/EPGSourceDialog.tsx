import { useUiText } from '../i18n/useUiText';
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
import { epgProviders } from '../services/epgProviders';
import { EPGSourceFormData } from '../hooks/useEPGSourceManagement';

interface EPGSourceDialogProps {
  open: boolean;
  isEdit: boolean;
  formData: EPGSourceFormData;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSelectProvider?: (provider: { name: string; url: string }) => void;
  onClose: () => void;
  onSubmit: () => void;
}

const EPGSourceDialog: React.FC<EPGSourceDialogProps> = ({
  open,
  isEdit,
  formData,
  onChange,
  onSelectProvider,
  onClose,
  onSubmit,
}) => { const tUi = useUiText(); return (
  <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
    <DialogTitle>
      {isEdit ? tUi("Edit EPG Source") : tUi("Add EPG Source")}
    </DialogTitle>
    <DialogContent>
      {!isEdit && onSelectProvider ? epgProviders.map(provider => <Button key={provider.id} onClick={() => onSelectProvider(provider)}>{tUi("Use")}{' '}{provider.name}</Button>) : null}
      <TextField
        margin="dense"
        name="name"
        label={tUi("Name")}
        fullWidth
        value={formData.name}
        onChange={onChange}
        sx={{ mb: 2 }}
      />
      <TextField
        margin="dense"
        name="url"
        label={tUi("URL")}
        fullWidth
        value={formData.url}
        onChange={onChange}
        sx={{ mb: 2 }}
        placeholder={tUi("https://example.com/epg.xml")}
        helperText={tUi("XMLTV, TV Rioja weekday schedule, or a Sincroguía /programacion/ channel page. Football schedules belong in Events.")}
      />
      <FormControlLabel
        control={
          <Switch
            name="enabled"
            checked={formData.enabled}
            onChange={onChange}
          />
        }
        label={tUi("Enabled")}
      />
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>{tUi("Cancel")}</Button>
      <Button
        onClick={onSubmit}
        variant="contained"
        color="primary"
        disabled={!formData.url || !formData.name}
      >
        {isEdit ? tUi("Update") : tUi("Add")}
      </Button>
    </DialogActions>
  </Dialog>
); };

export default EPGSourceDialog;

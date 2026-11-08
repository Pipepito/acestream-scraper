import {
Alert,Button,
Dialog,
DialogActions,
DialogContent,
DialogTitle
} from '@mui/material';
import React from 'react';
import { EPGSourceFormData } from '../hooks/useEPGSourceManagement';
import { useUiText } from '../i18n/useUiText';
import { epgProviders } from '../services/epgProviders';
import GuideSourceFields from './GuideSourceFields';

interface EPGSourceDialogProps {
  open: boolean;
  isEdit: boolean;
  formData: EPGSourceFormData;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSelectProvider?: (provider: { name: string; url: string }) => void;
  onClose: () => void;
  onSubmit: () => void;
  pending?: boolean;
  error?: string;
}

const EPGSourceDialog: React.FC<EPGSourceDialogProps> = ({
  open,
  isEdit,
  formData,
  onChange,
  onSelectProvider,
  onClose,
  onSubmit,
  pending = false,
  error,
}) => { const tUi = useUiText(); return (
  <Dialog open={open} onClose={pending ? undefined : onClose} maxWidth="md" fullWidth>
    <DialogTitle>
      {isEdit ? tUi("Edit EPG Source") : tUi("Add EPG Source")}
    </DialogTitle>
    <DialogContent>
      {!isEdit && onSelectProvider ? epgProviders.map(provider => <Button key={provider.id} disabled={pending} onClick={() => onSelectProvider(provider)}>{tUi("Use")}{' '}{provider.name}</Button>) : null}
      <GuideSourceFields value={formData} onChange={onChange} disabled={pending} />
      {error ? <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert> : null}
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose} disabled={pending}>{tUi("Cancel")}</Button>
      <Button
        onClick={onSubmit}
        variant="contained"
        color="primary"
        disabled={pending || !formData.url.trim() || !formData.name.trim()}
      >
        {isEdit ? tUi("Update") : tUi("Add")}
      </Button>
    </DialogActions>
  </Dialog>
); };

export default EPGSourceDialog;

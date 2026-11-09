import { useUiText } from '../i18n/useUiText';
import React, { useLayoutEffect, useRef, useState } from 'react';
import {
  Alert,
  Autocomplete,
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
import { translateKnown } from '../i18n/text';
import { getErrorMessage } from '../utils/errorUtils';
import { useUnsavedChanges } from './UnsavedChanges';
import { useConfirm } from './ConfirmDialog';
import { TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';
import { TVChannelFormErrors } from '../hooks/useTVChannelForm';
import { useQuery } from '@tanstack/react-query';
import { tvChannelService } from '../services/tvChannelService';
import { useTranslation } from 'react-i18next';

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
}) => {
  const tUi = useUiText();
  const { i18n } = useTranslation();
  const definitions = useQuery({ queryKey: ['categoryDefinitions'], queryFn: tvChannelService.categoryDefinitions, enabled: open, staleTime: Infinity });
  const current = JSON.stringify(formData);
  const [initial, setInitial] = useState(current);
  const wasOpen = useRef(false);
  useLayoutEffect(() => { if (open && !wasOpen.current) setInitial(current); wasOpen.current = open; }, [open, current]);
  const dirty = open && current !== initial;
  useUnsavedChanges(dirty, open && submitting);
  const { confirm, dialog } = useConfirm();
  const close = async () => {
    if (submitting) return;
    if (dirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onClose();
  };
  return (<>
  {dialog}
  <Dialog open={open} onClose={() => void close()} {...dialogProps}>
    <DialogTitle>{mode === 'create' ? tUi("Add TV Channel") : tUi("Edit TV Channel")}</DialogTitle>
    <DialogContent dividers>
      {formErrors.submit != null ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {getErrorMessage(formErrors.submit)}
        </Alert>
      ) : null}
      <Stack component="fieldset" disabled={submitting} spacing={2.5} sx={{ py: 1, px: 0, m: 0, border: 0, minWidth: 0 }}>
        <TextField
          name="name"
          label={tUi("Channel Name")}
          fullWidth
          value={formData.name || ''}
          onChange={onChange}
          required
          error={Boolean(formErrors.name)}
          helperText={formErrors.name ? translateKnown(formErrors.name) : undefined}
        />
        <TextField
          name="description"
          label={tUi("Description")}
          fullWidth
          value={formData.description || ''}
          onChange={onChange}
          multiline
          rows={3}
          inputProps={{ maxLength: 1000 }}
        />

        <Box>
          <Typography variant="helperText" sx={{ display: 'block', mb: 1 }}>
            {tUi("Optional details")}</Typography>
          <Stack spacing={2}>
            <TextField name="logo_url" label={tUi("Logo URL")} fullWidth value={formData.logo_url || ''} onChange={onChange} />
            <Autocomplete freeSolo options={definitions.data?.map(item => item.id) ?? []} value={formData.category || ''}
              getOptionLabel={value => { const item = definitions.data?.find(row => row.id === value); return item ? i18n.resolvedLanguage?.startsWith('es') ? item.label_es : item.label : value; }}
              onInputChange={(_, value, reason) => { if (reason === 'input' || reason === 'clear') onChange({ target: { name: 'category', value, type: 'text' } } as React.ChangeEvent<HTMLInputElement>); }}
              onChange={(_, value) => onChange({ target: { name: 'category', value: value ?? '', type: 'text' } } as React.ChangeEvent<HTMLInputElement>)}
              renderInput={params => <TextField {...params} name="category" label={tUi('Channel category')} helperText={tUi('Choose a category or enter your own. This stays independent of current programmes.')} />} />
            <TextField name="country" label={tUi("Country")} fullWidth value={formData.country || ''} onChange={onChange} />
            <TextField name="language" label={tUi("Language")} fullWidth value={formData.language || ''} onChange={onChange} />
            {mode === 'edit' ? <TextField name="epg_id" label={tUi("EPG ID")} fullWidth value={formData.epg_id || ''} onChange={onChange} /> : null}
            <TextField name="channel_number" label={tUi("Channel Number")} type="number" fullWidth value={formData.channel_number ?? ''} onChange={onChange} />
          </Stack>
        </Box>

        <Stack spacing={1}>
          <FormControlLabel
            control={<Switch checked={formData.is_active === true} onChange={onChange} name="is_active" color="primary" />}
            label={tUi("Active")}
          />
          <FormControlLabel
            control={<Switch checked={formData.is_favorite === true} onChange={onChange} name="is_favorite" color="primary" />}
            label={tUi("Favorite")}
          />
        </Stack>
      </Stack>
    </DialogContent>
    <DialogActions>
      <Button disabled={submitting} onClick={() => void close()}>{tUi("Cancel")}</Button>
      <Button onClick={onSubmit} variant="contained" color="primary" disabled={submitting}>
        {mode === 'create' ? tUi("Create") : tUi("Update")}
      </Button>
    </DialogActions>
  </Dialog>
</>); };

export default TVChannelFormDialog;

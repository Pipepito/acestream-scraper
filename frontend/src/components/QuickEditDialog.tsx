import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import type { AcestreamChannel } from '../services/channelService';
import { getErrorMessage } from '../utils/errorUtils';
import { ApiError } from '../services/apiErrors';
import { formatRelativeTime } from '../utils/format';

export interface QuickEditValues {
  id: string;
  name: string;
  group: string;
  logo: string;
  tvg_id: string;
  tvg_name: string;
  is_active: boolean;
  epg_update_protected: boolean;
}

export type QuickEditChannel = Partial<AcestreamChannel> & { id?: string };

export interface QuickEditDialogProps {
  open: boolean;
  onClose: () => void;
  channel: QuickEditChannel | null;
  onSave: (values: QuickEditValues) => Promise<void>;
  /** "create" asks for the Acestream ID; "edit" keeps it read-only. Defaults to edit when the channel has an id. */
  mode?: 'edit' | 'create';
  fullScreen?: boolean;
}

const toValues = (channel: QuickEditChannel | null): QuickEditValues => ({
  id: channel?.id ?? '',
  name: channel?.name ?? '',
  group: channel?.group ?? '',
  logo: channel?.logo ?? '',
  tvg_id: channel?.tvg_id ?? '',
  tvg_name: channel?.tvg_name ?? '',
  is_active: channel?.is_active ?? true,
  epg_update_protected: channel?.epg_update_protected ?? false,
});

const QuickEditDialog: React.FC<QuickEditDialogProps> = ({ open, onClose, channel, onSave, mode, fullScreen }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const creating = mode ? mode === 'create' : !channel?.id;
  const [values, setValues] = useState<QuickEditValues>(() => toValues(channel));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setValues(toValues(channel));
    setError(null);
  }, [channel, open]);

  const setField = (field: keyof QuickEditValues) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const next = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setValues((prev) => ({ ...prev, [field]: next }));
  };

  const handleSave = async () => {
    setError(null);
    setSaving(true);
    try {
      await onSave({ ...values, id: values.id.trim(), name: values.name.trim() });
    } catch (err) {
      setError(err instanceof ApiError ? getErrorMessage(err) : err instanceof Error && err.message ? err.message : getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const summary = !creating && channel
    ? [
        `Last checked ${formatRelativeTime(channel.last_checked)}`,
        `Last scraped ${formatRelativeTime(channel.last_seen)}`,
        ...(channel.check_error ? [`Last error: ${channel.check_error}`] : []),
      ].join(' · ')
    : null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth fullScreen={fullScreen ?? isMobile} aria-labelledby="quick-edit-title">
      <DialogTitle id="quick-edit-title">{creating ? 'Add channel' : 'Edit channel'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField label="Name" value={values.name} onChange={setField('name')} fullWidth required />
          <TextField
            label="Acestream ID"
            value={values.id}
            onChange={setField('id')}
            fullWidth
            required
            InputProps={{ readOnly: !creating, sx: { fontFamily: 'monospace' } }}
            helperText={creating ? '40-character hash from the source or the engine search.' : 'The ID cannot be changed after creation.'}
          />
          <TextField label="Group" value={values.group} onChange={setField('group')} fullWidth />
          <TextField label="Logo URL" value={values.logo} onChange={setField('logo')} fullWidth />
          <TextField label="TVG ID" value={values.tvg_id} onChange={setField('tvg_id')} fullWidth helperText="EPG channel id written to the playlist." />
          <TextField label="TVG Name" value={values.tvg_name} onChange={setField('tvg_name')} fullWidth />
          <FormControlLabel
            control={<Checkbox checked={values.is_active} onChange={setField('is_active')} />}
            label="Show in playlist"
          />
          <FormControlLabel
            control={<Checkbox checked={values.epg_update_protected} onChange={setField('epg_update_protected')} />}
            label="Keep my EPG fields (protect from EPG updates)"
            sx={{ mt: -1.5 }}
          />
          {summary ? (
            <Typography variant="body2" color="text.secondary">
              {summary}
            </Typography>
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={saving || !values.name.trim() || !values.id.trim()}>
          {saving ? 'Saving…' : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default QuickEditDialog;

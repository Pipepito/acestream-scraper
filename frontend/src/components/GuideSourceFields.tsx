import React from 'react';
import { FormControlLabel, Stack, Switch, TextField } from '@mui/material';
import { useUiText } from '../i18n/useUiText';
import type { EPGSourceFormData } from '../hooks/useEPGSourceManagement';

/** The same guide fields and constraints in setup and subsequent guide management. */
export default function GuideSourceFields({ value, onChange, disabled = false }: {
  value: EPGSourceFormData; onChange: (event: React.ChangeEvent<HTMLInputElement>) => void; disabled?: boolean;
}) {
  const t = useUiText();
  return <Stack spacing={2} sx={{ pt: 1 }}>
    <TextField name="name" label={t('Guide name')} fullWidth required disabled={disabled} value={value.name} onChange={onChange} inputProps={{ maxLength: 255 }} />
    <TextField name="url" label={t('Programme guide link')} fullWidth required disabled={disabled} value={value.url} onChange={onChange} inputProps={{ maxLength: 4096 }}
      helperText={t('XMLTV, TV Rioja weekday schedule, or a Sincroguía /programacion/ channel page. Football schedules belong in Events.')} />
    <FormControlLabel control={<Switch name="enabled" checked={value.enabled} disabled={disabled} onChange={onChange} />} label={t('Enabled')} />
  </Stack>;
}

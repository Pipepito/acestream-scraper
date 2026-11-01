import React from 'react';
import { Alert, Box, Checkbox, FormControlLabel, Link, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import type { SetupState } from '../../services/setupService';

interface NetworkSettingsFieldsProps {
  initial: SetupState;
  values: SetupState['runtime'];
  disabled: boolean;
  onChange: (values: SetupState['runtime']) => void;
}

export default function NetworkSettingsFields({ initial, values, disabled, onChange }: NetworkSettingsFieldsProps) {
  const broadProxies = String(values.FORWARDED_ALLOW_IPS ?? '').split(',').some(value =>
    ['*', '0.0.0.0/0', '::/0', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7'].includes(value.trim()));
  return <>
    <Alert severity={initial.api_protected ? 'success' : 'info'}>{initial.api_protected ? 'API token protection is enabled.' : 'No API token is configured.'} Manage user accounts in <Link component={RouterLink} to="/settings?tab=access">Settings → Access</Link>.</Alert>
    {initial.saved_overrides?.PUBLIC_BASE_URL ? <Alert severity="info">Public address saved in Integrations: {initial.saved_overrides.PUBLIC_BASE_URL}. This takes precedence over the runtime default. <Link component={RouterLink} to="/integrations/public-address">Edit public address</Link></Alert> : null}
    {broadProxies ? <Alert severity="warning">Trusted reverse proxies includes entire private networks or all addresses. This can block local HTTP sign-in and TV discovery by treating your browser as a proxy. Replace those entries with your actual proxy addresses; adding a narrower range does not remove the old ones.</Alert> : null}
    {initial.options.filter(option => option.group === 'network').map(option => {
      const value = values[option.name] ?? option.default;
      if (option.kind === 'boolean') return <Box key={option.name}>
        <FormControlLabel label={option.label} control={<Checkbox checked={value === true} disabled={disabled} onChange={(_, checked) => onChange({ [option.name]: checked })} />} />
        <Typography variant="body2" color="text.secondary">{option.help}</Typography>
      </Box>;
      return <TextField key={option.name} label={option.label} value={value} disabled={disabled} fullWidth
        helperText={option.help} inputProps={{ maxLength: 4096 }} onChange={event => onChange({ [option.name]: event.target.value })} />;
    })}
  </>;
}

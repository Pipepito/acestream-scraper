import React, { useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';
import ContentSection from '../layout/ContentSection';
import { getApiToken, setApiToken } from '../../services/apiToken';
import NewPasswordField, { PASSWORD_REQUIREMENT, validNewPassword } from './NewPasswordField';
import AccountTransportNotice from './AccountTransportNotice';

export default function AccountSetup() {
  const access = useAccess();
  const [enabled, setEnabled] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [migrate, setMigrate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [legacy, setLegacy] = useState(getApiToken() ?? '');
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('');
    if (enabled && !validNewPassword(password)) { setError(PASSWORD_REQUIREMENT); return; }
    if (enabled && password !== confirmation) { setError('The passwords do not match.'); return; }
    setBusy(true);
    try {
      if (access?.status.legacy_token) setApiToken(legacy.trim());
      await accessService.bootstrap({ enabled, username: enabled ? username : 'unused', password: enabled ? password : 'unused', password_confirmation: enabled ? confirmation : 'unused', migrate_legacy_token: migrate });
      setPassword(''); setConfirmation('');
      await access?.refresh();
    } catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  return <ContentSection title="Who can use this installation?" description="Choose how people access your channels and settings. You can change this later in Settings → Access.">
    <Stack component="form" aria-label="Account setup" onSubmit={submit} spacing={2} sx={{ maxWidth: 560 }}>
      <FormControlLabel control={<Checkbox checked={enabled} onChange={(_, value) => setEnabled(value)} />} label="Enable user management" />
      <Typography>User management protects settings with a login and lets you give other people viewing and casting permissions. Public viewing and local IPTV access can be allowed separately.</Typography>
      {access?.status.legacy_token ? <TextField label="Existing API token" type="password" required value={legacy} onChange={e => setLegacy(e.target.value)} autoComplete="off" /> : null}
      {enabled ? <>
        <AccountTransportNotice />
        <Typography variant="body2">Accounts work over HTTPS or through the server’s private IP address on your home network. HTTP on your home network is not encrypted.</Typography>
        <TextField label="Administrator username" required value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" inputProps={{ maxLength: 64, pattern: '[a-zA-Z0-9_.\\-]+' }} />
        <NewPasswordField label="Password" value={password} onChange={setPassword} />
        <TextField label="Confirm password" required type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} autoComplete="new-password" />
        {access?.status.legacy_token ? <Alert severity="warning"><FormControlLabel control={<Checkbox checked={migrate} onChange={(_, value) => setMigrate(value)} />} label="Keep the existing API token for playback only" /><Typography variant="body2">Existing administrative scripts will need a new header credential from Settings → Access. Replace shared playlist tokens when ready.</Typography></Alert> : null}
      </> : <Alert severity="warning">Anyone who can reach this installation can manage it when user management is off. Existing API-token protection is retained.</Alert>}
      {error ? <Alert severity="error">{error}</Alert> : null}
      <Button type="submit" variant="contained" disabled={busy || (enabled && (access?.status.account_transport === 'blocked' || (Boolean(access?.status.legacy_token) && !migrate)))}>{busy ? 'Saving…' : enabled ? 'Create administrator and continue' : 'Continue without accounts'}</Button>
      <Typography variant="body2" color="text.secondary">If you lose your password, the container owner can reset it with a command.</Typography>
    </Stack>
  </ContentSection>;
}

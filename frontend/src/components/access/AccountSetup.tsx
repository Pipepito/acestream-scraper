import React, { useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';
import ContentSection from '../layout/ContentSection';
import { getApiToken, setApiToken } from '../../services/apiToken';

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
    <Stack component="form" onSubmit={submit} spacing={2} sx={{ maxWidth: 560 }}>
      <FormControlLabel control={<Checkbox checked={enabled} onChange={(_, value) => setEnabled(value)} />} label="Enable user management" />
      <Typography>User management protects settings with a login and lets you give other people viewing and casting permissions. Public viewing and local IPTV access can be allowed separately.</Typography>
      {access?.status.legacy_token ? <TextField label="Existing API token" type="password" required value={legacy} onChange={e => setLegacy(e.target.value)} autoComplete="off" /> : null}
      {enabled ? <>
        <Typography variant="body2">Use HTTPS for account setup and sign-in. Local setup through localhost also works.</Typography>
        <TextField label="Administrator username" required value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" inputProps={{ maxLength: 64, pattern: '[a-zA-Z0-9_.\\-]+' }} />
        <TextField label="Password" required type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" helperText="Use 12–128 characters." inputProps={{ minLength: 12, maxLength: 128 }} />
        <TextField label="Confirm password" required type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} autoComplete="new-password" />
        {access?.status.legacy_token ? <Alert severity="warning"><FormControlLabel control={<Checkbox checked={migrate} onChange={(_, value) => setMigrate(value)} />} label="Keep the existing API token for playback only" /><Typography variant="body2">Existing administrative scripts will need a new header credential from Settings → Access. Replace shared playlist tokens when ready.</Typography></Alert> : null}
      </> : <Alert severity="warning">Anyone who can reach this installation can manage it when user management is off. Existing API-token protection is retained.</Alert>}
      {error ? <Alert severity="error">{error}</Alert> : null}
      <Button type="submit" variant="contained" disabled={busy || (enabled && Boolean(access?.status.legacy_token) && !migrate)}>{busy ? 'Saving…' : enabled ? 'Create administrator and continue' : 'Continue without accounts'}</Button>
      <Typography variant="body2" color="text.secondary">No Docker settings or setup secrets are needed. If you lose your password, the container owner can reset it with a command.</Typography>
    </Stack>
  </ContentSection>;
}

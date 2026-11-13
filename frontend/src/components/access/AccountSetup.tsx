import { useUnsavedChanges } from '../UnsavedChanges';
import { useUiText } from '../../i18n/useUiText';
import React, { useRef, useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, Stack, TextField, Typography } from '@mui/material';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';
import ContentSection from '../layout/ContentSection';
import { getApiToken, setApiToken } from '../../services/apiToken';
import NewPasswordField, { validNewPassword } from './NewPasswordField';
import AccountTransportNotice from './AccountTransportNotice';

export default function AccountSetup() {
  const tUi = useUiText();
  const access = useAccess();
  const [enabled, setEnabled] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [migrate, setMigrate] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [validation, setValidation] = useState<'length' | 'mismatch' | null>(null);
  const submitting = useRef(false);
  const [legacy, setLegacy] = useState(getApiToken() ?? '');
  const initialToken = useRef(legacy);
  useUnsavedChanges(Boolean(username || password || confirmation || migrate || !enabled || legacy !== initialToken.current), busy);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current) return;
    setError(null); setValidation(null);
    if (enabled && !validNewPassword(password)) { setValidation('length'); return; }
    if (enabled && password !== confirmation) { setValidation('mismatch'); return; }
    submitting.current = true; setBusy(true);
    try {
      if (access?.status.legacy_token) setApiToken(legacy.trim());
      await accessService.bootstrap({ enabled, username: enabled ? username : 'unused', password: enabled ? password : 'unused', password_confirmation: enabled ? confirmation : 'unused', migrate_legacy_token: migrate });
      setPassword(''); setConfirmation('');
      await access?.refresh();
    } catch (reason) { setError(reason); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <ContentSection title={tUi("Who can use this installation?")} description={tUi("Choose how people access your channels and settings. You can change this later in Settings → Access.")}>
    <Stack component="form" aria-label={tUi("Account setup")} onSubmit={submit} spacing={2} sx={{ maxWidth: 560 }}>
      <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControlLabel control={<Checkbox checked={enabled} onChange={(_, value) => setEnabled(value)} />} label={tUi("Enable user management")} />
      <Typography>{tUi("User management protects settings with a login and lets you give other people viewing and casting permissions. Public viewing and local IPTV access can be allowed separately.")}</Typography>
      <Typography variant="body2">{tUi("TV control follows app access. Set CAST_REQUIRE_HOME_NETWORK=true on the container to limit it to home networks, or enable accounts.")}</Typography>
      {access?.status.legacy_token ? <TextField label={tUi("Existing API token")} type="password" required value={legacy} onChange={e => setLegacy(e.target.value)} autoComplete="off" /> : null}
      {enabled ? <>
        <AccountTransportNotice />
        <Typography variant="body2">{tUi("Accounts work over HTTPS or through the server’s private IP address on your home network. HTTP on your home network is not encrypted.")}</Typography>
        <TextField label={tUi("Administrator username")} required value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" inputProps={{ maxLength: 64, pattern: '[a-zA-Z0-9_.\\-]+' }} />
        <NewPasswordField label={tUi("Password")} value={password} onChange={setPassword} />
        <TextField label={tUi("Confirm password")} required type="password" value={confirmation} onChange={e => setConfirmation(e.target.value)} autoComplete="new-password" />
        {access?.status.legacy_token ? <Alert severity="warning"><FormControlLabel control={<Checkbox checked={migrate} onChange={(_, value) => setMigrate(value)} />} label={tUi("Keep the existing API token for playback only")} /><Typography variant="body2">{tUi("Existing administrative scripts will need a new header credential from Settings → Access. Replace shared playlist tokens when ready.")}</Typography></Alert> : null}
      </> : <Alert severity="warning">{tUi("Anyone who can reach this installation can manage it when user management is off. Existing API-token protection is retained.")}</Alert>}
      {validation ? <Alert severity="error">{validation === 'length' ? tUi("Use 12–128 characters.") : tUi("The passwords do not match.")}</Alert> : error ? <Alert severity="error">{getAccessErrorMessage(error)}</Alert> : null}
      <Button type="submit" variant="contained" disabled={busy || (enabled && (access?.status.account_transport === 'blocked' || (Boolean(access?.status.legacy_token) && !migrate)))}>{busy ? tUi("Saving…") : enabled ? tUi("Create administrator and continue") : tUi("Continue without accounts")}</Button>
      <Typography variant="body2" color="text.secondary">{tUi("If you lose your password, the container owner can reset it with a command.")}</Typography>
      </Box>
    </Stack>
  </ContentSection>;
}

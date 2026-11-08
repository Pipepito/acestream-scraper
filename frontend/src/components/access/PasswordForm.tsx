import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Button, Stack, TextField } from '@mui/material';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import ContentSection from '../layout/ContentSection';
import { getAccessErrorMessage } from '../../services/accessErrors';
import NewPasswordField, { PASSWORD_REQUIREMENT, validNewPassword } from './NewPasswordField';

export default function PasswordForm() {
  const tUi = useUiText();
  const access = useAccess();
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError('');
    if (!validNewPassword(password)) { setError(PASSWORD_REQUIREMENT); return; }
    if (password !== confirmation) { setError(tUi("The passwords do not match.")); return; }
    setBusy(true);
    try { await accessService.password({ current_password: current, password, password_confirmation: confirmation }); setCurrent(''); setPassword(''); setConfirmation(''); await access?.refresh(); }
    catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  return <ContentSection title={tUi("Change your password")} description={tUi("Changing your password signs out your sessions and revokes your API credentials.")}>
    <Stack component="form" aria-label={tUi("Change password")} onSubmit={submit} spacing={2} sx={{ maxWidth: 480 }}>
      <TextField required type="password" label={tUi("Current password")} autoComplete="current-password" value={current} onChange={e => setCurrent(e.target.value)} />
      <NewPasswordField label={tUi("New password")} value={password} onChange={setPassword} />
      <TextField required type="password" label={tUi("Confirm new password")} autoComplete="new-password" value={confirmation} onChange={e => setConfirmation(e.target.value)} />
      {error ? <Alert severity="error">{error}</Alert> : null}
      <Button variant="contained" type="submit" disabled={busy}>{tUi("Change password")}</Button>
    </Stack>
  </ContentSection>;
}

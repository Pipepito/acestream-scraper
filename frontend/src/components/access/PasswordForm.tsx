import { useUnsavedChanges } from '../UnsavedChanges';
import { useUiText } from '../../i18n/useUiText';
import React, { useRef, useState } from 'react';
import { Alert, Box, Button, Stack, TextField } from '@mui/material';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import ContentSection from '../layout/ContentSection';
import { getAccessErrorMessage } from '../../services/accessErrors';
import NewPasswordField, { validNewPassword } from './NewPasswordField';

export default function PasswordForm() {
  const tUi = useUiText();
  const access = useAccess();
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [validation, setValidation] = useState<'length' | 'mismatch' | null>(null);
  const submitting = useRef(false);
  useUnsavedChanges(Boolean(current || password || confirmation), busy);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current) return;
    setError(null); setValidation(null);
    if (!validNewPassword(password)) { setValidation('length'); return; }
    if (password !== confirmation) { setValidation('mismatch'); return; }
    submitting.current = true; setBusy(true);
    try { await accessService.password({ current_password: current, password, password_confirmation: confirmation }); setCurrent(''); setPassword(''); setConfirmation(''); await access?.refresh(); }
    catch (reason) { setError(reason); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <ContentSection title={tUi("Change your password")} description={tUi("Changing your password signs out your sessions and revokes your API credentials.")}>
    <Stack component="form" aria-label={tUi("Change password")} onSubmit={submit} spacing={2} sx={{ maxWidth: 480 }}>
      <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField required type="password" label={tUi("Current password")} autoComplete="current-password" value={current} onChange={e => setCurrent(e.target.value)} />
      <NewPasswordField label={tUi("New password")} value={password} onChange={setPassword} />
      <TextField required type="password" label={tUi("Confirm new password")} autoComplete="new-password" value={confirmation} onChange={e => setConfirmation(e.target.value)} />
      {validation ? <Alert severity="error">{validation === 'length' ? tUi("Use 12–128 characters.") : tUi("The passwords do not match.")}</Alert> : error ? <Alert severity="error">{getAccessErrorMessage(error)}</Alert> : null}
      <Button variant="contained" type="submit" disabled={busy}>{tUi("Change password")}</Button>
      </Box>
    </Stack>
  </ContentSection>;
}

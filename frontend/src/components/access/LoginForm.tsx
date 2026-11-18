import { useUiText } from '../../i18n/useUiText';
import React, { useRef, useState } from 'react';
import { Alert, Button, Stack, TextField } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';
import AccountTransportNotice from './AccountTransportNotice';

export default function LoginForm({ onCancel }: { onCancel?: () => void }) {
  const tUi = useUiText();
  const access = useAccess();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<unknown>(null);
  const submitting = useRef(false);
  const [busy, setBusy] = useState(false);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError(null);
    try { await accessService.login(username, password); setPassword(''); await access?.refresh(); onCancel?.(); }
    catch (reason) { setError(reason); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <ContentSection title={tUi("Sign in")}><Stack component="form" spacing={2} onSubmit={submit} sx={{ maxWidth: 440 }}>
    <AccountTransportNotice />
    <TextField disabled={busy} required label={tUi("Username")} autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} />
    <TextField disabled={busy} required label={tUi("Password")} type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} />
    {error ? <Alert severity="error">{getAccessErrorMessage(error)}</Alert> : null}
    <Button type="submit" disabled={busy || access?.status.account_transport === 'blocked'} variant="contained">{busy ? tUi("Signing in…") : tUi("Sign in")}</Button>
    {onCancel ? <Button disabled={busy} onClick={onCancel}>{tUi("Back to viewing")}</Button> : null}
  </Stack></ContentSection>;
}

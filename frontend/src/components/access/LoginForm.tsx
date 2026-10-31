import React, { useState } from 'react';
import { Alert, Button, Stack, TextField } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import { accessService } from '../../services/accessService';
import { useAccess } from './AccessContext';
import { getAccessErrorMessage } from '../../services/accessErrors';

export default function LoginForm({ onCancel }: { onCancel?: () => void }) {
  const access = useAccess();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await accessService.login(username, password); setPassword(''); await access?.refresh(); onCancel?.(); }
    catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  return <ContentSection title="Sign in"><Stack component="form" spacing={2} onSubmit={submit} sx={{ maxWidth: 440 }}>
    <TextField required label="Username" autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} />
    <TextField required label="Password" type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} inputProps={{ maxLength: 128 }} />
    {error ? <Alert severity="error">{error}</Alert> : null}
    <Button type="submit" disabled={busy} variant="contained">{busy ? 'Signing in…' : 'Sign in'}</Button>
    {onCancel ? <Button onClick={onCancel}>Back to viewing</Button> : null}
  </Stack></ContentSection>;
}

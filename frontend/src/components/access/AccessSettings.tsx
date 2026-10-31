import React, { useState } from 'react';
import { Alert, Box, Button, Checkbox, FormControlLabel, FormGroup, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { accessService, permissionLabels, type Permission, type Account, type AccessPolicy } from '../../services/accessService';
import { useAccess } from './AccessContext';
import AccountSetup from './AccountSetup';
import PasswordForm from './PasswordForm';
import ContentSection from '../layout/ContentSection';
import { getAccessErrorMessage } from '../../services/accessErrors';

function PermissionFields({ values, onChange, options = Object.keys(permissionLabels) as Permission[] }: { values: Permission[]; onChange: (value: Permission[]) => void; options?: Permission[] }) {
  return <FormGroup row>{options.map(permission => <FormControlLabel key={permission} label={permissionLabels[permission]} control={<Checkbox checked={values.includes(permission)} onChange={(_, checked) => onChange(checked ? [...values, permission] : values.filter(p => p !== permission))} />} />)}</FormGroup>;
}

function AccountEditor({ initial, saved }: { initial?: Account; saved: () => Promise<void> }) {
  const [username, setUsername] = useState(initial?.username ?? '');
  const [password, setPassword] = useState('');
  const [administrator, setAdministrator] = useState(initial?.administrator ?? false);
  const [enabled, setEnabled] = useState(initial?.enabled ?? true);
  const [permissions, setPermissions] = useState<Permission[]>(initial?.permissions ?? ['live', 'channels', 'guide']);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError('');
    try {
      if (initial) await accessService.updateUser({ ...initial, enabled, administrator, permissions });
      else { await accessService.createUser({ username, password, administrator, permissions }); setUsername(''); setPassword(''); }
      await saved();
    } catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  return <Stack component="form" onSubmit={submit} spacing={1.5} sx={{ pb: 2, mb: 2, borderBottom: 1, borderColor: 'divider' }}>
    {initial ? <Typography component="h3" variant="subtitle1">{username}</Typography> : <>
      <TextField label="New account username" required value={username} onChange={e => setUsername(e.target.value)} autoComplete="off" inputProps={{ maxLength: 64, pattern: '[a-zA-Z0-9_.\\-]+' }} />
      <TextField label="Initial password" type="password" required value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" inputProps={{ minLength: 12, maxLength: 128 }} />
    </>}
    <FormGroup row><FormControlLabel label="Administrator" control={<Checkbox checked={administrator} onChange={(_, value) => setAdministrator(value)} />} />
      {initial ? <FormControlLabel label="Account enabled" control={<Checkbox checked={enabled} onChange={(_, value) => setEnabled(value)} />} /> : null}</FormGroup>
    {administrator ? <Typography variant="body2">Administrators can manage the installation and use all viewing features.</Typography> : <PermissionFields values={permissions} onChange={setPermissions} />}
    {error ? <Alert severity="error">{error}</Alert> : null}
    <Box><Button type="submit" variant={initial ? 'outlined' : 'contained'} disabled={busy}>{initial ? 'Save account' : 'Create account'}</Button></Box>
  </Stack>;
}

function PolicyForm({ initial }: { initial: AccessPolicy }) {
  const [policy, setPolicy] = useState(initial);
  const [home, setHome] = useState((initial.home_networks ?? []).join(', '));
  const [local, setLocal] = useState((initial.local_networks ?? []).join(', '));
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; error: boolean } | null>(null);
  const checkbox = (key: 'public_playlists' | 'local_iptv' | 'remote_casting' | 'compatibility_conversion', label: string) => <FormControlLabel label={label} control={<Checkbox checked={policy[key]} onChange={(_, value) => setPolicy({ ...policy, [key]: value })} />} />;
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setFeedback(null);
    try { await accessService.savePolicy({ ...policy, home_networks: home.split(',').map(v => v.trim()).filter(Boolean), local_networks: local.split(',').map(v => v.trim()).filter(Boolean) }); setFeedback({ message: 'Access policy saved.', error: false }); }
    catch (reason) { setFeedback({ message: getAccessErrorMessage(reason), error: true }); }
    finally { setBusy(false); }
  };
  return <ContentSection title="Viewing and network access"><Stack component="form" onSubmit={submit} spacing={2}>
    <Typography component="h3" variant="subtitle1">Public viewing features</Typography>
    <Typography variant="body2">Selected features are available without signing in. Public pages contain viewing information only.</Typography>
    <PermissionFields values={policy.public_features ?? []} onChange={value => setPolicy({ ...policy, public_features: value })} options={['live', 'channels', 'guide', 'events', 'cast']} />
    {checkbox('public_playlists', 'Allow public playlists, guides and media without credentials')}
    {checkbox('local_iptv', 'Allow IPTV without credentials on trusted local networks')}
    <TextField label="Local IPTV networks" value={local} onChange={e => setLocal(e.target.value)} helperText="Comma-separated client subnets, for example 192.168.1.0/24. A proxy or Docker gateway alone never proves local access." />
    <Typography component="h3" variant="subtitle1">Server-device casting</Typography>
    <TextField label="Home networks" value={home} onChange={e => setHome(e.target.value)} helperText="Only verified clients in these networks can control home TVs, unless remote casting is allowed." />
    {checkbox('remote_casting', 'Allow remote casting for accounts with Cast to server devices permission')}
    <TextField label="Application URL reachable by the TVs" value={policy.cast_media_url} onChange={e => setPolicy({ ...policy, cast_media_url: e.target.value })} placeholder="http://192.168.1.10:8000" helperText="Include any reverse-proxy path prefix. This must point to this installation." />
    {checkbox('compatibility_conversion', 'Offer H.264 compatibility conversion for casting')}
    <Typography variant="body2">Conversion uses more CPU, supports one converted stream at a time and caps output at 720p/30 fps. Original video remains the default.</Typography>
    {feedback ? <Alert severity={feedback.error ? 'error' : 'success'}>{feedback.message}</Alert> : null}
    <Box><Button type="submit" variant="contained" disabled={busy}>Save access policy</Button></Box>
  </Stack></ContentSection>;
}

function CredentialsPanel() {
  const cache = useQueryClient();
  const query = useQuery({ queryKey: ['access-credentials'], queryFn: accessService.credentials });
  const sessions = useQuery({ queryKey: ['access-sessions'], queryFn: accessService.sessions });
  const [label, setLabel] = useState('');
  const [kind, setKind] = useState<'admin' | 'playback'>('playback');
  const [issued, setIssued] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const run = async (action: () => Promise<unknown>) => { setBusy(true); setError(''); try { await action(); await cache.invalidateQueries({ queryKey: ['access-credentials'] }); await cache.invalidateQueries({ queryKey: ['access-sessions'] }); } catch (reason) { setError(getAccessErrorMessage(reason)); } finally { setBusy(false); } };
  return <>
    <ContentSection title="Playback and API credentials" description="Playback credentials can appear in IPTV URLs. Administrative credentials work only in request headers; never share them with players.">
      <Stack spacing={2}>
        <Stack component="form" spacing={2} onSubmit={e => { e.preventDefault(); void run(async () => { const value = await accessService.issueCredential(label, kind); setIssued(value.token); }); }}>
          <TextField required label="Credential label" value={label} onChange={e => setLabel(e.target.value)} inputProps={{ maxLength: 80 }} />
          <TextField select label="Credential access" value={kind} onChange={e => setKind(e.target.value as 'admin' | 'playback')}><MenuItem value="playback">Playback only</MenuItem><MenuItem value="admin">Administrative API</MenuItem></TextField>
          <Box><Button type="submit" disabled={busy}>Create credential</Button></Box>
        </Stack>
        {issued ? <Alert severity="info"><Typography>Save this credential now; it is shown only once.</Typography><TextField label="New credential" value={issued} fullWidth InputProps={{ readOnly: true }} /><Button onClick={() => setIssued('')}>Dismiss credential</Button></Alert> : null}
        {query.data?.map(item => <Stack direction="row" key={item.id} spacing={2} alignItems="center"><Typography sx={{ flex: 1, overflowWrap: 'anywhere' }}>{item.label} · {item.kind}</Typography><Button disabled={busy} onClick={() => void run(() => accessService.revokeCredential(item.id))}>Revoke</Button></Stack>)}
        <Typography variant="body2">After rotating a playlist credential, reload Kodi IPTV Simple so it fetches the new URLs.</Typography>
        {error || query.isError ? <Alert severity="error">{error || 'Could not load credentials.'}</Alert> : null}
      </Stack>
    </ContentSection>
    <ContentSection title="Login sessions"><Stack spacing={1}>{sessions.data?.map(item => <Stack key={item.id} direction="row" spacing={2} alignItems="center"><Typography sx={{ flex: 1 }}>{item.username} · last active {new Date(item.last_seen * 1000).toLocaleString()}</Typography><Button disabled={busy} onClick={() => void run(() => accessService.revokeSession(item.id))}>Sign out session</Button></Stack>)}{sessions.isError ? <Alert severity="error">Could not load sessions.</Alert> : null}</Stack></ContentSection>
  </>;
}

export default function AccessSettings() {
  const access = useAccess();
  const enabled = access?.status.mode === 'accounts';
  const users = useQuery({ queryKey: ['access-users'], queryFn: accessService.users, enabled });
  const policy = useQuery({ queryKey: ['access-policy'], queryFn: accessService.policy, enabled });
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  if (!access) return null;
  if (!enabled) return <AccountSetup />;
  const disable = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await accessService.disable(password); setPassword(''); await access.refresh(); }
    catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  return <>
    <PasswordForm />
    <ContentSection title="Accounts" description="Changing permissions signs out that account and revokes its API credentials.">
      {users.data?.map(user => <AccountEditor key={user.id} initial={user} saved={async () => { await users.refetch(); }} />)}
      {users.isError ? <Alert severity="error">Could not load accounts.</Alert> : null}
      <Typography component="h3" variant="h6" sx={{ mb: 2 }}>Add an account</Typography><AccountEditor saved={async () => { await users.refetch(); }} />
    </ContentSection>
    {policy.data ? <PolicyForm initial={policy.data} /> : policy.isError ? <Alert severity="error">Could not load access policy.</Alert> : <Typography role="status">Loading access policy…</Typography>}
    <CredentialsPanel />
    <ContentSection title="Disable user management" description="Accounts and their credentials will be removed. Anyone able to reach the app can manage it, unless the existing deployment API token still protects it.">
      <Stack component="form" onSubmit={disable} spacing={2} sx={{ maxWidth: 560 }}>
        <FormControlLabel label="I understand that account protection will be removed" control={<Checkbox checked={confirm} onChange={(_, value) => setConfirm(value)} />} />
        <TextField required type="password" label="Administrator password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} />
        {error ? <Alert severity="error">{error}</Alert> : null}<Button type="submit" color="error" disabled={!confirm || busy}>Disable user management</Button>
      </Stack>
    </ContentSection>
  </>;
}

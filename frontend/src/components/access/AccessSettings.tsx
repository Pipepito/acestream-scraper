import { Alert,Box,Button,Checkbox,FormControlLabel,FormGroup,MenuItem,Stack,TextField,Typography } from '@mui/material';
import { useQuery,useQueryClient } from '@tanstack/react-query';
import React,{ useRef,useState } from 'react';
import { flushSync } from 'react-dom';
import { getLocale } from '../../i18n/locale';
import { translateKnown } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import { getAccessErrorMessage } from '../../services/accessErrors';
import { accessService,permissionLabels,type AccessPolicy,type Account,type Permission } from '../../services/accessService';
import ContentSection from '../layout/ContentSection';
import { useUnsavedChanges } from '../UnsavedChanges';
import { useAccess } from './AccessContext';
import AccountSetup from './AccountSetup';
import NewPasswordField,{ validNewPassword } from './NewPasswordField';
import PasswordForm from './PasswordForm';

function PermissionFields({ values, onChange, options = Object.keys(permissionLabels) as Permission[] }: { values: Permission[]; onChange: (value: Permission[]) => void; options?: Permission[] }) {
  useUiText();
  return <FormGroup row>{options.map(permission => <FormControlLabel key={permission} label={translateKnown(permissionLabels[permission])} control={<Checkbox checked={values.includes(permission)} onChange={(_, checked) => onChange(checked ? [...values, permission] : values.filter(p => p !== permission))} />} />)}</FormGroup>;
}

function AccountEditor({ initial, saved }: { initial?: Account; saved: () => Promise<void> }) {
  const tUi = useUiText();
  const [username, setUsername] = useState(initial?.username ?? '');
  const [password, setPassword] = useState('');
  const [administrator, setAdministrator] = useState(initial?.administrator ?? false);
  const [enabled, setEnabled] = useState(initial?.enabled ?? true);
  const [permissions, setPermissions] = useState<Permission[]>(initial?.permissions ?? ['live', 'channels', 'guide']);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const submitting = useRef(false);
  const [invalidPassword, setInvalidPassword] = useState(false);
  const [baseline, setBaseline] = useState(() => JSON.stringify([username, administrator, enabled, permissions]));
  const current = JSON.stringify([username, administrator, enabled, permissions]);
  useUnsavedChanges(Boolean(password) || current !== baseline, busy);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current) return;
    setError(null); setInvalidPassword(false);
    if (!initial && !validNewPassword(password)) { setInvalidPassword(true); return; }
    submitting.current = true; setBusy(true);
    try {
      if (initial) await accessService.updateUser({ ...initial, enabled, administrator, permissions });
      else { await accessService.createUser({ username, password, administrator, permissions }); setUsername(''); setPassword(''); setBaseline(JSON.stringify(['', administrator, enabled, permissions])); }
      if (initial) setBaseline(current);
      await saved();
    } catch (reason) { setError(reason); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <Stack component="form" aria-label={initial ? tUi("Edit account {{value0}}", { value0: username }) : tUi("Create account")} onSubmit={submit} spacing={1.5} sx={{ pb: 2, mb: 2, borderBottom: 1, borderColor: 'divider' }}>
    <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
    {initial ? <Typography component="h3" variant="subtitle1">{username}</Typography> : <>
      <TextField label={tUi("New account username")} required value={username} onChange={e => setUsername(e.target.value)} autoComplete="off" inputProps={{ maxLength: 64, pattern: '[a-zA-Z0-9_.\\-]+' }} />
      <NewPasswordField label={tUi("Initial password")} value={password} onChange={setPassword} />
    </>}
    <FormGroup row><FormControlLabel label={tUi("Administrator")} control={<Checkbox checked={administrator} onChange={(_, value) => setAdministrator(value)} />} />
      {initial ? <FormControlLabel label={tUi("Account enabled")} control={<Checkbox checked={enabled} onChange={(_, value) => setEnabled(value)} />} /> : null}</FormGroup>
    {administrator ? <Typography variant="body2">{tUi("Administrators can manage the installation and use all viewing features.")}</Typography> : <PermissionFields values={permissions} onChange={setPermissions} />}
    {invalidPassword ? <Alert severity="error">{tUi("Use 12–128 characters.")}</Alert> : null}
    {error ? <Alert severity="error">{getAccessErrorMessage(error)}</Alert> : null}
    <Box><Button type="submit" variant={initial ? 'outlined' : 'contained'} disabled={busy}>{initial ? tUi("Save account") : tUi("Create account")}</Button></Box>
    </Box>
  </Stack>;
}

function PolicyForm({ initial }: { initial: AccessPolicy }) {
  const tUi = useUiText();
  const [draft, setPolicy] = useState<AccessPolicy | null>(null);
  const policy = draft ?? initial;
  const cache = useQueryClient();
  const [localDraft, setLocal] = useState<string | null>(null);
  const local = localDraft ?? (initial.local_networks ?? []).join(', ');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ error: false } | { error: true; reason: unknown } | null>(null);
  const submitting = useRef(false);
  useUnsavedChanges(draft !== null || localDraft !== null, busy);
  const checkbox = (key: 'public_playlists' | 'local_iptv', label: string) => <FormControlLabel label={label} control={<Checkbox checked={policy[key]} onChange={(_, value) => setPolicy({ ...policy, [key]: value })} />} />;
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setFeedback(null);
    try {
      await cache.cancelQueries({ queryKey: ['access-policy'] });
      const saved = await accessService.savePolicy({ public_features: policy.public_features, public_playlists: policy.public_playlists,
        local_iptv: policy.local_iptv, local_networks: local.split(',').map(v => v.trim()).filter(Boolean) });
      cache.setQueryData(['access-policy'], saved);
      setPolicy(null); setLocal(null);
      await cache.invalidateQueries({ queryKey: ['access-status'] });
      setFeedback({ error: false });
    }
    catch (reason) { setFeedback({ reason, error: true }); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <ContentSection title={tUi("Viewing and network access")}><Stack component="form" aria-label={tUi("Public viewing and network access")} onSubmit={submit} spacing={2}>
    <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
    <Typography component="h3" variant="subtitle1">{tUi("Public viewing features")}</Typography>
    <Typography variant="body2">{tUi("Selected features are available without signing in. Public pages contain viewing information only.")}</Typography>
    <PermissionFields values={policy.public_features ?? []} onChange={value => setPolicy({ ...policy, public_features: value })} options={['live', 'channels', 'guide', 'events', 'cast']} />
    {checkbox('public_playlists', tUi('Allow public playlists, guides and media without credentials'))}
    {checkbox('local_iptv', tUi('Allow IPTV without credentials on trusted local networks'))}
    <TextField label={tUi("Local IPTV networks")} value={local} onChange={e => { setPolicy(policy); setLocal(e.target.value); }} helperText={tUi("Comma-separated client subnets, for example 192.168.1.0/24. A proxy or Docker gateway alone never proves local access.")} />
    {feedback ? <Alert severity={feedback.error ? 'error' : 'success'}>{feedback.error ? getAccessErrorMessage(feedback.reason) : tUi("Access policy saved.")}</Alert> : null}
    <Box><Button type="submit" variant="contained" disabled={busy}>{tUi("Save access policy")}</Button></Box>
    </Box>
  </Stack></ContentSection>;
}

function CredentialsPanel({ enabled }: { enabled: boolean }) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const query = useQuery({ queryKey: ['access-credentials'], queryFn: ({ signal }) => accessService.credentials(signal), enabled });
  const sessions = useQuery({ queryKey: ['access-sessions'], queryFn: ({ signal }) => accessService.sessions(signal), enabled });
  const [label, setLabel] = useState('');
  const [kind, setKind] = useState<'admin' | 'playback'>('playback');
  const [issued, setIssued] = useState('');
  const [error, setError] = useState<unknown>(null);
  const submitting = useRef(false);
  const [busy, setBusy] = useState(false);
  useUnsavedChanges(Boolean(label || issued || kind !== 'playback'), busy);
  const run = async (action: () => Promise<unknown>) => { if (submitting.current) return; submitting.current = true; setBusy(true); setError(null); try { await action(); await cache.invalidateQueries({ queryKey: ['access-credentials'] }); await cache.invalidateQueries({ queryKey: ['access-sessions'] }); } catch (reason) { setError(reason); } finally { submitting.current = false; setBusy(false); } };
  return <>
    <ContentSection title={tUi("Playback and API credentials")} description={tUi("Playback credentials can appear in IPTV URLs. Administrative credentials work only in request headers; never share them with players.")}>
      <Stack spacing={2}>
        <Stack component="form" spacing={2} onSubmit={e => { e.preventDefault(); void run(async () => { const value = await accessService.issueCredential(label, kind); setIssued(value.token); setLabel(''); setKind('playback'); }); }}>
          <TextField disabled={busy} required label={tUi("Credential label")} value={label} onChange={e => setLabel(e.target.value)} inputProps={{ maxLength: 80 }} />
          <TextField disabled={busy} select label={tUi("Credential access")} value={kind} onChange={e => setKind(e.target.value as 'admin' | 'playback')}><MenuItem value="playback">{tUi("Playback only")}</MenuItem><MenuItem value="admin">{tUi("Administrative API")}</MenuItem></TextField>
          <Box><Button type="submit" disabled={busy}>{tUi("Create credential")}</Button></Box>
        </Stack>
        {issued ? <Alert severity="info"><Typography>{tUi("Save this credential now; it is shown only once.")}</Typography><TextField label={tUi("New credential")} value={issued} fullWidth InputProps={{ readOnly: true }} /><Button onClick={() => setIssued('')}>{tUi("Dismiss credential")}</Button></Alert> : null}
        {query.data?.map(item => <Stack direction="row" key={item.id} spacing={2} alignItems="center"><Typography sx={{ flex: 1, overflowWrap: 'anywhere' }}>{item.label} · {item.kind === 'admin' ? tUi('Administrative API') : tUi('Playback only')}</Typography><Button disabled={busy} onClick={() => void run(() => accessService.revokeCredential(item.id))}>{tUi("Revoke")}</Button></Stack>)}
        <Typography variant="body2">{tUi("After rotating a playlist credential, reload Kodi IPTV Simple so it fetches the new URLs.")}</Typography>
        {error || query.isError ? <Alert severity="error">{error ? getAccessErrorMessage(error) : tUi('Could not load credentials.')}</Alert> : null}
      </Stack>
    </ContentSection>
    <ContentSection title={tUi("Login sessions")}><Stack spacing={1}>{sessions.data?.map(item => <Stack key={item.id} direction="row" spacing={2} alignItems="center"><Typography sx={{ flex: 1 }}>{item.username} {' '}{tUi("· last active")}{' '}{new Date(item.last_seen * 1000).toLocaleString(getLocale())}</Typography><Button disabled={busy} onClick={() => void run(() => accessService.revokeSession(item.id))}>{tUi("Sign out session")}</Button></Stack>)}{sessions.isError ? <Alert severity="error">{tUi("Could not load sessions.")}</Alert> : null}</Stack></ContentSection>
  </>;
}

export default function AccessSettings() {
  const tUi = useUiText();
  const access = useAccess();
  const enabled = access?.status.mode === 'accounts';
  const cache = useQueryClient();
  const [busy, setBusy] = useState(false);
  const users = useQuery({ queryKey: ['access-users'], queryFn: ({ signal }) => accessService.users(signal), enabled: enabled && !busy });
  const policy = useQuery({ queryKey: ['access-policy'], queryFn: ({ signal }) => accessService.policy(signal), enabled: enabled && !busy });
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const submitting = useRef(false);
  useUnsavedChanges(Boolean(password || confirm), busy);
  if (!access) return null;
  if (!enabled) return <AccountSetup />;
  const disable = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current || !confirm) return;
    submitting.current = true; flushSync(() => setBusy(true)); setError(null);
    try {
      // Stop old administrative reads before revoking their authorization.
      await cache.cancelQueries({ predicate: query => ['access-users', 'access-policy', 'access-credentials', 'access-sessions'].includes(String(query.queryKey[0])) });
      await accessService.disable(password); setPassword(''); await access.refresh();
    }
    catch (reason) { setError(reason); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <Box component="fieldset" aria-label={tUi("Access")} aria-busy={busy} disabled={busy} sx={{ border: 0, p: 0, m: 0, minWidth: 0 }}>
    <PasswordForm />
    <ContentSection title={tUi("Accounts")} description={tUi("Changing permissions signs out that account and revokes its API credentials.")}>
      {users.data?.map(user => <AccountEditor key={user.id} initial={user} saved={async () => { await users.refetch(); }} />)}
      {users.isError ? <Alert severity="error">{tUi("Could not load accounts.")}</Alert> : null}
      <Typography component="h3" variant="h6" sx={{ mb: 2 }}>{tUi("Add an account")}</Typography><AccountEditor saved={async () => { await users.refetch(); }} />
    </ContentSection>
    {policy.data ? <PolicyForm initial={policy.data} /> : policy.isError ? <Alert severity="error">{tUi("Could not load access policy.")}</Alert> : <Typography role="status">{tUi("Loading access policy…")}</Typography>}
    <CredentialsPanel enabled={!busy} />
    <ContentSection title={tUi("Disable user management")} description={tUi("Accounts and their credentials will be removed. Anyone able to reach the app can manage it, unless the existing deployment API token still protects it.")}>
      <Stack component="form" onSubmit={disable} spacing={2} sx={{ maxWidth: 560 }}>
        <FormControlLabel label={tUi("I understand that account protection will be removed")} control={<Checkbox disabled={busy} checked={confirm} onChange={(_, value) => setConfirm(value)} />} />
        <TextField disabled={busy} required type="password" label={tUi("Administrator password")} autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} />
        {error ? <Alert severity="error">{getAccessErrorMessage(error)}</Alert> : null}<Button type="submit" color="error" disabled={!confirm || busy}>{tUi("Disable user management")}</Button>
      </Stack>
    </ContentSection>
  </Box>;
}

import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Box, Button, Divider, Link, Stack, TextField, Typography } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { useConfirm } from '../ConfirmDialog';
import { telegramService, TelegramSource, TelegramSourceConfig } from '../../services/telegramService';
import { telegramError as getErrorMessage } from '../../services/telegramService';
import TelegramSourceEditor from './TelegramSourceEditor';

export default function TelegramSection() {
  const cache = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const [token, setToken] = useState('');
  const [admin, setAdmin] = useState('');
  const [apiId, setApiId] = useState('');
  const [apiHash, setApiHash] = useState('');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<TelegramSource | 'new' | null>(null);
  const api = useMemo(() => telegramService(admin), [admin]);
  const status = useQuery({ queryKey: ['telegram', 'status'], queryFn: api.status, enabled: !!admin, refetchInterval: admin ? 10000 : false, retry: false });
  const sources = useQuery({ queryKey: ['telegram', 'sources'], queryFn: api.sources, enabled: !!admin && !status.isError, refetchInterval: admin ? 10000 : false, retry: false });
  useEffect(() => () => { cache.removeQueries({ queryKey: ['telegram'] }); }, [cache]);
  const refresh = async () => { await cache.invalidateQueries({ queryKey: ['telegram'] }); };
  const run = async (action: () => Promise<unknown>) => {
    setBusy(true); setError('');
    try { await action(); await refresh(); } catch (cause) { setError(getErrorMessage(cause)); } finally { setBusy(false); }
  };
  const lock = () => {
    setAdmin(''); setToken(''); setApiHash(''); setPhone(''); setCode(''); setPassword(''); setEditing(null); setError('');
    cache.removeQueries({ queryKey: ['telegram'] });
  };
  const toggle = async (source: TelegramSource) => {
    const { id: _id, chat_label: _chat, sender_labels: _labels, cursor: _cursor, state: _state, last_success: _success, imported_count: _count, message: _message, ...config } = source;
    await api.save({ ...config, enabled: !source.enabled } as TelegramSourceConfig, source.id);
  };
  return <Box id="telegram"><ContentSection title="Telegram sources" description="Collect AceStream links from selected chats using your own Telegram account.">
    <Stack spacing={2}>
      <Typography variant="body2"><Link href="https://github.com/Pipepito/acestream-scraper/wiki/Telegram-Sources" target="_blank" rel="noreferrer">Setup, key storage and recovery guide ↗</Link></Typography>
      {!admin ? <>
        <Typography variant="body2">Configure TELEGRAM_ADMIN_TOKEN and a separate encryption key on the server first. Use HTTPS or localhost. This admin token stays in memory until you lock or leave this page.</Typography>
        <Stack component="form" onSubmit={event => { event.preventDefault(); setAdmin(token); setToken(''); }} direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField fullWidth type="password" autoComplete="off" label="Telegram admin token" value={token} onChange={event => setToken(event.target.value)} />
          <Button type="submit" variant="outlined" disabled={!token}>Unlock Telegram settings</Button>
        </Stack>
      </> : <>
        <Stack direction="row" justifyContent="space-between" spacing={1}><Typography role="status">{status.data?.account_label ? `${status.data.account_label} · ` : ''}{status.data?.state.replaceAll('_', ' ') ?? 'Loading account…'}</Typography><Button onClick={lock}>Lock settings</Button></Stack>
        {(error || status.error || sources.error) && <Alert severity="error">{error || getErrorMessage(status.error ?? sources.error)}</Alert>}
        {status.data?.message && <Alert severity="info">{status.data.message}</Alert>}
        {status.data?.retry_at && <Typography>Retry after {new Date(status.data.retry_at).toLocaleString()}</Typography>}
        {!!status.data?.queue_size && <Typography>{status.data.queue_size} queued updates</Typography>}
        {status.data?.state === 'disconnected' && <>
          <Alert severity="warning">This session has the account’s broader Telegram permissions even though this app only reads selected chats. Connect only an account you control. API credentials alone do not grant access.</Alert>
          <Box component="form" onSubmit={event => { event.preventDefault(); void run(async () => { try { await api.login(Number(apiId), apiHash, phone); } finally { setApiHash(''); setPhone(''); } }); }}>
            <Stack spacing={2}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <TextField fullWidth label="Telegram API ID" value={apiId} onChange={event => setApiId(event.target.value)} inputProps={{ inputMode: 'numeric' }} />
                <TextField fullWidth type="password" autoComplete="off" label="Telegram API hash" value={apiHash} onChange={event => setApiHash(event.target.value)} />
                <TextField fullWidth type="tel" autoComplete="off" label="Phone number with country code" value={phone} onChange={event => setPhone(event.target.value)} />
              </Stack>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap"><Button type="submit" variant="contained" disabled={busy || !apiId || !apiHash || !phone}>Send login code</Button><Button disabled={busy} onClick={() => void run(api.reconnect)}>Reconnect saved account</Button></Stack>
            </Stack>
          </Box>
        </>}
        {status.data?.state === 'code_required' && <Stack component="form" onSubmit={event => { event.preventDefault(); void run(async () => { try { await api.code(code); } finally { setCode(''); } }); }} direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField fullWidth type="password" autoComplete="off" label="Telegram login code" value={code} onChange={event => setCode(event.target.value)} /><Button type="submit" variant="contained" disabled={busy || !code}>Verify code</Button>
        </Stack>}
        {status.data?.state === 'password_required' && <Stack component="form" onSubmit={event => { event.preventDefault(); void run(async () => { try { await api.password(password); } finally { setPassword(''); } }); }} direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <TextField fullWidth type="password" autoComplete="off" label="Telegram two-step verification password" value={password} onChange={event => setPassword(event.target.value)} /><Button type="submit" variant="contained" disabled={busy || !password}>Authorize account</Button>
        </Stack>}
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
          <Button disabled={busy} onClick={() => void run(api.disconnect)}>Disconnect</Button>
          <Button color="error" disabled={busy} onClick={() => void run(async () => {
            if (await confirm({ title: 'Revoke Telegram session?', body: 'This logs the account out of this app and removes its sources and observations. Existing catalogue streams stay available.', confirmLabel: 'Revoke and remove', danger: true })) { await api.logout(); setEditing(null); }
          })}>Revoke session and remove account</Button>
        </Stack>
        {status.data?.state === 'connected' && <>
          <Divider />
          <Typography variant="body2">New sources start with new messages only unless you choose history. Pause keeps progress; resume catches up in bounded batches. Retained message observations cover up to 1,000 messages per source for 30 days. Edits and deletions never remove catalogue streams.</Typography>
          {!sources.data?.length && <Typography>No sources yet. Select a joined chat to start collecting.</Typography>}
          {sources.data?.map(source => <Stack key={source.id} spacing={1} sx={{ borderBottom: 1, borderColor: 'divider', py: 2, overflowWrap: 'anywhere' }}>
            <Typography variant="subtitle1">{source.name}</Typography>
            <Typography variant="body2">{source.chat_label} · {source.state.replaceAll('_', ' ')} · {source.imported_count} new streams imported</Typography>
            <Typography variant="body2">Last processed: {source.last_success ? new Date(source.last_success).toLocaleString() : 'No messages processed yet'}</Typography>
            {source.message && <Alert severity="warning">{source.message}</Alert>}
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
              <Button disabled={busy} onClick={() => void run(() => toggle(source))}>{source.enabled ? 'Pause' : 'Resume'} {source.name}</Button>
              <Button disabled={busy || !source.enabled} onClick={() => void run(() => api.scan(source.id))}>Scan now</Button>
              <Button disabled={busy} onClick={() => setEditing(source)}>Edit {source.name}</Button>
              <Button disabled={busy} color="error" onClick={() => void run(async () => { if (await confirm({ title: 'Remove source?', body: 'Collection stops. Existing catalogue streams are preserved.', confirmLabel: 'Remove source', danger: true })) await api.remove(source.id); })}>Remove {source.name}</Button>
            </Stack>
          </Stack>)}
          {!editing && <Button variant="outlined" sx={{ alignSelf: 'flex-start' }} onClick={() => setEditing('new')}>Add Telegram source</Button>}
          {editing && <TelegramSourceEditor key={editing === 'new' ? 'new' : editing.id} api={api} source={editing === 'new' ? undefined : editing} onCancel={() => setEditing(null)} onSaved={async () => { setEditing(null); await refresh(); }} />}
        </>}
      </>}
    </Stack>{dialog}
  </ContentSection></Box>;
}

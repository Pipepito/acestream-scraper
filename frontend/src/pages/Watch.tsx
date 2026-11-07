import React, { useState } from 'react';
import { Alert, Box, Button, Container, List, ListItem, ListItemText, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useAccess } from '../components/access/AccessContext';
import { accessService, permissionLabels, type Permission } from '../services/accessService';
import apiClient from '../services/apiClient';
import type { components } from '../types/api-generated';
import LoginForm from '../components/access/LoginForm';
import PasswordForm from '../components/access/PasswordForm';
import StreamPlayerDialog from '../components/player/StreamPlayerDialog';
import RecordingPlayback from '../components/recordings/RecordingPlayback';

type Section = 'live' | 'channels' | 'guide' | 'events' | 'recordings' | 'playlists';
type ViewData = components['schemas']['WatchChannels'] | components['schemas']['WatchProgramme'][] | components['schemas']['WatchEvent'][] | components['schemas']['WatchRecording'][];

export default function Watch() {
  const access = useAccess();
  const permissions = access?.status.permissions ?? [];
  const sections = (['live', 'channels', 'guide', 'events', 'recordings', 'playlists'] as Section[]).filter(value => permissions.includes(value as Permission));
  const [selected, setSelected] = useState<Section>('live');
  const [login, setLogin] = useState(false);
  const [account, setAccount] = useState(false);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState('');
  const [playing, setPlaying] = useState<{ id: string; name: string } | null>(null);
  const [file, setFile] = useState<{ recording: string; id: string } | null>(null);
  const playlist = useMutation({ mutationFn: accessService.playlistLink });
  const section = sections.includes(selected) ? selected : sections[0];
  const query = useQuery<ViewData>({ queryKey: ['watch', section, offset, search],
    queryFn: async () => (await apiClient.get(`/v1/view/${section}`, { params: { offset, search } })).data,
    enabled: Boolean(section) && section !== 'playlists' && !login && !account, retry: false });
  const channels = section === 'live' || section === 'channels' ? query.data as components['schemas']['WatchChannels'] | undefined : undefined;
  const programmes = section === 'guide' ? query.data as components['schemas']['WatchProgramme'][] | undefined : undefined;
  const events = section === 'events' ? query.data as components['schemas']['WatchEvent'][] | undefined : undefined;
  const recordings = section === 'recordings' ? query.data as components['schemas']['WatchRecording'][] | undefined : undefined;
  return <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 4 } }}>
    <Stack direction={{ xs: 'column', sm: 'row' }} alignItems={{ xs: 'flex-start', sm: 'center' }} justifyContent="space-between" spacing={2} sx={{ mb: 3 }}>
      <Typography variant="h4" component="h1">Watch</Typography>
      {access?.status.user ? <Stack direction="row" spacing={1}><Button onClick={() => setAccount(!account)}>My account</Button><Button onClick={() => void accessService.logout().then(access.refresh)}>Sign out</Button></Stack> : <Button onClick={() => setLogin(true)}>Sign in</Button>}
    </Stack>
    {login || (!sections.length && !access?.status.user) ? <LoginForm onCancel={sections.length ? () => setLogin(false) : undefined} /> : account ? <PasswordForm /> : <>
      {!sections.length ? <Alert severity="info">Your account has no viewing permissions. Ask an administrator to enable the features you need.</Alert> : <>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField select label="View" value={section} onChange={e => { setSelected(e.target.value as Section); setOffset(0); setFile(null); }} sx={{ minWidth: 200 }}>{sections.map(value => <MenuItem key={value} value={value}>{permissionLabels[value]}</MenuItem>)}</TextField>
          {channels ? <TextField label="Search channels" value={search} onChange={e => { setSearch(e.target.value); setOffset(0); }} fullWidth /> : null}
        </Stack>
        {section === 'playlists' ? <Stack spacing={2}>
          <Typography>Open these links in Kodi or another IPTV player. Signed-in accounts receive a playback-only credential; an administrator can revoke it in Settings → Access.</Typography>
          <Button disabled={playlist.isPending || playlist.isSuccess} onClick={() => playlist.mutate()}>Create playlist links</Button>
          {playlist.isError ? <Alert severity="error">Could not create playlist links. Ask an administrator to check access or revoke unused credentials.</Alert> : null}
          {playlist.data ? <><TextField label="Playlist URL" value={playlist.data.url} InputProps={{ readOnly: true }} onFocus={e => e.target.select()} /><TextField label="Programme guide URL" value={playlist.data.guide_url} InputProps={{ readOnly: true }} onFocus={e => e.target.select()} /><Alert severity="info">Anyone with a credential in these links can play the catalogue. Share them only with people you trust.</Alert></> : null}
        </Stack> : query.isError ? <Alert severity="error">Could not load this viewing section. <Button onClick={() => void query.refetch()}>Retry</Button></Alert> : query.isPending ? <Typography role="status">Loading…</Typography> : <>
          {playing ? <StreamPlayerDialog inline open contentId={playing.id} title={playing.name} onClose={() => setPlaying(null)} /> : null}
          {file ? <Box sx={{ my: 2 }}>
            <RecordingPlayback key={file.id} recordingId={file.recording} fileId={file.id} />
            <Button onClick={() => setFile(null)}>Stop recording playback</Button></Box> : null}
          <List>
            {channels?.items.map(channel => <ListItem key={channel.id} divider secondaryAction={permissions.includes('live') ? <Button onClick={() => setPlaying({ id: channel.id, name: channel.name })}>Watch</Button> : undefined}><ListItemText primary={channel.name} secondary={[channel.category, channel.online === true ? 'Verified signal' : channel.online === false ? 'Offline' : 'Signal unknown'].filter(Boolean).join(' · ')} /></ListItem>)}
            {programmes?.map(programme => <ListItem key={programme.id} divider><ListItemText primary={programme.title} secondary={`${programme.channel} · ${new Date(programme.start).toLocaleString()} – ${new Date(programme.end).toLocaleTimeString()}`} /></ListItem>)}
            {events?.map(event => <ListItem key={event.id} divider><ListItemText primary={event.title} secondary={`${event.competition} · ${event.starts_at ? new Date(event.starts_at).toLocaleString() : 'Time to be confirmed'} · ${event.state}`} /></ListItem>)}
            {recordings?.map(recording => <ListItem key={recording.id} divider><ListItemText primary={recording.title} secondary={`${recording.channel} · ${recording.state}`} />{recording.files?.map((id, index) => <Button key={id} onClick={() => setFile({ recording: recording.id, id })}>Play file {index + 1}</Button>)}</ListItem>)}
          </List>
          {(channels?.items.length === 0 || (Array.isArray(query.data) && query.data.length === 0)) ? <Typography>No items to show.</Typography> : null}
          <Stack direction="row" spacing={1}><Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous</Button><Button disabled={channels ? offset + channels.items.length >= channels.total : !Array.isArray(query.data) || query.data.length < 100} onClick={() => setOffset(offset + 100)}>Next</Button></Stack>
        </>}
      </>}
    </>}
  </Container>;
}

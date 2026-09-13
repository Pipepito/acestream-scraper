import React, { useRef, useState } from 'react';
import { Alert, Box, Button, IconButton, Stack, Typography } from '@mui/material';
import { ArrowDownward, ArrowUpward, DragIndicator } from '@mui/icons-material';
import { TVChannel } from '../types/tvChannelTypes';
import { normalizeApiError } from '../services/apiErrors';

export default function TVChannelReorder({ channels, onSave, onCancel }: {
  channels: TVChannel[]; onSave: (ids: number[], expected: number[]) => Promise<void>; onCancel: () => void;
}) {
  const original = useRef(channels);
  const [ordered, setOrdered] = useState(channels);
  const dragged = useRef<number | null>(null);
  const [over, setOver] = useState<number | null>(null);
  const [pending, setPending] = useState(false);
  const saving = useRef(false);
  const [error, setError] = useState('');
  const [announcement, setAnnouncement] = useState('');
  const move = (id: number, targetId: number) => {
    if (pending || id === targetId) return;
    setOrdered(current => {
      const from = current.findIndex(c => c.id === id), to = current.findIndex(c => c.id === targetId);
      if (from < 0 || to < 0) return current;
      const next = [...current]; const [item] = next.splice(from, 1); next.splice(to, 0, item);
      return next;
    });
    setAnnouncement('Channel moved. Save order to apply the new numbers.');
  };
  const save = async () => {
    if (saving.current) return;
    saving.current = true; setPending(true); setError('');
    try { await onSave(ordered.map(c => c.id), original.current.map(c => c.id)); }
    catch (e) { setError(normalizeApiError(e).message); }
    finally { saving.current = false; setPending(false); }
  };
  return <Stack spacing={2}>
    <Typography>Drag a handle to move a channel, or use the arrow buttons. This shows all channels and saves consecutive numbers from 1.</Typography>
    {error ? <Alert severity="error">{error}</Alert> : null}
    <Typography role="status" variant="body2">{announcement}</Typography>
    <Box component="ol" aria-label="Channel order" sx={{ listStyle: 'none', p: 0, m: 0, maxHeight: '60vh', overflowY: 'auto' }}>
      {ordered.map((channel, index) => <Box component="li" key={channel.id}
        onDragOver={e => { if (!pending && dragged.current !== null) { e.preventDefault(); setOver(channel.id); e.dataTransfer.dropEffect = 'move'; } }}
        onDrop={e => { e.preventDefault(); if (dragged.current !== null) move(dragged.current, channel.id); dragged.current = null; setOver(null); }}
        sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, borderBottom: 1, borderColor: 'divider', bgcolor: over === channel.id ? 'action.selected' : 'transparent' }}>
        <IconButton draggable={!pending} disabled={pending} aria-label={`Drag ${channel.name}`} sx={{ cursor: 'grab' }}
          onDragStart={e => { dragged.current = channel.id; e.dataTransfer.setData('text/plain', String(channel.id)); e.dataTransfer.effectAllowed = 'move'; }}
          onDragEnd={() => { dragged.current = null; setOver(null); }}
          onKeyDown={e => { const target = e.key === 'ArrowUp' ? ordered[index - 1] : e.key === 'ArrowDown' ? ordered[index + 1] : null; if (target) { e.preventDefault(); move(channel.id, target.id); } }}><DragIndicator /></IconButton>
        <Typography aria-label={`Number ${index + 1}`} sx={{ minWidth: 32 }}>{index + 1}</Typography>
        <Typography sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}>{channel.name}</Typography>
        <IconButton aria-label={`Move ${channel.name} up`} disabled={pending || index === 0} onClick={() => move(channel.id, ordered[index - 1].id)}><ArrowUpward /></IconButton>
        <IconButton aria-label={`Move ${channel.name} down`} disabled={pending || index === ordered.length - 1} onClick={() => move(channel.id, ordered[index + 1].id)}><ArrowDownward /></IconButton>
      </Box>)}
    </Box>
    <Stack direction="row" spacing={1}>
      <Button variant="contained" disabled={pending} onClick={() => void save()}>{pending ? 'Saving…' : 'Save order'}</Button>
      <Button disabled={pending} onClick={onCancel}>Cancel</Button>
    </Stack>
  </Stack>;
}

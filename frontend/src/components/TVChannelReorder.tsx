import { useUiText } from '../i18n/useUiText';
import React, { useRef, useState } from 'react';
import { Alert, Box, Button, IconButton, Stack, Typography } from '@mui/material';
import { ArrowDownward, ArrowUpward, DragIndicator } from '@mui/icons-material';
import { TVChannel } from '../types/tvChannelTypes';
import { getErrorMessage } from '../utils/errorUtils';
import { useUnsavedChanges } from './UnsavedChanges';
import { useConfirm } from './ConfirmDialog';

export default function TVChannelReorder({ channels, onSave, onCancel }: {
  channels: TVChannel[]; onSave: (ids: number[], expected: number[]) => Promise<void>; onCancel: () => void;
}) {
  const tUi = useUiText();
  const original = useRef(channels);
  const [ordered, setOrdered] = useState(channels);
  const dragged = useRef<number | null>(null);
  const [over, setOver] = useState<number | null>(null);
  const [pending, setPending] = useState(false);
  const saving = useRef(false);
  const [error, setError] = useState<unknown>(null);
  const [moved, setMoved] = useState(false);
  const dirty = ordered.some((channel, index) => channel.id !== original.current[index]?.id);
  useUnsavedChanges(dirty, pending);
  const { confirm, dialog } = useConfirm();
  const cancel = async () => {
    if (saving.current) return;
    if (dirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onCancel();
  };
  const move = (id: number, targetId: number) => {
    if (pending || id === targetId) return;
    setOrdered(current => {
      const from = current.findIndex(c => c.id === id), to = current.findIndex(c => c.id === targetId);
      if (from < 0 || to < 0) return current;
      const next = [...current]; const [item] = next.splice(from, 1); next.splice(to, 0, item);
      return next;
    });
    setMoved(true);
  };
  const save = async () => {
    if (saving.current) return;
    saving.current = true; setPending(true); setError(null);
    try { await onSave(ordered.map(c => c.id), original.current.map(c => c.id)); }
    catch (e) { setError(e); }
    finally { saving.current = false; setPending(false); }
  };
  return <Stack spacing={2}>
    {dialog}
    <Typography>{tUi("Drag a handle to move a channel, or use the arrow buttons. This shows all channels and saves consecutive numbers from 1.")}</Typography>
    {error != null ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
    <Typography role="status" variant="body2">{moved ? tUi('Channel moved. Save order to apply the new numbers.') : ''}</Typography>
    <Box component="ol" aria-label={tUi("Channel order")} sx={{ listStyle: 'none', p: 0, m: 0, maxHeight: '60vh', overflowY: 'auto' }}>
      {ordered.map((channel, index) => <Box component="li" key={channel.id}
        onDragOver={e => { if (!pending && dragged.current !== null) { e.preventDefault(); setOver(channel.id); e.dataTransfer.dropEffect = 'move'; } }}
        onDrop={e => { e.preventDefault(); if (dragged.current !== null) move(dragged.current, channel.id); dragged.current = null; setOver(null); }}
        sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 1, borderBottom: 1, borderColor: 'divider', bgcolor: over === channel.id ? 'action.selected' : 'transparent' }}>
        <IconButton draggable={!pending} disabled={pending} aria-label={tUi("Drag {{value0}}", { value0: channel.name })} sx={{ cursor: 'grab' }}
          onDragStart={e => { dragged.current = channel.id; e.dataTransfer.setData('text/plain', String(channel.id)); e.dataTransfer.effectAllowed = 'move'; }}
          onDragEnd={() => { dragged.current = null; setOver(null); }}
          onKeyDown={e => { const target = e.key === 'ArrowUp' ? ordered[index - 1] : e.key === 'ArrowDown' ? ordered[index + 1] : null; if (target) { e.preventDefault(); move(channel.id, target.id); } }}><DragIndicator /></IconButton>
        <Typography aria-label={tUi("Number {{value0}}", { value0: index + 1 })} sx={{ minWidth: 32 }}>{index + 1}</Typography>
        <Typography sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}>{channel.name}</Typography>
        <IconButton aria-label={tUi("Move {{value0}} up", { value0: channel.name })} disabled={pending || index === 0} onClick={() => move(channel.id, ordered[index - 1].id)}><ArrowUpward /></IconButton>
        <IconButton aria-label={tUi("Move {{value0}} down", { value0: channel.name })} disabled={pending || index === ordered.length - 1} onClick={() => move(channel.id, ordered[index + 1].id)}><ArrowDownward /></IconButton>
      </Box>)}
    </Box>
    <Stack direction="row" spacing={1}>
      <Button variant="contained" disabled={pending} onClick={() => void save()}>{pending ? tUi("Saving…") : tUi("Save order")}</Button>
      <Button disabled={pending} onClick={() => void cancel()}>{tUi("Cancel")}</Button>
    </Stack>
  </Stack>;
}

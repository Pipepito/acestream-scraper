import { useUiText } from '../i18n/useUiText';
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { defaultRangeExtractor, useVirtualizer } from '@tanstack/react-virtual';
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
  const scrollElement = useRef<HTMLDivElement>(null);
  const [focusedId, setFocusedId] = useState<number | null>(null);
  const [draggedId, setDraggedId] = useState<number | null>(null);
  const focusAfterMove = useRef<{ id: number; index: number } | null>(null);
  const positions = useMemo(() => new Map(ordered.map((channel, index) => [channel.id, index])), [ordered]);
  const virtualized = ordered.length > 100;
  const virtualizer = useVirtualizer({
    count: ordered.length,
    enabled: virtualized,
    getScrollElement: () => scrollElement.current,
    estimateSize: () => 80,
    initialRect: { height: 540, width: 400 },
    overscan: 4,
    getItemKey: useCallback((index: number) => ordered[index].id, [ordered]),
    rangeExtractor: useCallback((range: Parameters<typeof defaultRangeExtractor>[0]) => {
      const visible = defaultRangeExtractor(range);
      // Keep the focused/dragged DOM node alive even when it leaves the viewport.
      for (const id of [focusedId, draggedId]) {
        const index = id == null ? undefined : positions.get(id);
        if (index !== undefined && !visible.includes(index)) visible.push(index);
      }
      return visible.sort((a, b) => a - b);
    }, [focusedId, draggedId, positions]),
  });
  useEffect(() => {
    const target = focusAfterMove.current;
    if (!target) return;
    const frame = requestAnimationFrame(() => {
      if (virtualized) virtualizer.scrollToIndex(target.index, { align: 'auto' });
      scrollElement.current?.querySelector<HTMLButtonElement>(`[data-channel-id="${target.id}"] [data-drag-handle]`)?.focus({ preventScroll: true });
      focusAfterMove.current = null;
    });
    return () => cancelAnimationFrame(frame);
  }, [ordered, focusedId, virtualized, virtualizer]);
  const focusRow = (index: number) => {
    const channel = ordered[index];
    if (!channel) return;
    focusAfterMove.current = { id: channel.id, index };
    setFocusedId(channel.id);
  };
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
    const targetIndex = positions.get(targetId);
    if (targetIndex === undefined) return;
    focusAfterMove.current = { id, index: targetIndex };
    setFocusedId(id);
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
    <Typography variant="body2" color="text.secondary">{tUi('On a drag handle, Home and End focus the first and last channels; Page Up and Page Down move focus ten rows. Arrow keys change the order.')}</Typography>
    {error != null ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
    <Typography role="status" variant="body2">{moved ? tUi('Channel moved. Save order to apply the new numbers.') : ''}</Typography>
    <Box ref={scrollElement} sx={{ height: virtualized ? '60vh' : 'auto', maxHeight: '60vh', overflowY: 'auto', minWidth: 0 }}>
    <Box component="ol" aria-label={tUi("Channel order")} sx={{ listStyle: 'none', p: 0, m: 0, position: 'relative', height: virtualized ? virtualizer.getTotalSize() : undefined }}>
      {(virtualized ? virtualizer.getVirtualItems() : ordered.map((channel, index) => ({ key: channel.id, index, start: 0 }))).map(item => {
        const index = item.index, channel = ordered[index];
        return <Box component="li" key={channel.id} data-index={index} data-channel-id={channel.id}
        aria-posinset={index + 1} aria-setsize={ordered.length}
        ref={virtualized ? virtualizer.measureElement : undefined}
        onFocusCapture={() => setFocusedId(channel.id)}
        onBlurCapture={event => { if (!scrollElement.current?.contains(event.relatedTarget as Node | null)) setFocusedId(null); }}
        onDragOver={e => { if (!pending && dragged.current !== null) { e.preventDefault(); setOver(channel.id); e.dataTransfer.dropEffect = 'move'; } }}
        onDrop={e => { e.preventDefault(); if (dragged.current !== null) move(dragged.current, channel.id); dragged.current = null; setDraggedId(null); setOver(null); }}
        sx={{ ...(virtualized ? { position: 'absolute', top: 0, left: 0, width: '100%', transform: `translateY(${item.start}px)` } : {}), display: { xs: 'grid', sm: 'flex' }, gridTemplateColumns: '44px minmax(0, 1fr) 44px 44px', gridTemplateAreas: '"handle name name name" "number . up down"', alignItems: 'center', gap: 1, p: 1, borderBottom: 1, borderColor: 'divider', bgcolor: over === channel.id ? 'action.selected' : 'transparent' }}>
        <IconButton data-drag-handle draggable={!pending} disabled={pending} aria-label={tUi("Drag {{value0}}", { value0: channel.name })} sx={{ cursor: 'grab', gridArea: 'handle' }}
          onDragStart={e => { dragged.current = channel.id; setDraggedId(channel.id); e.dataTransfer.setData('text/plain', String(channel.id)); e.dataTransfer.effectAllowed = 'move'; }}
          onDragEnd={() => { dragged.current = null; setDraggedId(null); setOver(null); }}
          onKeyDown={e => {
            const target = e.key === 'ArrowUp' ? ordered[index - 1] : e.key === 'ArrowDown' ? ordered[index + 1] : null;
            if (target) { e.preventDefault(); move(channel.id, target.id); }
            else if (['Home', 'End', 'PageUp', 'PageDown'].includes(e.key)) {
              e.preventDefault();
              focusRow(e.key === 'Home' ? 0 : e.key === 'End' ? ordered.length - 1 : Math.max(0, Math.min(ordered.length - 1, index + (e.key === 'PageUp' ? -10 : 10))));
            }
          }}><DragIndicator /></IconButton>
        <Typography aria-label={tUi("Number {{value0}}", { value0: index + 1 })} sx={{ minWidth: 32, gridArea: 'number' }}>{index + 1}</Typography>
        <Typography sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere', gridArea: 'name' }}>{channel.name}</Typography>
        <IconButton sx={{ gridArea: 'up' }} aria-label={tUi("Move {{value0}} up", { value0: channel.name })} disabled={pending || index === 0} onClick={() => move(channel.id, ordered[index - 1].id)}><ArrowUpward /></IconButton>
        <IconButton sx={{ gridArea: 'down' }} aria-label={tUi("Move {{value0}} down", { value0: channel.name })} disabled={pending || index === ordered.length - 1} onClick={() => move(channel.id, ordered[index + 1].id)}><ArrowDownward /></IconButton>
      </Box>;
      })}
    </Box>
    </Box>
    <Stack direction="row" spacing={1}>
      <Button variant="contained" disabled={pending} onClick={() => void save()}>{pending ? tUi("Saving…") : tUi("Save order")}</Button>
      <Button disabled={pending} onClick={() => void cancel()}>{tUi("Cancel")}</Button>
    </Stack>
  </Stack>;
}

import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Button, Checkbox, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, FormControlLabel, Stack, Typography } from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { catalogueService, type CatalogueEntry, type FolderMatchApplyRequest, type FolderMatchRow } from '../../services/catalogueService';
import { getErrorMessage } from '../../utils/errorUtils';

interface FolderMatchDialogProps {
  open: boolean;
  catalogueId: number;
  entries: CatalogueEntry[];
  onClose: () => void;
  onApplied: (message: () => string) => void;
}

type Choice = { folder_id: string; tv_channel_id: number } | { folder_id: string; create: true };

/** Preview which folders match a TV channel by name, tick the ones to assign, apply once. */
const FolderMatchDialog: React.FC<FolderMatchDialogProps> = ({ open, catalogueId, entries, onClose, onApplied }) => {
  const tUi = useUiText();
  const preview = useQuery({ queryKey: ['catalogue', catalogueId, 'folder-matches'], queryFn: () => catalogueService.folderMatches(catalogueId), enabled: open, staleTime: 0 });
  const pending = useRef(false);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  useEffect(() => {
    if (preview.data) setChecked(Object.fromEntries(preview.data.rows.map((row) => [row.folder_id, row.status === 'match'])));
  }, [preview.data]);
  const parents = useMemo(() => new Map(entries.map((entry) => [entry.id, entry.parent_id ?? null])), [entries]);
  const isDescendant = (childId: string, ancestorId: string) => {
    let current = parents.get(childId) ?? null;
    let guard = 0;
    while (current && guard < 100) { if (current === ancestorId) return true; current = parents.get(current) ?? null; guard += 1; }
    return false;
  };
  const rows = preview.data?.rows ?? [];
  const coveredBy = (row: FolderMatchRow) => rows.find((other) => other.folder_id !== row.folder_id && checked[other.folder_id] && isDescendant(other.folder_id, row.folder_id));
  const choices: Choice[] = rows.flatMap((row): Choice[] => {
    if (!checked[row.folder_id] || coveredBy(row)) return [];
    if (row.status === 'match' && row.candidate) return [{ folder_id: row.folder_id, tv_channel_id: row.candidate.id }];
    if (row.status === 'none') return [{ folder_id: row.folder_id, create: true as const }];
    return [];
  });
  const apply = useMutation({
    mutationFn: (request: FolderMatchApplyRequest) => catalogueService.applyFolderMatches(catalogueId, request),
    onSuccess: (result) => {
      const done = result.results.filter((row) => row.tv_channel);
      const streams = done.reduce((sum, row) => sum + (row.assigned ?? 0) + (row.moved ?? 0), 0);
      onApplied(() => tUi('Assigned across {{folders}}: {{streams}}.', { folders: tUi('folderCount', { count: done.length }), streams: tUi('streamCount', { count: streams }) }));
      onClose();
    },
  });
  return (
    <Dialog open={open} onClose={apply.isPending ? undefined : onClose} maxWidth="md" fullWidth aria-labelledby="folder-match-title">
      <DialogTitle id="folder-match-title">{tUi("Match folders to TV channels")}</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 1.5 }}>{tUi("Folders whose name equals a TV channel are ticked. Tick Create for folders without a match to make a TV channel with the folder's name. Streams already on another TV channel are left where they are.")}</DialogContentText>
        {preview.isPending ? <CircularProgress aria-label={tUi("Loading folder matches")} /> : preview.isError ? <Alert severity="error" action={<Button onClick={() => void preview.refetch()}>{tUi("Retry")}</Button>}>{getErrorMessage(preview.error)}</Alert>
          : rows.length === 0 ? <Typography>{tUi("No folders with imported streams.")}</Typography>
          : <Stack spacing={1}>
            {rows.map((row) => {
              const cover = coveredBy(row);
              const streams = tUi('streamCount', { count: row.stream_count });
              if (row.status === 'assigned' && row.current) return <Stack key={row.folder_id} sx={{ overflowWrap: 'anywhere' }}><Typography>{row.path} · {streams}</Typography><Typography variant="body2" color="text.secondary">{tUi("Already on")}{' '}{row.current.name}</Typography></Stack>;
              if (row.status === 'ambiguous') return <Stack key={row.folder_id} sx={{ overflowWrap: 'anywhere' }}><Typography>{row.path} · {streams}</Typography><Typography variant="body2" color="text.secondary">{tUi("More than one TV channel matches; assign it from the folder menu.")}</Typography></Stack>;
              const label = row.status === 'match' && row.candidate ? tUi('Assign {{folder}} to {{channel}}', { folder: row.name, channel: row.candidate.name }) : tUi('Create TV channel {{name}}', { name: row.name });
              return <Stack key={row.folder_id} sx={{ overflowWrap: 'anywhere' }}>
                <FormControlLabel control={<Checkbox checked={Boolean(checked[row.folder_id]) && !cover} disabled={Boolean(cover) || apply.isPending} onChange={(_, value) => setChecked((current) => ({ ...current, [row.folder_id]: value }))} />} label={label} />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>{row.path} · {streams}{cover ? tUi(" · covered by {{value0}}", { value0: cover.name }) : ''}</Typography>
              </Stack>;
            })}
          </Stack>}
        {apply.isError ? <Alert severity="error" sx={{ mt: 2 }}>{getErrorMessage(apply.error)}</Alert> : null}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={apply.isPending}>{tUi("Close")}</Button>
        <Button variant="contained" disabled={apply.isPending || choices.length === 0} onClick={async () => { if (pending.current) return; pending.current = true; try { await apply.mutateAsync({ assignments: choices, reassign: false }); } catch { /* Mutation keeps the error and choices. */ } finally { pending.current = false; } }}>{tUi("Apply matches")}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default FolderMatchDialog;

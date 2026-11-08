import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useId, useState } from 'react';
import { Alert, Button, Checkbox, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, FormControlLabel, Stack, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { scraperService, type OrphanedSource } from '../../services/scraperService';
import { useConfirm } from '../ConfirmDialog';
import { getErrorMessage } from '../../utils/errorUtils';

interface OrphanedSourcesDialogProps {
  open: boolean;
  onClose: () => void;
  onDone: (message: string) => void;
}

const describe = (row: OrphanedSource) => `${row.count} stream${row.count === 1 ? '' : 's'} · ${row.assigned_count} linked to TV channels`;

/** Streams left behind by sources that were removed; the user ticks which to delete. */
const OrphanedSourcesDialog: React.FC<OrphanedSourcesDialogProps> = ({ open, onClose, onDone }) => {
  const tUi = useUiText();
  const titleId = useId();
  const cache = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const rows = useQuery({ queryKey: ['scrapers', 'orphaned-sources'], queryFn: scraperService.orphanedSources, enabled: open });
  const [selected, setSelected] = useState<string[]>([]);
  useEffect(() => { if (rows.data) setSelected(rows.data.map((row) => row.source_url)); }, [rows.data]);
  const cleanup = useMutation({
    mutationFn: (urls: string[]) => scraperService.cleanupOrphanedSources(urls),
    onSuccess: (result) => {
      const removed = Object.values(result.deleted).reduce((sum, count) => sum + count, 0);
      const sources = Object.keys(result.deleted).length;
      void cache.invalidateQueries({ queryKey: ['acestream-channels'] });
      void cache.invalidateQueries({ queryKey: ['channel-sources'] });
      void cache.invalidateQueries({ queryKey: ['scrapers', 'orphaned-sources'] });
      onDone(`Removed ${removed} stream${removed === 1 ? '' : 's'} from ${sources} source${sources === 1 ? '' : 's'}.`);
      onClose();
    },
  });
  const toggle = (url: string, checked: boolean) => setSelected((current) => checked ? [...current, url] : current.filter((value) => value !== url));
  return (
    <Dialog open={open} onClose={cleanup.isPending ? undefined : onClose} aria-labelledby={titleId} maxWidth="sm" fullWidth>
      {dialog}
      <DialogTitle id={titleId}>{tUi("Clean up removed sources")}</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 1.5 }}>{tUi("Streams from sources that are no longer configured. Tick the ones to remove; catalogue, Telegram, saved-search and manual additions are not listed.")}</DialogContentText>
        {rows.isPending ? <CircularProgress aria-label={tUi("Loading removed sources")} /> : rows.isError ? <Alert severity="error" action={<Button onClick={() => void rows.refetch()}>{tUi("Retry")}</Button>}>{tUi("Could not load removed sources.")}</Alert>
          : rows.data.length === 0 ? <Typography>{tUi("No streams from removed sources.")}</Typography>
          : <Stack spacing={0.5}>
            {rows.data.map((row) => <FormControlLabel key={row.source_url} sx={{ alignItems: 'flex-start', overflowWrap: 'anywhere' }}
              control={<Checkbox checked={selected.includes(row.source_url)} disabled={cleanup.isPending} onChange={(_, checked) => toggle(row.source_url, checked)} />}
              label={<span><Typography component="span" display="block">{row.source_url}</Typography><Typography component="span" variant="body2" color="text.secondary">{describe(row)}</Typography></span>} />)}
          </Stack>}
        {cleanup.isError ? <Alert severity="error" sx={{ mt: 2 }}>{getErrorMessage(cleanup.error)}</Alert> : null}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={cleanup.isPending}>{tUi("Close")}</Button>
        <Button variant="contained" color="error" disabled={cleanup.isPending || selected.length === 0} onClick={async () => {
          const total = (rows.data ?? []).filter((row) => selected.includes(row.source_url)).reduce((sum, row) => sum + row.count, 0);
          if (await confirm({ title: uiText("Remove streams from removed sources?"), body: `${total} stream${total === 1 ? '' : 's'} from ${selected.length} source${selected.length === 1 ? '' : 's'} will be deleted, including streams linked to TV channels. TV channels are kept.`, confirmLabel: uiText("Remove streams"), danger: true })) cleanup.mutate(selected);
        }}>{tUi("Remove selected")}</Button>
      </DialogActions>
    </Dialog>
  );
};

export default OrphanedSourcesDialog;

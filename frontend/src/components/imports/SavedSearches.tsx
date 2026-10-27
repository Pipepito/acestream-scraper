import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, LinearProgress, Pagination, Stack, Switch, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import StatusLine from '../StatusLine';
import RowActionsMenu from '../RowActionsMenu';
import { useConfirm } from '../ConfirmDialog';
import { normalizeApiError } from '../../services/apiErrors';
import { savedSearchService as service, SavedSearch, SavedSearchPreview, SavedSearchResult } from '../../services/savedSearchService';
import { formatRelativeTime } from '../../utils/format';
import SavedSearchDialog from './SavedSearchDialog';

export const searchCounts = (r: SavedSearchResult) => `${r.added} added · ${r.existing} existing · ${r.excluded_candidates} excluded · ${r.unresolved_candidates} unresolved · ${r.deferred_candidates} deferred`;
export default function SavedSearches() {
  const cache = useQueryClient();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<SavedSearch | null | undefined>();
  const [preview, setPreview] = useState<{ row: SavedSearch; view: SavedSearchPreview }>();
  const { confirm, dialog } = useConfirm();
  const list = useQuery({ queryKey: ['saved-searches', { page }], queryFn: ({ signal }) => service.list((page - 1) * 50, signal),
    refetchInterval: query => query.state.data?.items.some(r => r.run_state) ? Math.min(10000, 2000 + query.state.dataUpdateCount * 500) : false });
  const completed = list.data?.items.filter(row => !row.run_state && row.last_finished_at).map(row => `${row.id}:${row.last_finished_at}`).join('|') || '';
  useEffect(() => { if (completed) void cache.invalidateQueries({ queryKey: ['acestream-channels'] }); }, [cache, completed]);
  const invalidate = () => { void cache.invalidateQueries({ queryKey: ['saved-searches'] }); void cache.invalidateQueries({ queryKey: ['saved-search'] }); };
  const save = useMutation({ mutationFn: (row: SavedSearch) => service.save({ ...row, refresh_enabled: !row.refresh_enabled }, row), onSuccess: invalidate });
  const remove = useMutation({ mutationFn: service.remove, onSuccess: invalidate });
  const run = useMutation({ mutationFn: ({ row, token }: { row: SavedSearch; token?: string }) => service.run(row, token), onSuccess: () => { invalidate(); setPreview(undefined); } });
  const inspect = useMutation({ mutationFn: service.preview, onSuccess: (view, row) => setPreview({ row, view }) });
  const error = list.error || save.error || remove.error || run.error || inspect.error;
  return <>
    <StatusLine items={[{ label: 'Saved searches', value: list.data?.total ?? '—' }]} />
    <ContentSection title="Saved searches" actions={<Button variant="contained" onClick={() => setEditing(null)}>Create search</Button>}>
      <Typography sx={{ mb: 2 }}>Import matching results on the source refresh schedule. <Button component={RouterLink} to="/settings?tab=automation">Edit schedule</Button></Typography>
      {error ? <Alert severity="error">{normalizeApiError(error).message} <Button component={RouterLink} to="/settings?tab=playback">Engine settings</Button></Alert> : null}
      {list.isLoading || inspect.isPending ? <LinearProgress aria-label={inspect.isPending ? 'Previewing search' : 'Loading saved searches'} /> : null}
      {list.data?.total === 0 ? <Typography color="text.secondary">Create a query here or save your last submitted query from <Button component={RouterLink} to="/search">Search</Button>. Automatic refresh starts off.</Typography> : null}
      {list.data?.items.map(row => <Stack key={row.id} direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }} alignItems={{ md: 'center' }}>
        <Box sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}><Typography variant="subtitle1">{row.name}</Typography><Typography variant="body2">{row.query} · {row.category || 'All categories'}</Typography>
          <Stack direction="row" spacing={1} sx={{ my: 1 }}><Chip size="small" label={(row.run_state || row.last_outcome || 'Never run').replace(/^./, first => first.toUpperCase())} /><Chip size="small" variant="outlined" label={row.refresh_enabled ? 'Automatic refresh on' : 'Paused'} /></Stack>
          <Typography variant="body2" color="text.secondary">{row.last_result ? searchCounts(row.last_result) : 'No imports yet'} · {formatRelativeTime(row.last_finished_at)}</Typography>
          {row.last_result?.stop_reason ? <Typography variant="body2">Stopped: {row.last_result.stop_reason.replace(/_/g, ' ')}</Typography> : null}
          {row.error_message ? <Alert severity="warning" sx={{ mt: 1 }}>{row.error_message}<Button component={RouterLink} to="/settings?tab=playback">Engine settings</Button></Alert> : null}
        </Box>
        <Stack direction="row" alignItems="center" spacing={1} flexWrap="wrap"><Switch checked={row.refresh_enabled} inputProps={{ 'aria-label': `Refresh ${row.name} automatically` }} onChange={() => save.mutate(row)} disabled={save.isPending} />
          <Button variant="outlined" disabled={Boolean(row.run_state) || run.isPending} onClick={() => run.mutate({ row })}>{row.run_state === 'waiting' ? 'Waiting' : row.run_state === 'running' ? 'Running' : 'Run now'}</Button>
          <RowActionsMenu label={`Actions for ${row.name}`} actions={[{ label: 'Edit', onClick: () => setEditing(row) }, { label: 'Preview', disabled: inspect.isPending, onClick: () => inspect.mutate(row) }, { label: 'Delete', danger: true, onClick: async () => { if (await confirm({ title: 'Delete saved search?', body: 'Imported channels remain. This removes the definition and its discovery memberships.', confirmLabel: 'Delete' })) remove.mutate(row); } }]} />
        </Stack>
      </Stack>)}
      {(list.data?.total ?? 0) > 50 ? <Pagination page={page} count={Math.ceil((list.data?.total ?? 0) / 50)} onChange={(_, value) => setPage(value)} sx={{ mt: 2 }} /> : null}
    </ContentSection>
    {editing !== undefined ? <SavedSearchDialog row={editing || undefined} onClose={() => setEditing(undefined)} /> : null}
    <Dialog open={Boolean(preview)} onClose={() => setPreview(undefined)} fullWidth aria-labelledby="search-preview-title"><DialogTitle id="search-preview-title">Search preview</DialogTitle><DialogContent>
      {preview ? <Stack spacing={2}><Alert severity={preview.view.result.outcome === 'complete' ? 'info' : 'warning'}>{preview.view.result.outcome} · {searchCounts(preview.view.result)}. Nothing has been imported.</Alert>
        <Typography>Import this preview uses only these results. Preview expires after five minutes.</Typography>
        {(preview.view.result.samples ?? []).map((item, i) => <Typography variant="body2" key={`${item.infohash}-${i}`} sx={{ overflowWrap: 'anywhere' }}>{item.content_id || item.infohash} · {item.outcome}{item.rule_ids?.length ? <Button component={RouterLink} to={`/scraper?tab=exclusions#rule-${item.rule_ids[0]}`}>Exclusion rule</Button> : null}</Typography>)}
        {preview.view.result.samples_truncated ? <Typography>Showing the first 100 outcomes.</Typography> : null}
        {run.error ? <Alert severity="error">{normalizeApiError(run.error).message}</Alert> : null}</Stack> : null}
    </DialogContent><DialogActions><Button onClick={() => setPreview(undefined)}>Close</Button><Button variant="contained" disabled={!preview || run.isPending || ['failed', 'skipped'].includes(preview?.view.result.outcome || '')} onClick={() => { if (preview) run.mutate({ row: preview.row, token: preview.view.preview_token }); }}>Import this preview</Button></DialogActions></Dialog>
    {dialog}
  </>;
}

import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, LinearProgress, MenuItem, Pagination, Stack, Switch, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import StatusLine from '../StatusLine';
import RowActionsMenu from '../RowActionsMenu';
import { useConfirm } from '../ConfirmDialog';
import { normalizeApiError } from '../../services/apiErrors';
import { importExclusionService as service, ExclusionInput, ExclusionRule, ExclusionPreview } from '../../services/importExclusionService';
import { formatRelativeTime } from '../../utils/format';

const labels = { name_contains: 'Name contains', name_equals: 'Name equals', stream_id_equals: 'Stream ID equals' };
const initial: ExclusionInput = { kind: 'name_contains', value: '', enabled: true, note: '' };
export default function ImportExclusions() {
  const cache = useQueryClient();
  const { hash } = useLocation();
  const ruleId = /^#rule-[1-9]\d*$/.test(hash) ? Number(hash.slice(6)) : undefined;
  const [page, setPage] = useState(1);
  const [form, setForm] = useState<ExclusionInput>(initial);
  const [editing, setEditing] = useState<ExclusionRule>();
  const [open, setOpen] = useState(false);
  const [preview, setPreview] = useState<ExclusionPreview>();
  const { confirm, dialog } = useConfirm();
  const list = useQuery({ queryKey: ['import-exclusions', { page, ruleId }], queryFn: ({ signal }) => service.list(ruleId ? 0 : (page - 1) * 50, signal, ruleId) });
  const invalidate = () => { void cache.invalidateQueries({ queryKey: ['import-exclusions'] }); void cache.invalidateQueries({ queryKey: ['import-policy'] }); setPreview(undefined); };
  const save = useMutation({ mutationFn: ({ data, row }: { data: ExclusionInput; row?: ExclusionRule }) => service.save(data, row), onSuccess: () => { invalidate(); setOpen(false); } });
  const remove = useMutation({ mutationFn: service.remove, onSuccess: invalidate });
  const inspect = useMutation({ mutationFn: service.preview, onSuccess: setPreview });
  const error = save.error || remove.error || list.error || inspect.error;
  const edit = (row?: ExclusionRule) => { setEditing(row); setForm(row || initial); setPreview(undefined); save.reset(); inspect.reset(); setOpen(true); };
  return <>
    <StatusLine items={[{ label: 'Rules', value: list.data?.total ?? '—' }, { label: 'Policy revision', value: list.data?.policy_revision ?? '—' }]} />
    <ContentSection title="Import exclusions" actions={<Button variant="contained" onClick={() => edit()}>Add exclusion</Button>}>
      <Typography sx={{ mb: 2 }}>Skips future imports. Existing channels stay.</Typography>
      {ruleId ? <Alert severity="info">Showing rule #{ruleId}. <Button component={RouterLink} to="/scraper?tab=exclusions">Show all rules</Button></Alert> : null}
      {error ? <Alert severity="error">{normalizeApiError(error).message}</Alert> : null}
      {list.isLoading ? <LinearProgress aria-label="Loading exclusions" /> : null}
      {list.data?.total === 0 ? <Typography color="text.secondary">{ruleId ? 'This exclusion no longer exists.' : 'Add a name or stream ID rule to skip unwanted discoveries across your import sources.'}</Typography> : null}
      {list.data?.items.map(row => <Stack key={row.id} id={`rule-${row.id}`} direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ py: 2, borderBottom: 1, borderColor: 'divider' }} alignItems={{ sm: 'center' }}>
        <Box sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}><Typography variant="subtitle2">#{row.id} · {labels[row.kind]} · {row.value}</Typography><Typography variant="body2" color="text.secondary">{row.note} · Edited {formatRelativeTime(row.updated_at)}</Typography></Box>
        <Stack direction="row" alignItems="center"><Chip size="small" label={row.enabled ? 'Enabled' : 'Disabled'} /><Switch checked={row.enabled} disabled={save.isPending} inputProps={{ 'aria-label': `Enable ${row.value}` }} onChange={(_, enabled) => save.mutate({ data: { ...row, enabled }, row })} />
          <RowActionsMenu label={`Actions for ${row.value}`} actions={[{ label: 'Edit', onClick: () => edit(row) }, { label: 'Delete', danger: true, onClick: async () => { if (await confirm({ title: 'Delete exclusion?', body: 'Future imports may discover matching streams again. Existing channels stay.', confirmLabel: 'Delete' })) remove.mutate(row); } }]} />
        </Stack>
      </Stack>)}
      {(list.data?.total ?? 0) > 50 ? <Pagination page={page} count={Math.ceil((list.data?.total ?? 0) / 50)} onChange={(_, value) => setPage(value)} sx={{ mt: 2 }} /> : null}
    </ContentSection>
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="sm" aria-labelledby="exclusion-dialog-title">
      <DialogTitle id="exclusion-dialog-title">{editing ? 'Edit exclusion' : 'Add exclusion'}</DialogTitle>
      <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
        <TextField select label="Rule type" value={form.kind} onChange={e => { setForm({ ...form, kind: e.target.value as ExclusionInput['kind'] }); setPreview(undefined); }}>{Object.entries(labels).map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}</TextField>
        <TextField label="Value" value={form.value} inputProps={{ maxLength: 256 }} onChange={e => { setForm({ ...form, value: e.target.value }); setPreview(undefined); }} helperText="Literal matching, ignoring name case and repeated spaces. No wildcards." />
        <TextField label="Note (optional)" value={form.note ?? ''} inputProps={{ maxLength: 500 }} onChange={e => setForm({ ...form, note: e.target.value })} />
        <FormControlLabel control={<Switch checked={form.enabled} onChange={(_, enabled) => setForm({ ...form, enabled })} />} label="Enabled" />
        <Button disabled={!form.value.trim() || inspect.isPending} onClick={() => inspect.mutate(form)}>Preview matches</Button>
        {preview ? <Alert severity="info">{preview.complete ? '' : 'At least '}{preview.matched} matches in {preview.scanned} current channels. {preview.complete ? '' : 'Preview stopped at its scan limit. '}Future publisher names may differ.
          {preview.examples.map(item => <Typography key={item.channel_id} variant="body2" sx={{ overflowWrap: 'anywhere' }}>{item.name}</Typography>)}
        </Alert> : null}
        {save.error || inspect.error ? <Alert severity="error">{normalizeApiError(save.error || inspect.error).message}</Alert> : null}
      </Stack></DialogContent>
      <DialogActions><Button onClick={() => setOpen(false)}>Cancel</Button><Button variant="contained" disabled={!form.value.trim() || save.isPending} onClick={() => save.mutate({ data: form, row: editing })}>Save exclusion</Button></DialogActions>
    </Dialog>{dialog}
  </>;
}

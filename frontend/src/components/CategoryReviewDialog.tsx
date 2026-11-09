import React, { useState } from 'react';
import { Alert, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, LinearProgress, Stack, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { tvChannelService } from '../services/tvChannelService';
import { useUiText } from '../i18n/useUiText';
import { getErrorMessage } from '../utils/errorUtils';
import { useUnsavedChanges } from './UnsavedChanges';
import { useConfirm } from './ConfirmDialog';
import { translateKnown } from '../i18n/text';

export default function CategoryReviewDialog({ ids, onClose }: { ids: number[]; onClose: () => void }) {
  const tUi = useUiText();
  const { i18n } = useTranslation();
  const cache = useQueryClient();
  const [selected, setSelected] = useState<number[]>([]);
  const definitions = useQuery({ queryKey: ['categoryDefinitions'], queryFn: tvChannelService.categoryDefinitions });
  const preview = useQuery({ queryKey: ['tvChannels', 'category-review', ids], queryFn: () => tvChannelService.previewCategories(ids), retry: false, staleTime: Infinity, refetchOnWindowFocus: false });
  const apply = useMutation({ mutationFn: () => tvChannelService.applyCategories((preview.data ?? []).filter(row => selected.includes(row.channel_id) && row.suggested_category).map(row => ({ channel_id: row.channel_id, category_id: row.suggested_category!, fingerprint: row.fingerprint }))),
    onSuccess: async () => { setSelected([]); await cache.invalidateQueries({ queryKey: ['tvChannels'] }); await cache.invalidateQueries({ queryKey: ['tvChannel'] }); onClose(); } });
  const reset = useMutation({ mutationFn: ({ id, revision }: { id: number; revision: number }) => tvChannelService.assignCategory(id, { mode: 'automatic', expected_revision: revision }),
    onSuccess: async () => { setSelected([]); await cache.invalidateQueries({ queryKey: ['tvChannels'] }); await cache.invalidateQueries({ queryKey: ['tvChannel'] }); } });
  const pending = apply.isPending || reset.isPending;
  useUnsavedChanges(selected.length > 0, pending);
  const { confirm, dialog } = useConfirm();
  const close = async () => {
    if (pending) return;
    if (selected.length && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onClose();
  };
  const allowSuggestions = async (id: number, revision: number) => {
    if (await confirm(() => ({ title: tUi('Allow category suggestions?'), body: tUi('This clears the saved category. Review a new suggestion before applying it.'), confirmLabel: tUi('Clear category'), danger: true }))) reset.mutate({ id, revision });
  };
  const label = (id: string) => {
    const item = definitions.data?.find(row => row.id === id);
    return item ? i18n.resolvedLanguage?.startsWith('es') ? item.label_es : item.label : id;
  };
  return <>{dialog}<Dialog open fullWidth maxWidth="md" onClose={() => void close()}>
    <DialogTitle>{tUi('Review channel categories')}</DialogTitle>
    <DialogContent dividers>
      <Typography variant="body2" sx={{ mb: 2 }}>{tUi('Suggestions for the channels on this page. Select the assignments you want to save. Manual and reviewed categories are protected.')}</Typography>
      {preview.isLoading ? <LinearProgress /> : null}
      {preview.isError || apply.isError || reset.isError ? <Alert severity="error" action={<Button disabled={pending} onClick={() => { setSelected([]); apply.reset(); reset.reset(); void preview.refetch(); }}>{tUi('Review again')}</Button>}>{getErrorMessage(preview.error ?? apply.error ?? reset.error)}</Alert> : null}
      <Stack spacing={1} component="fieldset" disabled={pending} sx={{ border: 0, p: 0, m: 0, minWidth: 0 }}>
        {preview.data?.map(row => <Stack key={row.channel_id} sx={{ borderBottom: 1, borderColor: 'divider', pb: 1.5 }}>
          <FormControlLabel control={<Checkbox disabled={!row.suggested_category} checked={selected.includes(row.channel_id)} onChange={(_, checked) => setSelected(previous => checked ? [...previous, row.channel_id] : previous.filter(id => id !== row.channel_id))} />}
            label={<Typography sx={{ overflowWrap: 'anywhere' }}>{row.name} · {row.current_category ? label(row.current_category) : tUi('Uncategorized')}{row.suggested_category ? ` → ${label(row.suggested_category)}` : ''}</Typography>} />
          <Typography variant="body2" color="text.secondary">{translateKnown(row.reason)}</Typography>
          {row.evidence.map((text, index) => <Typography key={index} variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{text}</Typography>)}
          {!row.suggested_category && row.reason === 'Saved assignment is protected' ? <Button size="small" sx={{ alignSelf: 'flex-start' }} onClick={() => void allowSuggestions(row.channel_id, row.category_revision)}>{tUi('Allow suggestions')}</Button> : null}
        </Stack>)}
      </Stack>
    </DialogContent>
    <DialogActions><Button disabled={pending} onClick={() => void close()}>{tUi('Cancel')}</Button><Button variant="contained" disabled={pending || !selected.length || apply.isError || preview.isFetching} onClick={() => apply.mutate()}>{tUi('Apply selected')} · {selected.length}</Button></DialogActions>
  </Dialog></>;
}

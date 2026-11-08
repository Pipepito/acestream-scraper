import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, Switch, TextField } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { savedSearchService, SavedSearchInput, SavedSearch } from '../../services/savedSearchService';
import { normalizeApiError } from '../../services/apiErrors';
interface Props { initial?: SavedSearchInput; row?: SavedSearch; onClose: () => void }
export default function SavedSearchDialog({ initial, row, onClose }: Props) {
  const tUi = useUiText();
  const [form, setForm] = useState<SavedSearchInput>(row || initial || { name: '', query: '', category: '', refresh_enabled: false });
  const cache = useQueryClient();
  const save = useMutation({ mutationFn: () => savedSearchService.save(form, row), onSuccess: () => { void cache.invalidateQueries({ queryKey: ['saved-searches'] }); void cache.invalidateQueries({ queryKey: ['saved-search'] }); onClose(); } });
  return <Dialog open onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="saved-search-dialog-title">
    <DialogTitle id="saved-search-dialog-title">{row ? tUi("Edit saved search") : tUi("Save search")}</DialogTitle>
    <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      <TextField label={tUi("Name")} value={form.name} inputProps={{ maxLength: 100 }} onChange={e => setForm({ ...form, name: e.target.value })} />
      <TextField label={tUi("Query")} value={form.query} inputProps={{ maxLength: 256 }} onChange={e => setForm({ ...form, query: e.target.value, refresh_enabled: false })} />
      <TextField label={tUi("Category")} value={form.category} inputProps={{ maxLength: 100 }} onChange={e => setForm({ ...form, category: e.target.value, refresh_enabled: false })} helperText={tUi("Leave blank for all categories.")} />
      <FormControlLabel control={<Switch checked={form.refresh_enabled} onChange={(_, refresh_enabled) => setForm({ ...form, refresh_enabled })} />} label={tUi("Import matching results on the source refresh schedule.")} />
      <Alert severity="info">{tUi("Saving stores this definition only. Use Run now to import results. Changing the query or category pauses automatic refresh until you enable it again.")}</Alert>
      {save.error ? <Alert severity="error">{normalizeApiError(save.error).message}</Alert> : null}
    </Stack></DialogContent>
    <DialogActions><Button onClick={onClose}>{tUi("Cancel")}</Button><Button variant="contained" disabled={!form.name.trim() || !form.query.trim() || save.isPending} onClick={() => save.mutate()}>{tUi("Save")}</Button></DialogActions>
  </Dialog>;
}

import React, { useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, Switch, TextField } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { savedSearchService, SavedSearchInput, SavedSearch } from '../../services/savedSearchService';
import { normalizeApiError } from '../../services/apiErrors';
interface Props { initial?: SavedSearchInput; row?: SavedSearch; onClose: () => void }
export default function SavedSearchDialog({ initial, row, onClose }: Props) {
  const [form, setForm] = useState<SavedSearchInput>(row || initial || { name: '', query: '', category: '', refresh_enabled: false });
  const cache = useQueryClient();
  const save = useMutation({ mutationFn: () => savedSearchService.save(form, row), onSuccess: () => { void cache.invalidateQueries({ queryKey: ['saved-searches'] }); void cache.invalidateQueries({ queryKey: ['saved-search'] }); onClose(); } });
  return <Dialog open onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="saved-search-dialog-title">
    <DialogTitle id="saved-search-dialog-title">{row ? 'Edit saved search' : 'Save search'}</DialogTitle>
    <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      <TextField label="Name" value={form.name} inputProps={{ maxLength: 100 }} onChange={e => setForm({ ...form, name: e.target.value })} />
      <TextField label="Query" value={form.query} inputProps={{ maxLength: 256 }} onChange={e => setForm({ ...form, query: e.target.value, refresh_enabled: false })} />
      <TextField label="Category" value={form.category} inputProps={{ maxLength: 100 }} onChange={e => setForm({ ...form, category: e.target.value, refresh_enabled: false })} helperText="Leave blank for all categories." />
      <FormControlLabel control={<Switch checked={form.refresh_enabled} onChange={(_, refresh_enabled) => setForm({ ...form, refresh_enabled })} />} label="Import matching results on the source refresh schedule." />
      <Alert severity="info">Saving stores this definition only. Use Run now to import results. Changing the query or category pauses automatic refresh until you enable it again.</Alert>
      {save.error ? <Alert severity="error">{normalizeApiError(save.error).message}</Alert> : null}
    </Stack></DialogContent>
    <DialogActions><Button onClick={onClose}>Cancel</Button><Button variant="contained" disabled={!form.name.trim() || !form.query.trim() || save.isPending} onClick={() => save.mutate()}>Save</Button></DialogActions>
  </Dialog>;
}

import { Alert,Button,Dialog,DialogActions,DialogContent,DialogTitle,FormControlLabel,Stack,Switch,TextField } from '@mui/material';
import { useMutation,useQueryClient } from '@tanstack/react-query';
import React,{ useRef, useState } from 'react';
import { useUiText } from '../../i18n/useUiText';
import { SavedSearch,SavedSearchInput,savedSearchService } from '../../services/savedSearchService';
import { getErrorMessage } from '../../utils/errorUtils';
import { useConfirm } from '../ConfirmDialog';
import { useUnsavedChanges } from '../UnsavedChanges';
interface Props { initial?: SavedSearchInput; row?: SavedSearch; onClose: () => void }
export default function SavedSearchDialog({ initial, row, onClose }: Props) {
  const tUi = useUiText();
  const [original] = useState<SavedSearchInput>(() => row ? { name: row.name, query: row.query, category: row.category, refresh_enabled: row.refresh_enabled } : initial || { name: '', query: '', category: '', refresh_enabled: false });
  const [form, setForm] = useState(original);
  const [reviewedRow] = useState(row);
  const pending = useRef(false);
  const { confirm, dialog } = useConfirm();
  const dirty = JSON.stringify(form) !== JSON.stringify(original);
  const cache = useQueryClient();
  const save = useMutation({ mutationFn: () => savedSearchService.save(form, reviewedRow), onSuccess: () => { void cache.invalidateQueries({ queryKey: ['saved-searches'] }); void cache.invalidateQueries({ queryKey: ['saved-search'] }); onClose(); } });
  useUnsavedChanges(dirty, save.isPending);
  const close = async () => {
    if (pending.current) return;
    if (dirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    onClose();
  };
  const submit = async () => {
    if (pending.current || !form.name.trim() || !form.query.trim()) return;
    pending.current = true;
    try { await save.mutateAsync(); } catch { /* Mutation retains its error and draft. */ }
    finally { pending.current = false; }
  };
  return <><Dialog open onClose={() => void close()} fullWidth maxWidth="sm" aria-labelledby="saved-search-dialog-title">
    <DialogTitle id="saved-search-dialog-title">{row ? tUi("Edit saved search") : tUi("Save search")}</DialogTitle>
    <DialogContent><Stack component="fieldset" disabled={save.isPending} spacing={2} sx={{ pt: 1, m: 0, p: 0, border: 0, minWidth: 0 }}>
      <TextField label={tUi("Name")} value={form.name} inputProps={{ maxLength: 100 }} onChange={e => setForm({ ...form, name: e.target.value })} />
      <TextField label={tUi("Query")} value={form.query} inputProps={{ maxLength: 256 }} onChange={e => setForm({ ...form, query: e.target.value, refresh_enabled: false })} />
      <TextField label={tUi("Category")} value={form.category} inputProps={{ maxLength: 100 }} onChange={e => setForm({ ...form, category: e.target.value, refresh_enabled: false })} helperText={tUi("Leave blank for all categories.")} />
      <FormControlLabel control={<Switch checked={form.refresh_enabled} onChange={(_, refresh_enabled) => setForm({ ...form, refresh_enabled })} />} label={tUi("Import matching results on the source refresh schedule.")} />
      <Alert severity="info">{tUi("Saving stores this definition only. Use Run now to import results. Changing the query or category pauses automatic refresh until you enable it again.")}</Alert>
      {save.error ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    </Stack></DialogContent>
    <DialogActions><Button disabled={save.isPending} onClick={() => void close()}>{tUi("Cancel")}</Button><Button variant="contained" disabled={!form.name.trim() || !form.query.trim() || save.isPending} onClick={() => void submit()}>{tUi("Save")}</Button></DialogActions>
  </Dialog>{dialog}</>;
}

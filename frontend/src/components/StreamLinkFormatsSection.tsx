import { useUnsavedChanges } from './UnsavedChanges';
import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { getErrorMessage } from '../utils/errorUtils';
import React, { useState } from 'react';
import { Alert, Box, Button, Checkbox, Chip, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, IconButton, Stack, TextField, Tooltip, Typography } from '@mui/material';
import { Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import { useBaseUrl, useUpdateBaseUrl } from '../hooks/useConfig';
import { useBaseUrls, useCreateBaseUrl, usePatchBaseUrl, useDeleteBaseUrl } from '../hooks/useBaseUrls';
import { StreamBaseUrl } from '../services/baseUrlService';
import { ApiError } from '../services/apiErrors';
import { useConfirm } from './ConfirmDialog';
import ContentSection from './layout/ContentSection';
import StreamFormatSuggestions from './StreamFormatSuggestions';
type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string, severity: FeedbackSeverity) => void;

const describeSaveError = (error: unknown, attemptedName: string, fallback: string): string => {
  if (error instanceof ApiError && error.status === 409) {
    return uiText('A link format named "{{name}}" already exists. Choose a different name.', { name: attemptedName });
  }
  if (error instanceof ApiError && error.message) {
    return getErrorMessage(error);
  }
  return uiText(fallback, { defaultValue: fallback });
};

interface StreamLinkFormatsSectionProps {
  notify: Notify;
}

/**
 * "Stream link formats": the named base URL entries used when generating playlist links.
 * The legacy `base_url` setting shows as a built-in "Default" row (editable in place) until a
 * named entry is marked default.
 */
const StreamLinkFormatsSection: React.FC<StreamLinkFormatsSectionProps> = ({ notify }) => {
  const tUi = useUiText();
  const { confirm, dialog: confirmDialog } = useConfirm();
  const baseUrlsQuery = useBaseUrls();
  const createBaseUrlMutation = useCreateBaseUrl();
  const patchBaseUrlMutation = usePatchBaseUrl();
  const deleteBaseUrlMutation = useDeleteBaseUrl();
  const legacyBaseUrlQuery = useBaseUrl();
  const updateLegacyBaseUrlMutation = useUpdateBaseUrl();

  const [addOpen, setAddOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newPattern, setNewPattern] = useState('');
  const [newIsDefault, setNewIsDefault] = useState(false);
  const [editingEntry, setEditingEntry] = useState<StreamBaseUrl | 'builtin' | null>(null);
  const [editName, setEditName] = useState('');
  const [editPattern, setEditPattern] = useState('');

  const entries = baseUrlsQuery.data ?? [];
  const hasNamedDefault = entries.some((entry) => entry.is_default);
  const isMutating =
    createBaseUrlMutation.isPending || patchBaseUrlMutation.isPending || deleteBaseUrlMutation.isPending || updateLegacyBaseUrlMutation.isPending;

  const addDirty = addOpen && Boolean(newName || newPattern || newIsDefault);
  const editDirty = Boolean(editingEntry && (editPattern !== (editingEntry === 'builtin' ? legacyBaseUrlQuery.data ?? '' : editingEntry.pattern)
    || editingEntry !== 'builtin' && editName !== editingEntry.name));
  useUnsavedChanges(addDirty || editDirty, isMutating);
  const requestClose = async (kind: 'add' | 'edit') => {
    if (isMutating) return;
    if ((kind === 'add' ? addDirty : editDirty) && !await confirm({ title: tUi('Discard unsaved changes?'),
      body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true })) return;
    if (kind === 'edit') setEditingEntry(null);
    else { setAddOpen(false); setNewName(''); setNewPattern(''); setNewIsDefault(false); }
  };

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    const pattern = newPattern.trim();
    if (!name || !pattern || isMutating) return;
    createBaseUrlMutation.mutate(
      { name, pattern, is_default: newIsDefault },
      {
        onSuccess: () => {
          setNewName('');
          setNewPattern('');
          setNewIsDefault(false);
          setAddOpen(false);
          notify(tUi('Link format "{{name}}" added', { name }), 'success');
        },
        onError: (error) => notify(describeSaveError(error, name, 'Failed to add the link format'), 'error'),
      }
    );
  };

  const handleMakeDefault = (entry: StreamBaseUrl) => {
    patchBaseUrlMutation.mutate(
      { id: entry.id, data: { is_default: true } },
      {
        onSuccess: () => notify(tUi('"{{name}}" is now the default link format', { name: entry.name }), 'success'),
        onError: (error) => notify(describeSaveError(error, entry.name, 'Failed to change the default link format'), 'error'),
      }
    );
  };

  const handleDelete = async (entry: StreamBaseUrl) => {
    const ok = await confirm({
      title: tUi('Delete the link format “{{name}}”?', { name: entry.name }),
      body: tUi('Playlists that were built with this format fall back to the default one.'),
      confirmLabel: uiText("Delete"),
      danger: true,
    });
    if (!ok) return;
    deleteBaseUrlMutation.mutate(entry.id, {
      onSuccess: () => notify(tUi('Link format "{{name}}" deleted', { name: entry.name }), 'success'),
      onError: (error) => notify(describeSaveError(error, entry.name, 'Failed to delete the link format'), 'error'),
    });
  };

  const openEditDialog = (entry: StreamBaseUrl | 'builtin') => {
    setEditingEntry(entry);
    setEditName(entry === 'builtin' ? uiText("Default") : entry.name);
    setEditPattern(entry === 'builtin' ? legacyBaseUrlQuery.data ?? '' : entry.pattern);
  };

  const closeEditDialog = () => setEditingEntry(null);

  const handleEditSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEntry || isMutating) return;
    const name = editName.trim();
    const pattern = editPattern.trim();
    if (!pattern || (editingEntry !== 'builtin' && !name)) return;
    if (editingEntry === 'builtin') {
      updateLegacyBaseUrlMutation.mutate(pattern, {
        onSuccess: () => {
          closeEditDialog();
          notify(tUi("Default link format updated"), 'success');
        },
        onError: (error) => notify(getErrorMessage(error), 'error'),
      });
      return;
    }
    patchBaseUrlMutation.mutate(
      { id: editingEntry.id, data: { name, pattern } },
      {
        onSuccess: () => {
          closeEditDialog();
          notify(tUi('Link format "{{name}}" updated', { name }), 'success');
        },
        onError: (error) => notify(describeSaveError(error, name, 'Failed to update the link format'), 'error'),
      }
    );
  };

  const renderRow = (key: string | number, name: string, pattern: string, isDefault: boolean, actions: React.ReactNode) => (
    <Box
      key={key}
      sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 1, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, py: 0.75 }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Box sx={{ typography: 'body2', fontWeight: 600, wordBreak: 'break-word' }}>{name}</Box>
          {isDefault ? <Chip label={tUi("Default")} color="primary" size="small" /> : null}
        </Box>
        <Box sx={{ typography: 'body2', color: 'text.secondary', fontFamily: 'monospace', wordBreak: 'break-all' }}>{pattern}</Box>
      </Box>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ flexShrink: 0 }}>
        {actions}
      </Stack>
    </Box>
  );

  return (
    <ContentSection
      title={tUi("Stream link formats")}
      description={tUi("How each channel link is written in the playlist. Pick the one your player understands; the Default is used unless the playlist asks for another.")}
      actions={
        <Button variant="outlined" size="small" onClick={() => setAddOpen(true)}>
          {tUi("Add format")}</Button>
      }
    >
      <Stack spacing={1.5}>
        <StreamFormatSuggestions onSelect={(name, pattern) => {
          setNewName(name);
          setNewPattern(pattern);
          setAddOpen(true);
        }} />
        {baseUrlsQuery.isLoading ? (
          <Box display="flex" alignItems="center">
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Box component="span">{tUi("Loading link formats...")}</Box>
          </Box>
        ) : baseUrlsQuery.error ? (
          <Alert severity="warning">{tUi("Could not load the saved link formats. Try reloading the page.")}</Alert>
        ) : (
          <Stack spacing={0.5} divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
            {!hasNamedDefault
              ? renderRow(
                  'builtin',
                  tUi('Default'),
                  legacyBaseUrlQuery.data ?? 'acestream://',
                  true,
                  <Tooltip title={tUi("Edit the default format")}>
                    <IconButton size="small" aria-label={tUi("Edit default link format")} onClick={() => openEditDialog('builtin')} disabled={isMutating}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )
              : null}
            {entries.map((entry) =>
              renderRow(
                entry.id,
                entry.name,
                entry.pattern,
                Boolean(entry.is_default),
                <>
                  {!entry.is_default ? (
                    <Button size="small" variant="outlined" onClick={() => handleMakeDefault(entry)} disabled={isMutating}>
                      {tUi("Make default")}</Button>
                  ) : null}
                  <IconButton size="small" aria-label={tUi("Edit base URL {{value0}}", { value0: entry.name })} onClick={() => openEditDialog(entry)} disabled={isMutating}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" aria-label={tUi("Delete base URL {{value0}}", { value0: entry.name })} onClick={() => handleDelete(entry)} disabled={isMutating}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </>
              )
            )}
          </Stack>
        )}
        <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
          {tUi("Use")}{' '}<code>{'{tv_channel_id}'}</code> {' '}{tUi("with")}{' '}<code>{tUi("/tuner/channel/")}</code> {' '}{tUi("for one stable relay entry per TV channel and automatic source failover. Playlist can optionally append unassigned streams using individual relay URLs.")}{' '}<code>{'{channel_id}'}</code> {' '}{tUi("is the AceStream hash for a specific source.")}{' '}
          {tUi("A format without placeholders is a prefix put before the channel id (like")}{' '}<code>{tUi("acestream://")}</code>{tUi("). A format with")}{' '}
          <code>{'{channel_id}'}</code> {' '}{tUi("is a template and may also use")}{' '}<code>{'{pid}'}</code>{tUi(", for example")}{' '}
          <code>{'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}'}</code>.
        </Typography>
      </Stack>

      <Dialog open={addOpen} onClose={() => void requestClose('add')} fullWidth maxWidth="sm">
        <form onSubmit={handleAddSubmit}>
          <DialogTitle>{tUi("Add link format")}</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label={tUi("Name")} fullWidth disabled={isMutating} value={newName} onChange={(e) => setNewName(e.target.value)} helperText={tUi("A short label, e.g. VLC or Ace player")} />
              <TextField
                label={tUi("Pattern")}
                fullWidth
                disabled={isMutating} value={newPattern}
                onChange={(e) => setNewPattern(e.target.value)}
                helperText={tUi('Use {tv_channel_id} for a stable TV relay, or {channel_id} for a specific stream')}
              />
              <FormControlLabel control={<Checkbox disabled={isMutating} checked={newIsDefault} onChange={(e) => setNewIsDefault(e.target.checked)} />} label={tUi("Set as default")} />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => void requestClose('add')} disabled={isMutating} color="inherit">
              {tUi("Cancel")}</Button>
            <Button type="submit" variant="contained" color="primary" disabled={!newName.trim() || !newPattern.trim() || createBaseUrlMutation.isPending}>
              {createBaseUrlMutation.isPending ? <CircularProgress size={24} color="inherit" /> : tUi("Add base URL")}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <Dialog open={Boolean(editingEntry)} onClose={() => void requestClose('edit')} fullWidth maxWidth="sm">
        <form onSubmit={handleEditSave}>
          <DialogTitle>{editingEntry === 'builtin' ? tUi("Edit default link format") : tUi("Edit link format")}</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              {editingEntry !== 'builtin' ? <TextField label={tUi("Name")} fullWidth disabled={isMutating} value={editName} onChange={(e) => setEditName(e.target.value)} /> : null}
              <TextField
                label={tUi("Pattern")}
                fullWidth
                disabled={isMutating} value={editPattern}
                onChange={(e) => setEditPattern(e.target.value)}
                helperText={tUi('Use {tv_channel_id} for a stable TV relay, or {channel_id} for a specific stream')}
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => void requestClose('edit')} disabled={isMutating} color="inherit">
              {tUi("Cancel")}</Button>
            <Button type="submit" variant="contained" color="primary" disabled={!editPattern.trim() || (editingEntry !== 'builtin' && !editName.trim()) || isMutating}>
              {tUi("Save changes")}</Button>
          </DialogActions>
        </form>
      </Dialog>
      {confirmDialog}
    </ContentSection>
  );
};


export default StreamLinkFormatsSection;

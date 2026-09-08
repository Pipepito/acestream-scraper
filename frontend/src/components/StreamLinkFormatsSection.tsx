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
    return `A link format named "${attemptedName}" already exists. Choose a different name.`;
  }
  if (error instanceof ApiError && error.message) {
    return error.message;
  }
  return fallback;
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

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const name = newName.trim();
    const pattern = newPattern.trim();
    if (!name || !pattern) return;
    createBaseUrlMutation.mutate(
      { name, pattern, is_default: newIsDefault },
      {
        onSuccess: () => {
          setNewName('');
          setNewPattern('');
          setNewIsDefault(false);
          setAddOpen(false);
          notify(`Link format "${name}" added`, 'success');
        },
        onError: (error) => notify(describeSaveError(error, name, 'Failed to add the link format'), 'error'),
      }
    );
  };

  const handleMakeDefault = (entry: StreamBaseUrl) => {
    patchBaseUrlMutation.mutate(
      { id: entry.id, data: { is_default: true } },
      {
        onSuccess: () => notify(`"${entry.name}" is now the default link format`, 'success'),
        onError: (error) => notify(describeSaveError(error, entry.name, 'Failed to change the default link format'), 'error'),
      }
    );
  };

  const handleDelete = async (entry: StreamBaseUrl) => {
    const ok = await confirm({
      title: `Delete the link format “${entry.name}”?`,
      body: 'Playlists that were built with this format fall back to the default one.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    deleteBaseUrlMutation.mutate(entry.id, {
      onSuccess: () => notify(`Link format "${entry.name}" deleted`, 'success'),
      onError: (error) => notify(describeSaveError(error, entry.name, 'Failed to delete the link format'), 'error'),
    });
  };

  const openEditDialog = (entry: StreamBaseUrl | 'builtin') => {
    setEditingEntry(entry);
    setEditName(entry === 'builtin' ? 'Default' : entry.name);
    setEditPattern(entry === 'builtin' ? legacyBaseUrlQuery.data ?? '' : entry.pattern);
  };

  const closeEditDialog = () => setEditingEntry(null);

  const handleEditSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEntry) return;
    const name = editName.trim();
    const pattern = editPattern.trim();
    if (!pattern || (editingEntry !== 'builtin' && !name)) return;
    if (editingEntry === 'builtin') {
      updateLegacyBaseUrlMutation.mutate(pattern, {
        onSuccess: () => {
          closeEditDialog();
          notify('Default link format updated', 'success');
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
          notify(`Link format "${name}" updated`, 'success');
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
          {isDefault ? <Chip label="Default" color="primary" size="small" /> : null}
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
      title="Stream link formats"
      description="How each channel link is written in the playlist. Pick the one your player understands; the Default is used unless the playlist asks for another."
      actions={
        <Button variant="outlined" size="small" onClick={() => setAddOpen(true)}>
          Add format
        </Button>
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
            <Box component="span">Loading link formats...</Box>
          </Box>
        ) : baseUrlsQuery.error ? (
          <Alert severity="warning">Could not load the saved link formats. Try reloading the page.</Alert>
        ) : (
          <Stack spacing={0.5} divider={<Box sx={{ borderBottom: 1, borderColor: 'divider' }} />}>
            {!hasNamedDefault
              ? renderRow(
                  'builtin',
                  'Default',
                  legacyBaseUrlQuery.data ?? 'acestream://',
                  true,
                  <Tooltip title="Edit the default format">
                    <IconButton size="small" aria-label="Edit default link format" onClick={() => openEditDialog('builtin')} disabled={isMutating}>
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
                      Make default
                    </Button>
                  ) : null}
                  <IconButton size="small" aria-label={`Edit base URL ${entry.name}`} onClick={() => openEditDialog(entry)} disabled={isMutating}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton size="small" aria-label={`Delete base URL ${entry.name}`} onClick={() => handleDelete(entry)} disabled={isMutating}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </>
              )
            )}
          </Stack>
        )}
        <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
          A format without placeholders is a prefix put before the channel id (like <code>acestream://</code>). A format with{' '}
          <code>{'{channel_id}'}</code> is a template and may also use <code>{'{pid}'}</code>, for example{' '}
          <code>{'http://127.0.0.1:6878/ace/getstream?id={channel_id}&pid={pid}'}</code>.
        </Typography>
      </Stack>

      <Dialog open={addOpen} onClose={() => setAddOpen(false)} fullWidth maxWidth="sm">
        <form onSubmit={handleAddSubmit}>
          <DialogTitle>Add link format</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField label="Name" fullWidth value={newName} onChange={(e) => setNewName(e.target.value)} helperText="A short label, e.g. VLC or Ace player" />
              <TextField
                label="Pattern"
                fullWidth
                value={newPattern}
                onChange={(e) => setNewPattern(e.target.value)}
                helperText={'A prefix like acestream://, or a template using {channel_id} and optionally {pid}'}
              />
              <FormControlLabel control={<Checkbox checked={newIsDefault} onChange={(e) => setNewIsDefault(e.target.checked)} />} label="Set as default" />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAddOpen(false)} color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained" color="primary" disabled={!newName.trim() || !newPattern.trim() || createBaseUrlMutation.isPending}>
              {createBaseUrlMutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Add base URL'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      <Dialog open={Boolean(editingEntry)} onClose={closeEditDialog} fullWidth maxWidth="sm">
        <form onSubmit={handleEditSave}>
          <DialogTitle>{editingEntry === 'builtin' ? 'Edit default link format' : 'Edit link format'}</DialogTitle>
          <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
              {editingEntry !== 'builtin' ? <TextField label="Name" fullWidth value={editName} onChange={(e) => setEditName(e.target.value)} /> : null}
              <TextField
                label="Pattern"
                fullWidth
                value={editPattern}
                onChange={(e) => setEditPattern(e.target.value)}
                helperText={'A prefix like acestream://, or a template using {channel_id} and optionally {pid}'}
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeEditDialog} color="inherit">
              Cancel
            </Button>
            <Button type="submit" variant="contained" color="primary" disabled={!editPattern.trim() || (editingEntry !== 'builtin' && !editName.trim()) || isMutating}>
              Save changes
            </Button>
          </DialogActions>
        </form>
      </Dialog>
      {confirmDialog}
    </ContentSection>
  );
};


export default StreamLinkFormatsSection;

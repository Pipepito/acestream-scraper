import React, { useState } from 'react';
import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Typography, useMediaQuery, useTheme } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import TVChannelLinkField from '../TVChannelLinkField';
import { searchService, type SearchResultItem } from '../../services/searchService';
import { normalizeApiError } from '../../services/apiErrors';

interface AddAndLinkDialogProps {
  stream: SearchResultItem;
  onClose: () => void;
  onAdded: () => void;
}

export default function AddAndLinkDialog({ stream, onClose, onAdded }: AddAndLinkDialogProps) {
  const [target, setTarget] = useState<number | null>(null);
  const client = useQueryClient();
  const fullScreen = useMediaQuery(useTheme().breakpoints.down('sm'));
  const save = useMutation({ mutationFn: async () => {
    if (!target) throw new Error('Choose a TV channel.');
    const result = await searchService.importResults([stream], target);
    const outcome = result.items[0];
    if (!outcome || !['added', 'existing'].includes(outcome.outcome)) {
      throw new Error(outcome?.outcome === 'excluded' ? 'This stream matches an import exclusion. Review the rules in Scraper → Exclusions.' : 'Could not resolve this stream. Nothing was linked. Try again when the engine is available.');
    }
  }, onSuccess: () => {
    for (const key of ['acestream-channels', 'tvChannels', 'tvChannel', 'tvChannelAcestreams']) void client.invalidateQueries({ queryKey: [key] });
    onAdded();
  } });
  return <Dialog open fullWidth maxWidth="sm" fullScreen={fullScreen} onClose={save.isPending ? undefined : onClose} aria-labelledby="add-link-title">
    <DialogTitle id="add-link-title">Add and Link</DialogTitle>
    <DialogContent><Stack spacing={2} sx={{ pt: 1 }}>
      <Typography sx={{ overflowWrap: 'anywhere' }}>{stream.name}</Typography>
      <TVChannelLinkField value={target} onChange={setTarget} required disabled={save.isPending} />
      <Typography variant="body2" color="text.secondary">Add this stream directly to a TV channel. An existing link to another channel will be preserved.</Typography>
      {save.isError ? <Alert severity="error">{normalizeApiError(save.error).message}</Alert> : null}
    </Stack></DialogContent>
    <DialogActions><Button disabled={save.isPending} onClick={onClose}>Cancel</Button><Button variant="contained" disabled={!target || save.isPending} onClick={() => save.mutate()}>{save.isPending ? 'Adding and linking…' : 'Add and Link'}</Button></DialogActions>
  </Dialog>;
}

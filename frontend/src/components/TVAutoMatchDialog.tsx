import React, { useMemo, useState } from 'react';
import { Alert, Box, Button, Checkbox, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TablePagination, Typography, useMediaQuery, useTheme } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { tvChannelService, TVMatchPreview } from '../services/tvChannelService';
import { normalizeApiError } from '../services/apiErrors';

interface TVAutoMatchDialogProps {
  onClose: () => void;
}

export default function TVAutoMatchDialog({ onClose }: TVAutoMatchDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const queryClient = useQueryClient();
  const [preview, setPreview] = useState<TVMatchPreview | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(0);
  const analyze = useMutation({
    mutationFn: tvChannelService.previewAutoMatch,
    onSuccess: (result) => {
      setPreview(result);
      setSelected(new Set(result.candidates.filter((item) => item.recommended).map((item) => item.acestream_channel_id)));
      setPage(0);
      apply.reset();
    },
  });
  const apply = useMutation({
    mutationFn: tvChannelService.applyAutoMatch,
    onSuccess: () => {
      setPreview(null);
      setSelected(new Set());
      void queryClient.invalidateQueries({ queryKey: ['tvChannels'] });
      for (const key of ['tvChannel', 'tvChannelAcestreams', 'acestream-channels', 'acestream-channel']) {
        void queryClient.invalidateQueries({ queryKey: [key] });
      }
    },
  });
  const rows = useMemo(() => preview?.candidates.slice(page * 25, (page + 1) * 25) ?? [], [preview, page]);
  const busy = analyze.isPending || apply.isPending;
  const error = analyze.error || apply.error;
  return (
    <Dialog open onClose={busy ? undefined : onClose} fullScreen={fullScreen} fullWidth maxWidth="md" aria-labelledby="tv-automatch-title">
      <DialogTitle id="tv-automatch-title">Auto-match streams</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Typography>Find streams for all TV channels. Existing assignments are preserved. Review the suggestions before assigning.</Typography>
          <Button variant="outlined" disabled={busy} onClick={() => analyze.mutate()}>{preview ? 'Analyze again' : 'Find matches'}</Button>
          {busy ? <CircularProgress size={24} aria-label={analyze.isPending ? 'Finding matches' : 'Assigning streams'} /> : null}
          {error ? <Alert severity="error">{normalizeApiError(error).message}</Alert> : null}
          {apply.data ? <Alert severity="success">{apply.data.assigned_count} streams assigned. {apply.data.skipped_count} skipped because they changed or were already assigned.</Alert> : null}
          {preview ? <>
            <Typography role="status">{preview.candidates.length} suggestions from {preview.unassigned_streams} unassigned streams across {preview.tv_channels} TV channels. {preview.ambiguous_streams} ambiguous; {preview.unmatched_streams} without a match.</Typography>
            <Alert severity="info">Country differences and similar names need review and are not selected automatically. Ambiguous matches are left for manual assignment.</Alert>
            {preview.candidates.length === 0 ? <Alert severity="info">No matches found. You can assign streams from a TV channel’s detail page.</Alert> : <>
              <Stack direction="row" spacing={1}>
                <Button disabled={busy} onClick={() => setSelected(new Set(preview.candidates.filter((item) => item.recommended).map((item) => item.acestream_channel_id)))}>Select recommended</Button>
                <Button disabled={busy} onClick={() => setSelected(new Set())}>Clear selection</Button>
              </Stack>
              {rows.map((item) => <Box key={item.acestream_channel_id} sx={{ borderBottom: 1, borderColor: 'divider', pb: 1, overflowWrap: 'anywhere' }}>
                <FormControlLabel sx={{ alignItems: 'flex-start', m: 0 }} control={<Checkbox disabled={busy} checked={selected.has(item.acestream_channel_id)} onChange={(_, checked) => setSelected((current) => {
                  const next = new Set(current);
                  if (checked) next.add(item.acestream_channel_id); else next.delete(item.acestream_channel_id);
                  return next;
                })} />} label={<Box sx={{ pt: 1 }}>
                  <Typography>{item.acestream_name} → {item.tv_channel_name}</Typography>
                  <Typography variant="body2" color="text.secondary">{item.reason} · {Math.round(item.score * 100)}% match score</Typography>
                  <Typography variant="caption" color="text.secondary">{item.acestream_channel_id}</Typography>
                </Box>} />
              </Box>)}
              <TablePagination component="div" count={preview.candidates.length} page={page} rowsPerPage={25} rowsPerPageOptions={[25]} onPageChange={(_, next) => setPage(next)} />
            </>}
          </> : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button disabled={busy} onClick={onClose}>Close</Button>
        <Button variant="contained" disabled={busy || !selected.size || !preview} onClick={() => apply.mutate({ assignments: (preview?.candidates ?? []).filter((item) => selected.has(item.acestream_channel_id)).map((item) => ({ acestream_channel_id: item.acestream_channel_id, tv_channel_id: item.tv_channel_id })) })}>Assign selected ({selected.size})</Button>
      </DialogActions>
    </Dialog>
  );
}

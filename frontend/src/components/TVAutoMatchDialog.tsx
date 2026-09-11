import React, { useMemo, useState } from 'react';
import { Alert, Box, Button, Checkbox, CircularProgress, Collapse, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, Stack, TablePagination, TextField, MenuItem, Typography, useMediaQuery, useTheme } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { tvChannelService, TVMatchPreview, TVMatchOptions } from '../services/tvChannelService';
import { normalizeApiError } from '../services/apiErrors';

const COUNTRY_OPTIONS: Array<{ value: NonNullable<TVMatchOptions['assumed_country']>; label: string }> = [
  { value: 'ES', label: 'Spain' }, { value: 'PT', label: 'Portugal' },
  { value: 'FR', label: 'France' }, { value: 'DE', label: 'Germany' },
  { value: 'IT', label: 'Italy' }, { value: 'GB', label: 'United Kingdom' },
  { value: 'US', label: 'United States' }, { value: 'NL', label: 'Netherlands' },
  { value: 'PL', label: 'Poland' }, { value: 'TR', label: 'Türkiye' },
  { value: 'BE', label: 'Belgium' }, { value: 'AR', label: 'Argentina' },
  { value: 'RU', label: 'Russia' },
];

interface StationMatches {
  id: number;
  name: string;
  streams: TVMatchPreview['candidates'];
}

interface TVAutoMatchDialogProps {
  onClose: () => void;
}

export default function TVAutoMatchDialog({ onClose }: TVAutoMatchDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const queryClient = useQueryClient();
  const [assumedCountry, setAssumedCountry] = useState<NonNullable<TVMatchOptions['assumed_country']> | ''>('');
  const [preview, setPreview] = useState<TVMatchPreview | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const analyze = useMutation({
    mutationFn: tvChannelService.previewAutoMatch,
    onSuccess: (result) => {
      setPreview(result);
      setSelected(new Set());
      setExpanded(new Set());
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
  const stations = useMemo(() => {
    const groups = new Map<number, StationMatches>();
    for (const item of preview?.candidates ?? []) {
      const group = groups.get(item.tv_channel_id) ?? { id: item.tv_channel_id, name: item.tv_channel_name, streams: [] };
      group.streams.push(item);
      groups.set(group.id, group);
    }
    return Array.from(groups.values());
  }, [preview]);
  const rows = stations.slice(page * 10, (page + 1) * 10);
  const toggleStreams = (ids: string[], checked: boolean) => setSelected((current) => {
    const next = new Set(current);
    for (const id of ids) {
      if (checked) next.add(id); else next.delete(id);
    }
    return next;
  });
  const busy = analyze.isPending || apply.isPending;
  const error = analyze.error || apply.error;
  return (
    <Dialog open onClose={busy ? undefined : onClose} fullScreen={fullScreen} fullWidth maxWidth="md" aria-labelledby="tv-automatch-title">
      <DialogTitle id="tv-automatch-title">Auto-match streams</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <Typography>Find streams for all TV channels. Existing assignments are preserved. Review the suggestions before assigning.</Typography>
          <TextField select label="Assume country for unlabelled channels" value={assumedCountry} disabled={busy} helperText="Applies to streams and TV channels without a country. Explicit country labels take precedence. Stored channel data is unchanged." onChange={(event) => {
            const country = COUNTRY_OPTIONS.find((option) => option.value === event.target.value)?.value ?? '';
            setAssumedCountry(country);
            setPreview(null);
            setSelected(new Set());
            setExpanded(new Set());
            setPage(0);
            analyze.reset();
            apply.reset();
          }}>
            <MenuItem value="">No assumption</MenuItem>
            {COUNTRY_OPTIONS.map((option) => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
          </TextField>
          <Button variant="outlined" disabled={busy} onClick={() => analyze.mutate({ assumed_country: assumedCountry || null })}>{preview ? 'Analyze again' : 'Find matches'}</Button>
          {busy ? <CircularProgress size={24} aria-label={analyze.isPending ? 'Finding matches' : 'Assigning streams'} /> : null}
          {error ? <Alert severity="error">{normalizeApiError(error).message}</Alert> : null}
          {apply.data ? <Alert severity="success">{apply.data.assigned_count} streams assigned. {apply.data.skipped_count} skipped because they changed or were already assigned.</Alert> : null}
          {preview ? <>
            <Typography role="status">{stations.length} TV channels with {preview.candidates.length} matching stream IDs. Checked {preview.tv_channels} TV channels and {preview.unassigned_streams} unassigned streams. {preview.ambiguous_streams} ambiguous; {preview.unmatched_streams} without a match.</Typography>
            <Alert severity="info">Only exact station identities are shown. Uncertain names, editions and conflicting metadata are discarded. Select the stations or individual streams to assign.</Alert>
            {preview.candidates.length === 0 ? <Alert severity="info">No matches found. You can assign streams from a TV channel’s detail page.</Alert> : <>
              <Button disabled={busy || !selected.size} onClick={() => setSelected(new Set())}>Clear selection</Button>
              {rows.map((station) => {
                const selectedCount = station.streams.filter((item) => selected.has(item.acestream_channel_id)).length;
                const open = expanded.has(station.id);
                return <Box key={station.id} sx={{ borderBottom: 1, borderColor: 'divider', pb: 1, overflowWrap: 'anywhere' }}>
                  <FormControlLabel control={<Checkbox disabled={busy} checked={selectedCount === station.streams.length} indeterminate={selectedCount > 0 && selectedCount < station.streams.length} onChange={(_, checked) => toggleStreams(station.streams.map((item) => item.acestream_channel_id), checked)} />} label={`${station.name} · ${station.streams.length} stream ${station.streams.length === 1 ? 'ID' : 'IDs'}`} />
                  <Button aria-expanded={open} aria-controls={`station-streams-${station.id}`} onClick={() => setExpanded((current) => {
                    const next = new Set(current);
                    if (open) next.delete(station.id); else next.add(station.id);
                    return next;
                  })}>{open ? 'Hide' : 'Review'} streams for {station.name}</Button>
                  <Collapse in={open} unmountOnExit id={`station-streams-${station.id}`}>
                    {station.streams.map((item) => <Box key={item.acestream_channel_id} sx={{ pl: 2 }}>
                      <FormControlLabel sx={{ alignItems: 'flex-start', m: 0 }} control={<Checkbox disabled={busy} checked={selected.has(item.acestream_channel_id)} onChange={(_, checked) => toggleStreams([item.acestream_channel_id], checked)} />} label={<Box sx={{ pt: 1 }}>
                        <Typography>{item.acestream_name}</Typography>
                        <Typography variant="body2" color="text.secondary">{item.reason}</Typography>
                        <Typography variant="caption" color="text.secondary">{item.acestream_channel_id}</Typography>
                      </Box>} />
                    </Box>)}
                  </Collapse>
                </Box>;
              })}
              <TablePagination component="div" count={stations.length} page={page} rowsPerPage={10} rowsPerPageOptions={[10]} labelDisplayedRows={({ from, to, count }) => `${from}–${to} of ${count} TV channels`} onPageChange={(_, next) => setPage(next)} />
            </>}
          </> : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button disabled={busy} onClick={onClose}>Close</Button>
        <Button variant="contained" disabled={busy || !selected.size || !preview} onClick={() => apply.mutate({ assumed_country: assumedCountry || null, assignments: (preview?.candidates ?? []).filter((item) => selected.has(item.acestream_channel_id)).map((item) => ({ acestream_channel_id: item.acestream_channel_id, tv_channel_id: item.tv_channel_id })) })}>Assign selected ({selected.size})</Button>
      </DialogActions>
    </Dialog>
  );
}

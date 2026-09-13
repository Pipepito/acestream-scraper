import React, { useEffect, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Autocomplete, TextField, Typography, Box, Alert, createFilterOptions } from '@mui/material';
import type { TVChannel } from '../types/tvChannelTypes';

interface AssignTVChannelDialogProps {
  open: boolean;
  onClose: () => void;
  tvChannels?: TVChannel[];
  onAssign: (tvChannelId: number) => void;
  loading?: boolean;
  error?: string | null;
  catalogLoading?: boolean;
  catalogError?: string | null;
  onRetry?: () => void;
}

const label = (channel: TVChannel) => `${channel.channel_number != null ? `${channel.channel_number} · ` : ''}${channel.name}`;
const filterOptions = createFilterOptions<TVChannel>({ stringify: (channel) => `${label(channel)} ${channel.category ?? ''}` });

export default function AssignTVChannelDialog({ open, onClose, tvChannels = [], onAssign, loading, error, catalogLoading, catalogError, onRetry }: AssignTVChannelDialogProps) {
  const [selected, setSelected] = useState<TVChannel | null>(null);
  useEffect(() => { if (open) setSelected(null); }, [open]);
  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Assign to TV Channel</DialogTitle>
      <DialogContent>
        <Autocomplete
          sx={{ mt: 1 }}
          options={tvChannels}
          value={selected}
          onChange={(_, channel) => setSelected(channel)}
          getOptionLabel={label}
          isOptionEqualToValue={(option, value) => option.id === value.id}
          filterOptions={filterOptions}
          loading={catalogLoading}
          disabled={loading || Boolean(catalogError)}
          noOptionsText={tvChannels.length ? 'No matching TV channels' : 'No TV channels yet. Create one in TV Channels.'}
          renderOption={(props, channel) => (
            <li {...props} key={channel.id}>
              <Box><Typography>{label(channel)}</Typography><Typography variant="body2" color="text.secondary">{channel.category || 'No category'}</Typography></Box>
            </li>
          )}
          renderInput={(params) => <TextField {...params} label="TV Channel" helperText="Search by name, channel number or category." />}
        />
        {catalogError && <Alert severity="error" sx={{ mt: 2 }} action={<Button onClick={onRetry}>Retry</Button>}>{catalogError}</Alert>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button onClick={() => selected && onAssign(selected.id)} disabled={loading || catalogLoading || Boolean(catalogError) || !tvChannels.some(channel => channel.id === selected?.id)} variant="contained">
          {loading ? 'Assigning…' : 'Assign'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

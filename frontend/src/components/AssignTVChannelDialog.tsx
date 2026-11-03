import React, { useEffect, useMemo, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Autocomplete, TextField, Typography, Box, Alert, createFilterOptions } from '@mui/material';
import type { TVChannel } from '../types/tvChannelTypes';

/** What the user picked: an existing TV channel, or a new one named after the thing being assigned. */
export type AssignChoice = { tvChannelId: number } | { createName: string };

type AssignOption = { kind: 'existing'; channel: TVChannel } | { kind: 'create'; name: string };

interface AssignTVChannelDialogProps {
  open: boolean;
  onClose: () => void;
  tvChannels?: TVChannel[];
  onAssign: (choice: AssignChoice) => void;
  loading?: boolean;
  error?: string | null;
  catalogLoading?: boolean;
  catalogError?: string | null;
  onRetry?: () => void;
  /** Offer "Create TV channel '<name>'" first when no TV channel has this exact name. */
  createName?: string;
}

const label = (channel: TVChannel) => `${channel.channel_number != null ? `${channel.channel_number} · ` : ''}${channel.name}`;
const optionLabel = (option: AssignOption) => option.kind === 'create' ? `Create TV channel '${option.name}'` : label(option.channel);
const filterOptions = createFilterOptions<AssignOption>({ stringify: (option) => option.kind === 'create' ? option.name : `${label(option.channel)} ${option.channel.category ?? ''}` });

export default function AssignTVChannelDialog({ open, onClose, tvChannels = [], onAssign, loading, error, catalogLoading, catalogError, onRetry, createName }: AssignTVChannelDialogProps) {
  const [selected, setSelected] = useState<AssignOption | null>(null);
  useEffect(() => { if (open) setSelected(null); }, [open]);
  const options = useMemo<AssignOption[]>(() => {
    const existing: AssignOption[] = tvChannels.map((channel) => ({ kind: 'existing', channel }));
    const name = createName?.trim();
    if (name && !tvChannels.some((channel) => channel.name.toLocaleLowerCase() === name.toLocaleLowerCase())) return [{ kind: 'create', name }, ...existing];
    return existing;
  }, [tvChannels, createName]);
  const valid = selected !== null && (selected.kind === 'create' || tvChannels.some((channel) => channel.id === selected.channel.id));
  return (
    <Dialog open={open} onClose={loading ? undefined : onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Assign to TV Channel</DialogTitle>
      <DialogContent>
        <Autocomplete
          sx={{ mt: 1 }}
          options={options}
          value={selected}
          onChange={(_, option) => setSelected(option)}
          getOptionLabel={optionLabel}
          isOptionEqualToValue={(option, value) => optionLabel(option) === optionLabel(value)}
          filterOptions={filterOptions}
          loading={catalogLoading}
          disabled={loading || Boolean(catalogError)}
          noOptionsText={tvChannels.length ? 'No matching TV channels' : 'No TV channels yet. Create one in TV Channels.'}
          renderOption={(props, option) => (
            <li {...props} key={optionLabel(option)}>
              <Box><Typography>{optionLabel(option)}</Typography><Typography variant="body2" color="text.secondary">{option.kind === 'create' ? 'New TV channel' : option.channel.category || 'No category'}</Typography></Box>
            </li>
          )}
          renderInput={(params) => <TextField {...params} label="TV Channel" helperText="Search by name, channel number or category." />}
        />
        {catalogError && <Alert severity="error" sx={{ mt: 2 }} action={<Button onClick={onRetry}>Retry</Button>}>{catalogError}</Alert>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button onClick={() => { if (selected?.kind === 'create') onAssign({ createName: selected.name }); else if (selected) onAssign({ tvChannelId: selected.channel.id }); }}
          disabled={loading || catalogLoading || Boolean(catalogError) || !valid} variant="contained">
          {loading ? 'Assigning…' : 'Assign'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

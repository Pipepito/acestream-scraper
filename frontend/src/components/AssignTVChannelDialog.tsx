import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
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
  const tUi = useUiText();
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
      <DialogTitle>{tUi("Assign to TV Channel")}</DialogTitle>
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
          noOptionsText={tvChannels.length ? uiText("No matching TV channels") : uiText("No TV channels yet. Create one in TV Channels.")}
          renderOption={(props, option) => (
            <li {...props} key={optionLabel(option)}>
              <Box><Typography>{optionLabel(option)}</Typography><Typography variant="body2" color="text.secondary">{option.kind === 'create' ? tUi("New TV channel") : option.channel.category || 'No category'}</Typography></Box>
            </li>
          )}
          renderInput={(params) => <TextField {...params} label={tUi("TV Channel")} helperText={tUi("Search by name, channel number or category.")} />}
        />
        {catalogError && <Alert severity="error" sx={{ mt: 2 }} action={<Button onClick={onRetry}>{tUi("Retry")}</Button>}>{catalogError}</Alert>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>{tUi("Cancel")}</Button>
        <Button onClick={() => { if (selected?.kind === 'create') onAssign({ createName: selected.name }); else if (selected) onAssign({ tvChannelId: selected.channel.id }); }}
          disabled={loading || catalogLoading || Boolean(catalogError) || !valid} variant="contained">
          {loading ? tUi("Assigning…") : tUi("Assign")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

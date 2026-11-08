import { useUiText } from '../i18n/useUiText';
import React from 'react';
import { Alert, Autocomplete, Button, Stack, TextField, Typography, createFilterOptions } from '@mui/material';
import { useTVChannelCatalog } from '../hooks/useTVChannels';
import type { TVChannel } from '../types/tvChannelTypes';

interface TVChannelLinkFieldProps {
  value: number | null;
  onChange: (value: number | null) => void;
  disabled?: boolean;
  required?: boolean;
}

const filterOptions = createFilterOptions<TVChannel>({ stringify: channel => `${channel.name} ${channel.channel_number ?? ''} ${channel.country ?? ''} ${channel.category ?? ''}` });

export default function TVChannelLinkField({ value, onChange, disabled, required }: TVChannelLinkFieldProps) {
  const tUi = useUiText();
  const catalog = useTVChannelCatalog();
  const channels = catalog.data ?? [];
  return <Stack spacing={1}>
    <Autocomplete options={channels} value={channels.find(channel => channel.id === value) ?? null}
      onChange={(_, channel) => onChange(channel?.id ?? null)} disabled={disabled || catalog.isError}
      loading={catalog.isLoading} filterOptions={filterOptions} isOptionEqualToValue={(a, b) => a.id === b.id}
      getOptionLabel={channel => `${channel.channel_number == null ? '' : `${channel.channel_number} · `}${channel.name}`}
      noOptionsText="No matching TV channels. Create one in TV Channels."
      renderOption={(props, channel) => <li {...props} key={channel.id}><Stack><Typography>{channel.channel_number == null ? '' : tUi("{{value0}} · ", { value0: channel.channel_number })}{channel.name}</Typography><Typography variant="caption" color="text.secondary">{[channel.country, channel.category, !channel.is_active ? tUi("Hidden channel") : ''].filter(Boolean).join(' · ')}</Typography></Stack></li>}
      renderInput={params => <TextField {...params} label={required ? tUi("TV channel") : tUi("Link to TV channel (optional)")} required={required} helperText={tUi("Search by name, number, country or category.")} />} />
    {catalog.isError ? <Alert severity="error" action={<Button onClick={() => void catalog.refetch()}>{tUi("Retry")}</Button>}>{tUi("Could not load TV channels.")}</Alert> : null}
  </Stack>;
}

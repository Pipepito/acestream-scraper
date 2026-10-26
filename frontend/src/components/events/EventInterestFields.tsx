import React from 'react';
import { Autocomplete, Stack, TextField, Typography } from '@mui/material';
import type { EventInterests } from '../../services/eventService';

export const emptyInterests: EventInterests = { sports: [], competitions: [], teams: [] };
interface Props { value: EventInterests; onChange: (value: EventInterests) => void; choices?: EventInterests; disabled?: boolean; prefix?: string }
export default function EventInterestFields({ value, onChange, choices, disabled, prefix = '' }: Props) {
  return <Stack spacing={1.5}>
    <Typography variant="body2" color="text.secondary">Include any selected sport, competition or team. Leave all empty for everything. You can type a name and press Enter.</Typography>
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
      {(['sports', 'competitions', 'teams'] as const).map((key) => <Autocomplete key={key} multiple freeSolo fullWidth disabled={disabled}
        options={choices?.[key] ?? []} value={value[key] ?? []} onChange={(_, names) => onChange({ ...value, [key]: names })}
        renderInput={(params) => <TextField {...params} label={prefix + { sports: 'Sports', competitions: 'Competitions', teams: 'Teams' }[key]} />}
      />)}
    </Stack>
  </Stack>;
}

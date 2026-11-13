import React from 'react';
import { Autocomplete, Stack, TextField, Typography, createFilterOptions } from '@mui/material';
import type { EventInterests } from '../../services/eventService';

export const emptyInterests: EventInterests = { sports: [], competitions: [], teams: [] };

const KEYS = ['sports', 'competitions', 'teams'] as const;
const LABELS = { sports: 'Sports', competitions: 'Competitions', teams: 'Teams' };
// A provider can publish thousands of teams: render the first matches and let typing narrow them.
const MAX_LISTED = 100;
const filterNames = createFilterOptions<string>({ limit: MAX_LISTED });

interface Props {
  value: EventInterests;
  onChange: (value: EventInterests) => void;
  /** Names to choose from. A filter only matches a name spelled exactly as its source spells it. */
  choices?: EventInterests;
  /** The choices are being fetched. */
  loading?: boolean;
  /** A list was opened: the caller can fetch its choices now. */
  onOpen?: () => void;
  /** Only where names cannot be known beforehand (a schedule URL not fetched yet). */
  allowCustom?: boolean;
  disabled?: boolean;
  prefix?: string;
  emptyHint?: string;
}

export default function EventInterestFields({ value, onChange, choices, loading = false, onOpen, allowCustom = false, disabled, prefix = '', emptyHint = 'Leave all empty for everything.' }: Props) {
  return <Stack spacing={1.5}>
    <Typography variant="body2" color="text.secondary">Include any selected sport, competition or team. {emptyHint} {allowCustom
      ? 'Type each name exactly as the schedule spells it and press Enter.'
      : 'Choose from each list; type to find a name.'}</Typography>
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
      {KEYS.map((key) => {
        const selected = value[key] ?? [];
        const offered = choices?.[key] ?? [];
        // Names chosen earlier stay listed, even when the source does not publish them right now.
        const options = [...offered, ...selected.filter((name) => !offered.includes(name))];
        return <Autocomplete key={key} multiple fullWidth disabled={disabled} freeSolo={allowCustom}
          options={options} value={selected} filterSelectedOptions filterOptions={filterNames}
          loading={loading} loadingText="Loading names…" onOpen={onOpen}
          noOptionsText={offered.length ? 'No matching name' : 'No names to choose from yet'}
          onChange={(_, names) => onChange({ ...value, [key]: names })}
          renderInput={(params) => <TextField {...params} label={prefix + LABELS[key]} />}
        />;
      })}
    </Stack>
  </Stack>;
}

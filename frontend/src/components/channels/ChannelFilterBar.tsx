import React, { useEffect, useState } from 'react';
import { Box, Button, FormControl, InputLabel, MenuItem, Select, TextField } from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import type { AcestreamChannelFilters } from '../../services/channelService';

export interface ChannelFilterBarProps {
  filters: AcestreamChannelFilters;
  groups: string[];
  onChange: (filters: AcestreamChannelFilters) => void;
}

const SEARCH_DEBOUNCE_MS = 300;

type TriState = '' | 'true' | 'false';

const toTriState = (value: boolean | undefined): TriState => (value === undefined ? '' : value ? 'true' : 'false');
const fromTriState = (value: TriState): boolean | undefined => (value === '' ? undefined : value === 'true');

/** Filters honoured by the channel list API: text search, group, online state and playlist visibility. */
const ChannelFilterBar: React.FC<ChannelFilterBarProps> = ({ filters, groups, onChange }) => {
  const [search, setSearch] = useState(filters.search ?? '');

  useEffect(() => {
    setSearch(filters.search ?? '');
  }, [filters.search]);

  useEffect(() => {
    const trimmed = search.trim();
    if (trimmed === (filters.search ?? '')) return undefined;
    const timer = window.setTimeout(() => {
      onChange({ ...filters, search: trimmed || undefined });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [search, filters, onChange]);

  const hasFilters = Boolean(filters.search || filters.group || filters.is_online !== undefined || filters.is_active !== undefined);

  const handleGroup = (event: SelectChangeEvent<string>) => {
    onChange({ ...filters, group: event.target.value || undefined });
  };
  const handleOnline = (event: SelectChangeEvent<TriState>) => {
    onChange({ ...filters, is_online: fromTriState(event.target.value as TriState) });
  };
  const handleVisibility = (event: SelectChangeEvent<TriState>) => {
    onChange({ ...filters, is_active: fromTriState(event.target.value as TriState) });
  };

  return (
    <Box
      role="search"
      aria-label="Channel filters"
      sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, alignItems: 'center', mb: 2 }}
    >
      <TextField
        size="small"
        label="Search"
        placeholder="Name or ID"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        sx={{ minWidth: { xs: '100%', sm: 220 }, flex: { sm: 1 }, maxWidth: 360 }}
      />
      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel id="channel-filter-group">Group</InputLabel>
        <Select labelId="channel-filter-group" label="Group" value={filters.group ?? ''} onChange={handleGroup}>
          <MenuItem value="">Any group</MenuItem>
          {groups.map((group) => (
            <MenuItem key={group} value={group}>
              {group}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 130 }}>
        <InputLabel id="channel-filter-online">Online</InputLabel>
        <Select labelId="channel-filter-online" label="Online" value={toTriState(filters.is_online)} onChange={handleOnline}>
          <MenuItem value="">Any</MenuItem>
          <MenuItem value="true">Online</MenuItem>
          <MenuItem value="false">Offline</MenuItem>
        </Select>
      </FormControl>
      <FormControl size="small" sx={{ minWidth: 150 }}>
        <InputLabel id="channel-filter-visibility">Playlist</InputLabel>
        <Select labelId="channel-filter-visibility" label="Playlist" value={toTriState(filters.is_active)} onChange={handleVisibility}>
          <MenuItem value="">All channels</MenuItem>
          <MenuItem value="true">In playlist</MenuItem>
          <MenuItem value="false">Hidden</MenuItem>
        </Select>
      </FormControl>
      {hasFilters ? (
        <Button size="small" onClick={() => onChange({})}>
          Reset filters
        </Button>
      ) : null}
    </Box>
  );
};

export default ChannelFilterBar;

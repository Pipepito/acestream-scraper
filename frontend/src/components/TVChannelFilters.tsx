import React, { useId, useState } from 'react';
import { Button, Collapse, MenuItem, Stack, TextField } from '@mui/material';
import { TVChannel } from '../types/tvChannelTypes';

export type TVFilters = Record<string, string>;
export function matchesTVFilters(channel: TVChannel, filters: TVFilters): boolean {
  const streams = channel.acestream_channels ?? [];
  const mapped = Boolean(channel.epg_id && channel.epg_source_id);
  return Object.entries(filters).every(([key, value]) => {
    if (!value) return true;
    if (key === 'search') return [channel.name, channel.description, channel.channel_number, channel.epg_id, ...streams.flatMap(s => [s.name, s.id])].some(v => String(v ?? '').toLowerCase().includes(value.trim().toLowerCase()));
    if (['category', 'country', 'language'].includes(key)) return channel[key as 'category' | 'country' | 'language'] === value;
    if (key === 'is_active' || key === 'is_favorite') return channel[key] === (value === 'true');
    if (key === 'epg') return mapped === (value === 'yes');
    if (key === 'epg_source_id') return String(channel.epg_source_id ?? '') === value;
    if (key === 'streams') return value === 'none' ? streams.length === 0 : value === 'multiple' ? streams.length > 1 : streams.length > 0;
    if (key === 'signal') return value === 'verified' ? streams.some(s => s.is_online === true) : value === 'unverified' ? streams.length > 0 && !streams.some(s => s.is_online === true) : streams.length > 0 && streams.every(s => s.is_online == null);
    if (key === 'number') return (channel.channel_number != null) === (value === 'yes');
    if (key === 'min_number') return channel.channel_number != null && channel.channel_number >= Number(value);
    if (key === 'max_number') return channel.channel_number != null && channel.channel_number <= Number(value);
    if (key === 'min_streams') return streams.length >= Number(value);
    if (key === 'max_streams') return streams.length <= Number(value);
    if (['logo_url', 'website', 'description'].includes(key)) return Boolean(channel[key as 'logo_url' | 'website' | 'description']?.trim()) === (value === 'yes');
    return true;
  });
}

export default function TVChannelFilters({ channels, filters, onChange }: { channels: TVChannel[]; filters: TVFilters; onChange: (filters: TVFilters) => void }) {
  const [advanced, setAdvanced] = useState(false);
  const advancedId = useId();
  const advancedCount = Object.entries(filters).filter(([key, value]) => value && !['search', 'category', 'is_active'].includes(key)).length;
  const change = (key: string, value: string) => onChange({ ...filters, [key]: value });
  const presence = [['yes', 'Present'], ['no', 'Missing']];
  const select = (key: string, label: string, options: string[][]) => <TextField key={key} select size="small" label={label} value={filters[key] ?? ''} onChange={e => change(key, e.target.value)}>
    <MenuItem value="">All</MenuItem>{options.map(([value, text]) => <MenuItem key={value} value={value}>{text}</MenuItem>)}
  </TextField>;
  return <Stack component="form" aria-label="Channel filters" onSubmit={e => e.preventDefault()} spacing={2}>
    <TextField fullWidth size="small" label="Search" placeholder="Name, number, description, EPG ID or stream" value={filters.search ?? ''} onChange={e => change('search', e.target.value)} />
    <Stack component="fieldset" sx={{ border: 0, p: 0, m: 0, display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', lg: 'repeat(4, minmax(0, 1fr))' }, gap: 2 }}>
      {(['category'] as const).map(key => select(key, key[0].toUpperCase() + key.slice(1), Array.from(new Set(channels.map(c => c[key]).filter((v): v is string => Boolean(v)))).sort().map(v => [v, v])))}
      {select('is_active', 'Status', [['true', 'Active'], ['false', 'Inactive']])}
    </Stack>
    <Button sx={{ alignSelf: 'flex-start' }} aria-expanded={advanced} aria-controls={advancedId} onClick={() => setAdvanced(value => !value)}>
      Advanced filters{advancedCount ? ` (${advancedCount} active)` : ''}
    </Button>
    <Collapse in={advanced} id={advancedId} unmountOnExit>
    <Stack sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', lg: 'repeat(4, minmax(0, 1fr))' }, gap: 2, pt: 1 }}>
      {(['country', 'language'] as const).map(key => select(key, key[0].toUpperCase() + key.slice(1), Array.from(new Set(channels.map(c => c[key]).filter((v): v is string => Boolean(v)))).sort().map(v => [v, v])))}
      {select('is_favorite', 'Favorite', [['true', 'Favorites'], ['false', 'Not favorites']])}
      {select('epg', 'EPG mapping', [['yes', 'Mapped'], ['no', 'Not mapped']])}
      {select('epg_source_id', 'EPG source', Array.from(new Set(channels.map(c => c.epg_source_id).filter((v): v is number => v != null))).sort((a,b) => a-b).map(v => [String(v), `Source ${v}`]))}
      {select('streams', 'Attached streams', [['any', 'With streams'], ['none', 'Without streams'], ['multiple', 'Multiple streams']])}
      {select('signal', 'Stream signal', [['verified', 'At least one verified'], ['unverified', 'None verified'], ['unknown', 'All not checked']])}
      {select('number', 'Channel number', presence)}
      {select('logo_url', 'Logo', presence)}
      {select('website', 'Website', presence)}
      {select('description', 'Description', presence)}
      {(['min_number', 'max_number', 'min_streams', 'max_streams'] as const).map((key, i) => <TextField key={key} size="small" type="number" label={['Minimum number', 'Maximum number', 'Minimum streams', 'Maximum streams'][i]} inputProps={{ min: 0, step: 1 }} value={filters[key] ?? ''} onChange={e => change(key, e.target.value)} />)}
    </Stack>
    </Collapse>
    <Button sx={{ alignSelf: 'flex-start' }} onClick={() => onChange({})}>Reset filters</Button>
  </Stack>;
}

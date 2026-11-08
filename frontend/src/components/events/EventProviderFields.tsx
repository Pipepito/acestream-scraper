import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Alert, Autocomplete, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { eventService, type EventProviderOptions } from '../../services/eventService';

interface Props { value: EventProviderOptions; onChange: (value: EventProviderOptions) => void;
  zone: string; onZone: (zone: string) => void; saved: boolean; disabled: boolean }
export default function EventProviderFields({ value, onChange, zone, onZone, saved, disabled }: Props) {
  const tUi = useUiText();
  const catalog = useQuery({ queryKey: ['events', 'providers'], queryFn: eventService.providers, staleTime: Infinity });
  const feeds = catalog.data?.feeds ?? [];
  const competitions = catalog.data?.football_competitions ?? [];
  const leagues = catalog.data?.leagues ?? [];
  return <Stack spacing={2}>
    <TextField select label={tUi("Provider")} value={value.provider} disabled={saved || disabled} onChange={(e) => {
      onChange({ ...value, provider: e.target.value as EventProviderOptions['provider'], interests: {} }); onZone('Europe/Madrid');
    }}>
      <MenuItem value="wosti_es">{tUi("Fútbol en la TV · Spain · multi-sport")}</MenuItem>
      <MenuItem value="openfootball">{tUi("OpenFootball · football fixtures")}</MenuItem>
    </TextField>
    {catalog.isError ? <Alert severity="error" action={<Button onClick={() => void catalog.refetch()}>{tUi("Retry")}</Button>}>{tUi("Could not load provider options.")}</Alert> : null}
    {value.provider === 'wosti_es' ? <>
      <Typography variant="body2">{tUi("Spain is the TV broadcast market. International events remain included. The all-sports guide covers the next few days; add individual sports for longer schedules.")}</Typography>
      <Autocomplete multiple options={feeds} loading={catalog.isFetching} disabled={disabled}
        value={feeds.filter((feed) => value.feeds?.includes(feed.id))} getOptionLabel={(feed) => feed.name}
        isOptionEqualToValue={(a, b) => a.id === b.id}
        onChange={(_, selected) => onChange({ ...value, feeds: selected.map((feed) => feed.id), football_competitions: selected.some((feed) => feed.id === 'football') && !selected.some((feed) => feed.id === 'all') ? value.football_competitions : [] })}
        renderInput={(params) => <TextField {...params} label={tUi("Sports feeds")} helperText={tUi("No API key needed. Times use Europe/Madrid.")} />} />
      {value.feeds?.includes('football') ? <Autocomplete multiple options={competitions} disabled={disabled || value.feeds.includes('all')}
        value={competitions.filter((competition) => value.football_competitions?.includes(competition.id))}
        getOptionLabel={(competition) => competition.name} isOptionEqualToValue={(a, b) => a.id === b.id}
        onChange={(_, selected) => onChange({ ...value, football_competitions: selected.map((competition) => competition.id) })}
        renderInput={(params) => <TextField {...params} label={tUi("Football competitions")}
          helperText={value.feeds?.includes('all') ? tUi("Remove All sports to request only selected football competitions.") : tUi("Choose competitions before fetching. Blank requests all football. Other selected sports are still included.")} />} /> : null}
    </> : <>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField fullWidth select label={tUi("League")} value={value.league} disabled={saved || disabled || !leagues.length} onChange={(e) => {
          onChange({ ...value, league: e.target.value as EventProviderOptions['league'], interests: {} });
          onZone(leagues.find((league) => league.id === e.target.value)?.timezone ?? 'UTC');
        }}>{leagues.map((league) => <MenuItem key={league.id} value={league.id}>{league.name}</MenuItem>)}</TextField>
        <TextField label={tUi("Season")} value={value.season} disabled={saved || disabled} onChange={(e) => onChange({ ...value, season: e.target.value })} helperText={tUi("For example, 2026-27")} />
      </Stack>
      <TextField label={tUi("Source timezone")} value={zone} disabled={disabled} onChange={(e) => onZone(e.target.value)} helperText={tUi("Confirm the timezone used for kickoff times. Date-only fixtures keep their time unknown.")} />
      <Typography variant="body2">{tUi("Free community data, with no TV listings. A season file must exist in OpenFootball; fixtures and kickoff times may be incomplete.")}</Typography>
    </>}
    <TextField select label={tUi("Import window")} value={value.window_days} disabled={disabled} onChange={(e) => onChange({ ...value, window_days: Number(e.target.value) })}>
      {Array.from(new Set([7, 14, 30, value.window_days ?? 14])).sort((a, b) => a - b).map((days) => <MenuItem key={days} value={days}>{tUi("Next")}{' '}{days} {' '}{tUi("days")}</MenuItem>)}
    </TextField>
  </Stack>;
}

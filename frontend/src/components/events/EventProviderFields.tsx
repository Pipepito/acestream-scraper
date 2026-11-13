import React, { useState } from 'react';
import { Alert, Autocomplete, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { eventService, type EventProviderOptions } from '../../services/eventService';
import EventInterestFields, { emptyInterests } from './EventInterestFields';
import { eventErrorMessage } from './eventErrors';

interface Props { value: EventProviderOptions; onChange: (value: EventProviderOptions) => void;
  zone: string; onZone: (zone: string) => void; saved: boolean; disabled: boolean }
export default function EventProviderFields({ value, onChange, zone, onZone, saved, disabled }: Props) {
  const catalog = useQuery({ queryKey: ['events', 'providers'], queryFn: eventService.providers, staleTime: Infinity });
  const feeds = catalog.data?.feeds ?? [];
  const competitions = catalog.data?.football_competitions ?? [];
  const leagues = catalog.data?.leagues ?? [];
  // The names depend on everything but the interests themselves. They are fetched from the
  // provider when a list is first opened, and again only after one of these choices changes.
  const { interests: _chosen, ...request } = value;
  const namesKey = JSON.stringify([request, value.provider === 'openfootball' ? zone : 'Europe/Madrid']);
  const [wantedKey, setWantedKey] = useState('');
  const names = useQuery({ queryKey: ['events', 'provider-interests', namesKey], enabled: wantedKey === namesKey,
    queryFn: () => eventService.providerInterests({ provider_options: { ...request, interests: emptyInterests }, timezone: zone }),
    staleTime: 5 * 60 * 1000, retry: false });
  return <Stack spacing={2}>
    <TextField select label="Provider" value={value.provider} disabled={saved || disabled} onChange={(e) => {
      onChange({ ...value, provider: e.target.value as EventProviderOptions['provider'], interests: {} }); onZone('Europe/Madrid');
    }}>
      <MenuItem value="wosti_es">Fútbol en la TV · Spain · multi-sport</MenuItem>
      <MenuItem value="marca_es">MARCA · Spain · daily sports TV agenda</MenuItem>
      <MenuItem value="openfootball">OpenFootball · football fixtures</MenuItem>
    </TextField>
    {catalog.isError ? <Alert severity="error" action={<Button onClick={() => void catalog.refetch()}>Retry</Button>}>Could not load provider options.</Alert> : null}
    {value.provider === 'wosti_es' ? <>
      <Typography variant="body2">Spain is the TV broadcast market. International events remain included. The all-sports guide covers the next few days; add individual sports for longer schedules.</Typography>
      <Autocomplete multiple options={feeds} loading={catalog.isFetching} disabled={disabled}
        value={feeds.filter((feed) => value.feeds?.includes(feed.id))} getOptionLabel={(feed) => feed.name}
        isOptionEqualToValue={(a, b) => a.id === b.id}
        onChange={(_, selected) => onChange({ ...value, feeds: selected.map((feed) => feed.id), football_competitions: selected.some((feed) => feed.id === 'football') && !selected.some((feed) => feed.id === 'all') ? value.football_competitions : [] })}
        renderInput={(params) => <TextField {...params} label="Sports feeds" helperText="No API key needed. Times use Europe/Madrid." />} />
      {value.feeds?.includes('football') ? <Autocomplete multiple options={competitions} disabled={disabled || value.feeds.includes('all')}
        value={competitions.filter((competition) => value.football_competitions?.includes(competition.id))}
        getOptionLabel={(competition) => competition.name} isOptionEqualToValue={(a, b) => a.id === b.id}
        onChange={(_, selected) => onChange({ ...value, football_competitions: selected.map((competition) => competition.id) })}
        renderInput={(params) => <TextField {...params} label="Football competitions"
          helperText={value.feeds?.includes('all') ? 'Remove All sports to request only selected football competitions.' : 'Choose competitions before fetching. Blank requests all football. Other selected sports are still included.'} />} /> : null}
    </> : value.provider === 'marca_es' ? <Typography variant="body2">Daily sports listings with competitions and TV channels in Spain. Times use Europe/Madrid. Only dates published by MARCA are available; the window advances on every refresh.</Typography> : <>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField fullWidth select label="League" value={value.league} disabled={saved || disabled || !leagues.length} onChange={(e) => {
          onChange({ ...value, league: e.target.value as EventProviderOptions['league'], interests: {} });
          onZone(leagues.find((league) => league.id === e.target.value)?.timezone ?? 'UTC');
        }}>{leagues.map((league) => <MenuItem key={league.id} value={league.id}>{league.name}</MenuItem>)}</TextField>
        <TextField label="Season" value={value.season} disabled={saved || disabled} onChange={(e) => onChange({ ...value, season: e.target.value })} helperText="For example, 2026-27" />
      </Stack>
      <TextField label="Source timezone" value={zone} disabled={disabled} onChange={(e) => onZone(e.target.value)} helperText="Confirm the timezone used for kickoff times. Date-only fixtures keep their time unknown." />
      <Typography variant="body2">Free community data, with no TV listings. A season file must exist in OpenFootball; fixtures and kickoff times may be incomplete.</Typography>
    </>}
    <TextField select label="Import window" value={value.window_days} disabled={disabled} onChange={(e) => onChange({ ...value, window_days: Number(e.target.value) })}>
      {Array.from(new Set([7, 14, 30, value.window_days ?? 14])).sort((a, b) => a - b).map((days) => <MenuItem key={days} value={days}>Next {days} days</MenuItem>)}
    </TextField>
    {names.isError ? <Alert severity="warning" action={<Button onClick={() => void names.refetch()}>Retry names</Button>}>
      The sports, competitions and teams to choose from are not available. {eventErrorMessage(names.error)}</Alert> : null}
    <EventInterestFields prefix="Import: " value={value.interests ?? emptyInterests} disabled={disabled}
      choices={names.data} loading={names.isFetching} onOpen={() => setWantedKey(namesKey)}
      onChange={(interests) => onChange({ ...value, interests })} emptyHint="Leave all empty for every event in the selected feeds." />
  </Stack>;
}

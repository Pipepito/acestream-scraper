import React, { useDeferredValue, useState } from 'react';
import { Alert, Box, Button, Chip, CircularProgress, Drawer, FormControlLabel, Checkbox, Stack, Tab, Tabs, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import StatusLine from '../components/StatusLine';
import EventImportPanel from '../components/events/EventImportPanel';
import EventSourcesPanel from '../components/events/EventSourcesPanel';
import EventDetails from '../components/events/EventDetails';
import StreamPlayerDialog from '../components/player/StreamPlayerDialog';
import { eventService, type EventUpdate, type EventSource } from '../services/eventService';
import { getErrorMessage } from '../utils/errorUtils';

const browserZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
function today(zone: string) {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
  return ['year', 'month', 'day'].map((key) => parts.find((part) => part.type === key)?.value).join('-');
}
export default function Events() {
  const cache = useQueryClient();
  const [tab, setTab] = useState('upcoming');
  const [zone, setZone] = useState(browserZone);
  const [zoneInput, setZoneInput] = useState(browserZone);
  const [zoneError, setZoneError] = useState(false);
  const [day, setDay] = useState(() => today(browserZone));
  const [search, setSearch] = useState('');
  const [sport, setSport] = useState('');
  const [competition, setCompetition] = useState('');
  const [source, setSource] = useState('');
  const [advanced, setAdvanced] = useState(false);
  const [followed, setFollowed] = useState(false);
  const [offset, setOffset] = useState(0);
  const [managing, setManaging] = useState(false);
  const [reviewSource, setReviewSource] = useState<EventSource | undefined>();
  const [adding, setAdding] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [playing, setPlaying] = useState<{ id: string; title: string } | null>(null);
  const [message, setMessage] = useState('');
  const deferredSearch = useDeferredValue(search);
  const filters = { search: deferredSearch, sport, competition, source, zone, day: tab === 'date' ? day : undefined, upcoming: tab === 'upcoming', followed, archived: tab === 'archived', offset };
  const list = useQuery({ queryKey: ['events', 'list', filters], queryFn: () => eventService.list(filters) });
  const detail = useQuery({ queryKey: ['events', 'detail', selected], queryFn: () => eventService.get(selected!), enabled: Boolean(selected) });
  const update = useMutation({ mutationFn: (input: EventUpdate) => eventService.update(selected!, input),
    onSuccess: () => { setMessage('Event saved.'); void cache.invalidateQueries({ queryKey: ['events'] }); },
    onError: (err) => setMessage(getErrorMessage(err)) });
  const events = list.data?.events ?? [];
  const total = list.data?.total ?? 0;
  const resetFilters = () => { setSearch(''); setSport(''); setCompetition(''); setSource(''); setFollowed(false); setOffset(0); setTab('all'); };
  return <Box>
    <PageHeader title="Events" subtitle="Schedules, broadcasts and your followed events." actions={<Stack direction="row" gap={1} flexWrap="wrap"><Button onClick={() => setManaging(!managing)} aria-expanded={managing}>Sources & retention</Button><Button variant="contained" onClick={() => { setReviewSource(undefined); setManaging(false); setAdding(true); }}>Add events</Button></Stack>} />
    <StatusLine items={[{ label: 'Events', value: list.isPending ? 'Loading…' : list.isError ? 'Unavailable' : total }, { label: 'Times', value: zone }]} />
    {message && !selected ? <Alert severity={update.isError ? 'error' : 'success'} onClose={() => setMessage('')} sx={{ mb: 2 }}>{message}</Alert> : null}
    {managing ? <EventSourcesPanel onReview={(source) => { setReviewSource(source); setManaging(false); setAdding(true); }} /> : null}
    {adding ? <EventImportPanel key={reviewSource?.id ?? 'new'} source={reviewSource} zone={zone} onClose={() => { setAdding(false); setReviewSource(undefined); }} /> : null}
    <ContentSection title="Schedule">
      <Tabs value={tab} onChange={(_, value: string) => { setTab(value); setOffset(0); }} variant="scrollable" scrollButtons="auto" aria-label="Event dates">
        <Tab label="Upcoming" value="upcoming" /><Tab label="By date" value="date" /><Tab label="All events" value="all" /><Tab label="Archived" value="archived" />
      </Tabs>
      <Stack direction="row" flexWrap="wrap" gap={1.5} sx={{ my: 2 }}>
        <Button onClick={() => { setDay(today(zone)); setTab('date'); setOffset(0); }}>Today</Button>
        {tab === 'date' ? <TextField type="date" label="Event date" value={day} onChange={(e) => { setDay(e.target.value); setOffset(0); }} InputLabelProps={{ shrink: true }} /> : null}
        <TextField label="Search events" value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} sx={{ flex: 1, minWidth: 180 }} />
      </Stack>
      <Stack direction="row" gap={1.5} flexWrap="wrap" sx={{ mb: 2 }}>
        <FormControlLabel control={<Checkbox checked={followed} onChange={(_, value) => { setFollowed(value); setOffset(0); }} />} label="Following" />
        <Button aria-expanded={advanced} aria-controls="event-filters" onClick={() => setAdvanced(!advanced)}>Filters & timezone{[sport, competition, source].filter(Boolean).length ? ` (${[sport, competition, source].filter(Boolean).length})` : ''}</Button>
      </Stack>
      {advanced ? <Stack id="event-filters" direction={{ xs: 'column', sm: 'row' }} gap={1.5} flexWrap="wrap" sx={{ mb: 2 }}>
        <TextField label="Display timezone" value={zoneInput} error={zoneError} helperText={zoneError ? 'Use a timezone such as Europe/Madrid' : 'IANA timezone'} onChange={(e) => setZoneInput(e.target.value)} onBlur={() => {
          try { new Intl.DateTimeFormat(undefined, { timeZone: zoneInput }).format(); setZone(zoneInput); setZoneError(false); setOffset(0); } catch { setZoneError(true); }
        }} />
        <TextField size="small" label="Sport" value={sport} onChange={(e) => { setSport(e.target.value); setOffset(0); }} />
        <TextField size="small" label="Competition" value={competition} onChange={(e) => { setCompetition(e.target.value); setOffset(0); }} />
        <TextField size="small" label="Source" value={source} onChange={(e) => { setSource(e.target.value); setOffset(0); }} />
      </Stack> : null}
      {list.isPending ? <CircularProgress aria-label="Loading events" /> : list.isError ? <Alert severity="error" action={<Button onClick={() => void list.refetch()}>Retry</Button>}>Events could not be loaded.</Alert> : !events.length ? <Stack spacing={1} sx={{ py: 3 }}>
        <Typography variant="h6">No events in this view</Typography>
        <Typography color="text.secondary">Add an event or import a schedule. Events without a start time appear under Upcoming and All events.</Typography>
        <Box><Button onClick={resetFilters}>Show all events</Button><Button onClick={() => setAdding(true)}>Add events</Button></Box>
      </Stack> : <Stack component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
        {events.map((event) => <Stack component="li" key={event.id} direction={{ xs: 'column', sm: 'row' }} gap={2} sx={{ py: 2, borderBottom: 1, borderColor: 'divider', alignItems: { sm: 'center' } }}>
          <Box sx={{ width: { sm: 150 }, flexShrink: 0 }}>
            <Typography fontWeight={600}>{event.starts_at ? new Date(event.starts_at).toLocaleTimeString(undefined, { timeZone: zone, hour: '2-digit', minute: '2-digit' }) : 'Time unknown'}</Typography>
            <Typography variant="body2" color="text.secondary">{event.starts_at ? new Date(event.starts_at).toLocaleDateString(undefined, { timeZone: zone, month: 'short', day: 'numeric' }) : 'Check source updates'}</Typography>
          </Box>
          <Box sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}>
            <Button sx={{ p: 0, textAlign: 'left', justifyContent: 'flex-start', fontSize: '1rem', fontWeight: 600 }} onClick={() => setSelected(event.id)}>{event.title}</Button>
            <Typography variant="body2" color="text.secondary">{[event.sport, event.competition].filter(Boolean).join(' · ') || 'Sport not supplied'}</Typography>
            <Typography variant="body2">{event.broadcasts.filter((b) => b.compatibility === 'playable').length} playable · {event.broadcasts.filter((b) => b.compatibility === 'unresolved').length} unresolved · {event.broadcasts.filter((b) => b.compatibility === 'unsupported').length} unsupported{event.broadcasts.some((b) => b.compatibility === 'unavailable') ? ` · ${event.broadcasts.filter((b) => b.compatibility === 'unavailable').length} unavailable` : ''}</Typography>
          </Box>
          <Stack direction="row" gap={1} alignItems="center" flexWrap="wrap"><Chip label={event.state === 'live' ? 'Live · reported' : event.state} size="small" variant="outlined" />{event.followed ? <Chip label="Following" size="small" /> : null}
            <Button aria-label={`View broadcasts for ${event.title}`} onClick={() => setSelected(event.id)}>View broadcasts</Button></Stack>
        </Stack>)}
      </Stack>}
      {total > 50 ? <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 2 }}><Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</Button><Typography>{offset + 1}–{Math.min(offset + 50, total)} of {total}</Typography><Button disabled={offset + 50 >= total} onClick={() => setOffset(offset + 50)}>Next</Button></Stack> : null}
    </ContentSection>
    <Drawer anchor="right" open={Boolean(selected)} onClose={() => setSelected(null)} PaperProps={{ role: 'dialog', 'aria-label': 'Event details', sx: { width: { xs: '100%', sm: 620 }, maxWidth: '100%', p: 2 } }}>
    {message ? <Alert severity={update.isError ? 'error' : 'success'} onClose={() => setMessage('')} sx={{ mb: 2 }}>{message}</Alert> : null}
    <Button onClick={() => setSelected(null)} sx={{ alignSelf: 'flex-start', mb: 1 }}>Close event details</Button>
    {selected && detail.isPending ? <CircularProgress aria-label="Loading event details" /> : null}
    {selected && detail.isError ? <Alert severity="error" action={<Button onClick={() => void detail.refetch()}>Retry</Button>}>Event details could not be loaded.</Alert> : null}
    {selected && detail.data ? <EventDetails key={`${detail.data.id}:${detail.data.revision}`} event={detail.data} zone={zone} busy={update.isPending} onUpdate={(input) => update.mutate(input)} onPlay={(id, label) => setPlaying({ id, title: `${detail.data.title} · ${label}` })} /> : null}
    </Drawer>
    <StreamPlayerDialog open={Boolean(playing)} contentId={playing?.id ?? null} title={playing?.title ?? ''} onClose={() => setPlaying(null)} />
  </Box>;
}

import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { useSearchParams } from 'react-router-dom';
import { validEventZone } from '../hooks/useDashboardEvents';
import React, { useDeferredValue, useRef, useState } from 'react';
import { Alert, Box, Button, CircularProgress, Drawer, MenuItem, FormControlLabel, Checkbox, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import EventAgenda from '../components/events/EventAgenda';
import StatusLine from '../components/StatusLine';
import EventInterestFields, { emptyInterests } from '../components/events/EventInterestFields';
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
  const tUi = useUiText();
  const cache = useQueryClient();
  const [params, setParams] = useSearchParams();
  const initialZone = params.get('zone') || browserZone;
  const displayZone = validEventZone(initialZone) ? initialZone : browserZone;
  const [tab, setTab] = useState('upcoming');
  const [zone, setZone] = useState(displayZone);
  const [zoneInput, setZoneInput] = useState(displayZone);
  const [zoneError, setZoneError] = useState(false);
  const [day, setDay] = useState(() => today(displayZone));
  const [search, setSearch] = useState('');
  const [interests, setInterests] = useState(emptyInterests);
  const [windowDays, setWindowDays] = useState(14);
  const choices = useQuery({ queryKey: ['events', 'interests'], queryFn: eventService.interests });
  const [sport, setSport] = useState('');
  const [competition, setCompetition] = useState('');
  const [source, setSource] = useState('');
  const [advanced, setAdvanced] = useState(false);
  const [followed, setFollowed] = useState(false);
  const [offset, setOffset] = useState(0);
  const [managing, setManaging] = useState(false);
  const [managementVisited, setManagementVisited] = useState(false);
  const [reviewSource, setReviewSource] = useState<EventSource | undefined>();
  const [adding, setAdding] = useState(false);
  const selected = params.get('event');
  const setSelected = (id: string | null) => {
    setFeedback(null);
    setParams(current => {
      const next = new URLSearchParams(current);
      if (id) next.set('event', id); else next.delete('event');
      return next;
    });
  };
  const [playing, setPlaying] = useState<{ id: string; title: string } | null>(null);
  const [feedback, setFeedback] = useState<{ error: unknown } | { saved: true } | null>(null);
  const message = feedback ? 'error' in feedback ? getErrorMessage(feedback.error) : tUi('Event saved.') : '';
  const action = useRef(false);
  const deferredSearch = useDeferredValue(search);
  const filters = { interests: JSON.stringify(interests), window_days: tab === 'upcoming' ? windowDays : undefined, search: deferredSearch, sport, competition, source, zone, day: tab === 'today' ? today(zone) : tab === 'date' ? day : undefined, upcoming: tab === 'upcoming', followed, archived: tab === 'archived', offset };
  const list = useQuery({ queryKey: ['events', 'list', filters], queryFn: () => eventService.list(filters) });
  const detail = useQuery({ queryKey: ['events', 'detail', selected], queryFn: () => eventService.get(selected!), enabled: Boolean(selected) });
  const update = useMutation({ mutationFn: (input: EventUpdate) => eventService.update(selected!, input),
    onSuccess: () => { setFeedback({ saved: true }); void cache.invalidateQueries({ queryKey: ['events'] }); },
    onError: (err) => setFeedback({ error: err }) });
  const saveEvent = async (input: EventUpdate) => {
    if (action.current) return false;
    action.current = true;
    try { await update.mutateAsync(input); return true; }
    catch { return false; }
    finally { action.current = false; }
  };
  const events = list.data?.events ?? [];
  const total = list.data?.total ?? 0;
  const interestCount = Object.values(interests).flat().length + [sport, competition, source].filter(Boolean).length + Number(followed);
  const resetFilters = () => { setInterests(emptyInterests); setSearch(''); setSport(''); setCompetition(''); setSource(''); setFollowed(false); setOffset(0); setTab('all'); };
  return <Box>
    <PageHeader title={tUi("Events")} subtitle={tUi("Find your next match, race or game.")} actions={<Stack direction="row" gap={1} flexWrap="wrap"><Button disabled={adding} onClick={() => { setManagementVisited(true); setManaging(!managing); }} aria-expanded={managing}>{tUi("Sources & retention")}</Button><Button disabled={adding} variant="contained" onClick={() => { setReviewSource(undefined); setManaging(false); setAdding(true); }}>{tUi("Add events")}</Button></Stack>} />
    <StatusLine items={[{ label: uiText("Events"), value: list.isPending ? uiText("Loading…") : list.isError ? uiText("Unavailable") : total }, { label: uiText("Times"), value: zone }]} />
    {message && !selected ? <Alert severity={update.isError ? 'error' : 'success'} onClose={() => setFeedback(null)} sx={{ mb: 2 }}>{message}</Alert> : null}
    {managementVisited ? <Box hidden={!managing}><EventSourcesPanel onReview={(source) => { setReviewSource(source); setManaging(false); setAdding(true); }} /></Box> : null}
    {adding ? <EventImportPanel key={reviewSource?.id ?? 'new'} source={reviewSource} zone={zone} onClose={() => { setAdding(false); setReviewSource(undefined); }} /> : null}
    <ContentSection title={tUi("Schedule")}>
      <Stack direction="row" flexWrap="wrap" gap={1.5} sx={{ mb: 2.5 }}>
        <TextField select size="small" label={tUi("When")} value={tab} onChange={(e) => { setTab(e.target.value); setOffset(0); }} sx={{ minWidth: 160 }}>
          <MenuItem value="upcoming">{tUi("Next")}{' '}{windowDays} {' '}{tUi("days")}</MenuItem><MenuItem value="today">{tUi("Today")}</MenuItem><MenuItem value="date">{tUi("Choose a date")}</MenuItem><MenuItem value="all">{tUi("All saved events")}</MenuItem><MenuItem value="archived">{tUi("Archived")}</MenuItem>
        </TextField>
        {tab === 'date' ? <TextField size="small" type="date" label={tUi("Event date")} value={day} onChange={(e) => { setDay(e.target.value); setOffset(0); }} InputLabelProps={{ shrink: true }} /> : null}
        <TextField size="small" label={tUi("Search events")} value={search} onChange={(e) => { setSearch(e.target.value); setOffset(0); }} sx={{ flex: 1, minWidth: 180 }} />
        <Button aria-expanded={advanced} aria-controls="event-filters" onClick={() => setAdvanced(!advanced)}>{tUi("Filter events")}{interestCount ? tUi(" ({{value0}})", { value0: interestCount }) : ''}</Button>
      </Stack>
      {advanced ? <Stack id="event-filters" spacing={2} sx={{ mb: 3 }}>
        <EventInterestFields value={interests} choices={choices.data} onChange={(value) => { setInterests(value); setOffset(0); }} />
        <Stack direction="row" gap={1} flexWrap="wrap">
          <FormControlLabel control={<Checkbox checked={followed} onChange={(_, value) => { setFollowed(value); setOffset(0); }} />} label={tUi("Following")} />
          {interestCount ? <Button onClick={() => { setInterests(emptyInterests); setSport(''); setCompetition(''); setSource(''); setFollowed(false); setOffset(0); }}>{tUi("Clear filters")}</Button> : null}
        </Stack>
        <Box component="details">
          <Box component="summary" sx={{ cursor: 'pointer', color: 'text.secondary', py: 1 }}>{tUi("More filters & timezone")}</Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5} flexWrap="wrap" sx={{ mt: 1 }}>
            <TextField size="small" label={tUi("Display timezone")} value={zoneInput} error={zoneError} helperText={zoneError ? tUi("Use a timezone such as Europe/Madrid") : tUi("IANA timezone")} onChange={(e) => setZoneInput(e.target.value)} onBlur={() => {
              try { new Intl.DateTimeFormat(undefined, { timeZone: zoneInput }).format(); setZone(zoneInput); setZoneError(false); setOffset(0); } catch { setZoneError(true); }
            }} />
            <TextField select size="small" label={tUi("Upcoming window")} value={windowDays} onChange={(e) => { setWindowDays(Number(e.target.value)); setOffset(0); }}>{[7, 14, 30].map((days) => <MenuItem value={days} key={days}>{tUi("Next")}{' '}{days} {' '}{tUi("days")}</MenuItem>)}</TextField>
            <TextField size="small" label={tUi("Sport contains")} value={sport} onChange={(e) => { setSport(e.target.value); setOffset(0); }} />
            <TextField size="small" label={tUi("Competition contains")} value={competition} onChange={(e) => { setCompetition(e.target.value); setOffset(0); }} />
            <TextField size="small" label={tUi("Source")} value={source} onChange={(e) => { setSource(e.target.value); setOffset(0); }} />
          </Stack>
        </Box>
      </Stack> : null}
      {list.isPending ? <CircularProgress aria-label={tUi("Loading events")} /> : list.isError ? <Alert severity="error" action={<Button onClick={() => void list.refetch()}>{tUi("Retry")}</Button>}>{tUi("Events could not be loaded.")}</Alert> : !events.length ? <Stack spacing={1} sx={{ py: 3 }}>
        <Typography variant="h6">{tUi("No events in this view")}</Typography>
        <Typography color="text.secondary">{tUi("Add an event or import a schedule. Events without a date appear in the upcoming schedule and All saved events.")}</Typography>
        <Box><Button onClick={resetFilters}>{tUi("Show all events")}</Button><Button onClick={() => setAdding(true)}>{tUi("Add events")}</Button></Box>
      </Stack> : <EventAgenda events={events} zone={zone} today={today(zone)} onSelect={setSelected} />}
      {total > 50 ? <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 2 }}><Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>{tUi("Previous")}</Button><Typography>{offset + 1}–{Math.min(offset + 50, total)} {' '}{tUi("of")}{' '}{total}</Typography><Button disabled={offset + 50 >= total} onClick={() => setOffset(offset + 50)}>{tUi("Next")}</Button></Stack> : null}
    </ContentSection>
    <Drawer anchor="right" open={Boolean(selected)} onClose={() => setSelected(null)} PaperProps={{ role: 'dialog', 'aria-label': uiText("Event details"), sx: { width: { xs: '100%', sm: 620 }, maxWidth: '100%', p: 2 } }}>
    {message ? <Alert severity={update.isError ? 'error' : 'success'} onClose={() => setFeedback(null)} sx={{ mb: 2 }}>{message}</Alert> : null}
    <Button onClick={() => setSelected(null)} sx={{ alignSelf: 'flex-start', mb: 1 }}>{tUi("Close event details")}</Button>
    {selected && detail.isPending ? <CircularProgress aria-label={tUi("Loading event details")} /> : null}
    {selected && detail.isError ? <Alert severity="error" action={<Button onClick={() => void detail.refetch()}>{tUi("Retry")}</Button>}>{tUi("Event details could not be loaded. The event may have been removed; close details to return to the agenda.")}</Alert> : null}
    {selected && detail.data?.archived ? <Alert severity="info">{tUi("This event is archived. Close details to return to the agenda.")}</Alert> : null}
    {selected && detail.data && !detail.isError ? <EventDetails key={detail.data.id} event={detail.data} zone={zone} busy={update.isPending} onUpdate={saveEvent} onPlay={(id, label) => setPlaying({ id, title: `${detail.data.title} · ${label}` })} /> : null}
    </Drawer>
    <StreamPlayerDialog open={Boolean(playing)} contentId={playing?.id ?? null} title={playing?.title ?? ''} onClose={() => setPlaying(null)} />
  </Box>;
}

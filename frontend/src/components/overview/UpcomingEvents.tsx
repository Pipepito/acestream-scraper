import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import { EventAgendaRow } from '../events/EventAgenda';
import EventInterestFields from '../events/EventInterestFields';
import { eventService } from '../../services/eventService';
import { readEventPreferences, saveEventPreferences, useDashboardEvents, validEventZone, type DashboardEventView } from '../../hooks/useDashboardEvents';

export default function UpcomingEvents() {
  const navigate = useNavigate();
  const [preferences, setPreferences] = useState(readEventPreferences);
  const [editing, setEditing] = useState(false);
  const [zoneInput, setZoneInput] = useState(preferences.zone);
  const [zoneError, setZoneError] = useState(false);
  const list = useDashboardEvents(preferences);
  const choices = useQuery({ queryKey: ['events', 'interests'], queryFn: eventService.interests, enabled: editing });
  useEffect(() => saveEventPreferences(preferences), [preferences]);
  const needsInterests = preferences.view === 'interests' && !Object.values(preferences.interests).some(names => names?.length);
  const selectAll = () => setPreferences(current => ({ ...current, view: 'all' }));
  return <ContentSection title="Up next" description={`Live reports and the next seven days · ${preferences.zone}`} actions={<Button component={RouterLink} to="/events">View all events</Button>}>
    <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
      <TextField select size="small" label="Events to show" value={preferences.view} onChange={e => setPreferences(current => ({ ...current, view: e.target.value as DashboardEventView }))} sx={{ minWidth: 180 }}>
        <MenuItem value="all">All upcoming</MenuItem><MenuItem value="following">Following</MenuItem><MenuItem value="interests">My interests</MenuItem>
      </TextField>
      <Button aria-expanded={editing} aria-controls="dashboard-event-preferences" onClick={() => setEditing(!editing)}>Customize events</Button>
    </Stack>
    {editing ? <Stack id="dashboard-event-preferences" spacing={2} sx={{ mb: 2 }}>
      <Typography variant="body2">Display preferences stay in this browser. Following an event is shared across this installation.</Typography>
      {choices.isError ? <Alert severity="warning" action={<Button onClick={() => void choices.refetch()}>Retry choices</Button>}>Interest suggestions could not be loaded. You can still type a name.</Alert> : null}
      <EventInterestFields emptyHint="Select at least one for My interests." value={preferences.interests} choices={choices.data} onChange={interests => setPreferences(current => ({ ...current, interests }))} />
      <TextField size="small" label="Display timezone" value={zoneInput} error={zoneError} helperText={zoneError ? 'Use a timezone such as Europe/Madrid' : 'IANA timezone'} onChange={e => setZoneInput(e.target.value)} onBlur={() => {
        const valid = validEventZone(zoneInput); setZoneError(!valid);
        if (valid) setPreferences(current => ({ ...current, zone: zoneInput }));
      }} />
    </Stack> : null}
    {needsInterests ? <Stack spacing={1}><Typography>Choose a sport, competition or team in Customize events to build this view.</Typography><Box><Button onClick={() => setEditing(true)}>Choose interests</Button><Button onClick={selectAll}>Show all upcoming</Button></Box></Stack>
      : list.isError ? <Alert severity="warning" action={<Button onClick={() => void list.refetch()}>Retry events</Button>}>Upcoming events could not be loaded.</Alert>
      : list.isPending ? <Typography role="status">Loading upcoming events…</Typography>
      : !list.data?.events.length ? <Stack spacing={1}>
        <Typography>{preferences.view === 'following' ? 'No followed events are coming up. Follow an event from its details in Events.' : preferences.view === 'interests' ? 'No upcoming events match your interests.' : 'No live or upcoming events in the next seven days.'}</Typography>
        <Box>{preferences.view !== 'all' ? <Button onClick={selectAll}>Show all upcoming</Button> : null}<Button component={RouterLink} to="/events">Browse or add events</Button></Box>
      </Stack> : <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
        {list.data.events.map(event => <EventAgendaRow key={event.id} event={event} zone={preferences.zone} showDate onSelect={id => navigate(`/events?event=${encodeURIComponent(id)}&zone=${encodeURIComponent(preferences.zone)}`)} />)}
      </Box>}
    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>Times to be confirmed appear after timed events. Undated events remain in the full agenda. Live status is reported by the source.</Typography>
  </ContentSection>;
}

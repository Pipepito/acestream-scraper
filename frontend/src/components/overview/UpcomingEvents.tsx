import { useUiText } from '../../i18n/useUiText';
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
  const tUi = useUiText();
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
  return <ContentSection title={tUi("Up next")} description={tUi("Live reports and the next seven days · {{value0}}", { value0: preferences.zone })} actions={<Button component={RouterLink} to="/events">{tUi("View all events")}</Button>}>
    <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
      <TextField select size="small" label={tUi("Events to show")} value={preferences.view} onChange={e => setPreferences(current => ({ ...current, view: e.target.value as DashboardEventView }))} sx={{ minWidth: 180 }}>
        <MenuItem value="all">{tUi("All upcoming")}</MenuItem><MenuItem value="following">{tUi("Following")}</MenuItem><MenuItem value="interests">{tUi("My interests")}</MenuItem>
      </TextField>
      <Button aria-expanded={editing} aria-controls="dashboard-event-preferences" onClick={() => setEditing(!editing)}>{tUi("Customize events")}</Button>
    </Stack>
    {editing ? <Stack id="dashboard-event-preferences" spacing={2} sx={{ mb: 2 }}>
      <Typography variant="body2">{tUi("Display preferences stay in this browser. Following an event is shared across this installation.")}</Typography>
      {choices.isError ? <Alert severity="warning" action={<Button onClick={() => void choices.refetch()}>{tUi("Retry choices")}</Button>}>{tUi("Interest suggestions could not be loaded. You can still type a name.")}</Alert> : null}
      <EventInterestFields emptyHint={tUi('Select at least one for My interests.')} value={preferences.interests} choices={choices.data} onChange={interests => setPreferences(current => ({ ...current, interests }))} />
      <TextField size="small" label={tUi("Display timezone")} value={zoneInput} error={zoneError} helperText={zoneError ? tUi("Use a timezone such as Europe/Madrid") : tUi("IANA timezone")} onChange={e => setZoneInput(e.target.value)} onBlur={() => {
        const valid = validEventZone(zoneInput); setZoneError(!valid);
        if (valid) setPreferences(current => ({ ...current, zone: zoneInput }));
      }} />
    </Stack> : null}
    {needsInterests ? <Stack spacing={1}><Typography>{tUi("Choose a sport, competition or team in Customize events to build this view.")}</Typography><Box><Button onClick={() => setEditing(true)}>{tUi("Choose interests")}</Button><Button onClick={selectAll}>{tUi("Show all upcoming")}</Button></Box></Stack>
      : list.isError ? <Alert severity="warning" action={<Button onClick={() => void list.refetch()}>{tUi("Retry events")}</Button>}>{tUi("Upcoming events could not be loaded.")}</Alert>
      : list.isPending ? <Typography role="status">{tUi("Loading upcoming events…")}</Typography>
      : !list.data?.events.length ? <Stack spacing={1}>
        <Typography>{preferences.view === 'following' ? tUi("No followed events are coming up. Follow an event from its details in Events.") : preferences.view === 'interests' ? tUi("No upcoming events match your interests.") : tUi("No live or upcoming events in the next seven days.")}</Typography>
        <Box>{preferences.view !== 'all' ? <Button onClick={selectAll}>{tUi("Show all upcoming")}</Button> : null}<Button component={RouterLink} to="/events">{tUi("Browse or add events")}</Button></Box>
      </Stack> : <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0 }}>
        {list.data.events.map(event => <EventAgendaRow key={event.id} event={event} zone={preferences.zone} showDate onSelect={id => navigate(`/events?event=${encodeURIComponent(id)}&zone=${encodeURIComponent(preferences.zone)}`)} />)}
      </Box>}
    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>{tUi("Times to be confirmed appear after timed events. Undated events remain in the full agenda. Live status is reported by the source.")}</Typography>
  </ContentSection>;
}

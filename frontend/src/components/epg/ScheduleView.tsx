import React, { useMemo, useState } from 'react';
import { Alert, Box, Button, Chip, Collapse, LinearProgress, List, ListItem, Stack, Tab, Tabs, Typography, useTheme } from '@mui/material';
import { addDays, format, parseISO, startOfDay } from 'date-fns';
import { useEPGPrograms } from '../../hooks/useEPG';
import type { EPGProgram } from '../../services/epgService';
import NowNext from './NowNext';

export interface ScheduleViewProps {
  epgChannelId: number;
  /** Injectable clock for tests. */
  now?: Date;
}

const DAY_COUNT = 7;

export const dayLabel = (offset: number, base: Date): string => {
  if (offset === 0) return 'Today';
  if (offset === 1) return 'Tomorrow';
  return format(addDays(base, offset), 'EEE d');
};

const ProgramRow: React.FC<{ program: EPGProgram; past: boolean }> = ({ program, past }) => {
  const [open, setOpen] = useState(false);
  const details = [program.subtitle, program.description].filter(Boolean).join(' — ');
  return (
    <ListItem
      component="li"
      aria-label={program.title}
      sx={{ display: 'block', py: 1, px: 0, opacity: past ? 0.6 : 1 }}
      divider
    >
      <Stack direction="row" spacing={1.5} alignItems="flex-start">
        <Typography component="span" variant="body2" sx={{ fontVariantNumeric: 'tabular-nums', minWidth: 96, pt: 0.25 }} color="text.secondary">
          {format(parseISO(program.start_time), 'HH:mm')}–{format(parseISO(program.end_time), 'HH:mm')}
        </Typography>
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
            <Typography component="span" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
              {program.title}
            </Typography>
            {program.category ? <Chip label={program.category} size="small" variant="outlined" /> : null}
          </Stack>
          {details ? (
            <>
              <Collapse in={open}>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {details}
                </Typography>
              </Collapse>
              <Button size="small" onClick={() => setOpen((value) => !value)} aria-expanded={open} sx={{ mt: 0.25, ml: -0.75 }}>
                {open ? 'Less' : 'More'}
              </Button>
            </>
          ) : null}
        </Box>
      </Stack>
    </ListItem>
  );
};

/** Day-tabbed schedule for one guide channel: Now/Next for today, then the day's programmes grouped by hour. */
const ScheduleView: React.FC<ScheduleViewProps> = ({ epgChannelId, now = new Date() }) => {
  const theme = useTheme();
  const [dayOffset, setDayOffset] = useState(0);
  const today = useMemo(() => startOfDay(now), [now]);
  const dayStart = useMemo(() => addDays(today, dayOffset), [today, dayOffset]);
  const dayEnd = useMemo(() => addDays(dayStart, 1), [dayStart]);

  // The API keeps programmes fully inside [start, end]; widen the window and trim client-side so
  // programmes crossing midnight still show on both days.
  const { data, isLoading, error } = useEPGPrograms(
    epgChannelId,
    addDays(dayStart, -1).toISOString(),
    addDays(dayEnd, 1).toISOString()
  );

  const programs = useMemo(
    () =>
      (data ?? [])
        .filter((program) => parseISO(program.end_time) > dayStart && parseISO(program.start_time) < dayEnd)
        .sort((a, b) => parseISO(a.start_time).getTime() - parseISO(b.start_time).getTime()),
    [data, dayStart, dayEnd]
  );

  const groups = useMemo(() => {
    const byHour = new Map<string, EPGProgram[]>();
    programs.forEach((program) => {
      const start = parseISO(program.start_time);
      const key = start < dayStart ? 'Before midnight' : format(start, 'HH:00');
      byHour.set(key, [...(byHour.get(key) ?? []), program]);
    });
    return Array.from(byHour.entries());
  }, [programs, dayStart]);

  const dayPhrase = dayOffset === 0 ? 'today' : dayOffset === 1 ? 'tomorrow' : `on ${dayLabel(dayOffset, today)}`;

  return (
    <Box>
      <Tabs
        value={dayOffset}
        onChange={(_event, value: number) => setDayOffset(value)}
        variant="scrollable"
        scrollButtons="auto"
        aria-label="Schedule day"
        sx={{ mb: 2, borderBottom: `1px solid ${theme.appTokens.surface.border}` }}
      >
        {Array.from({ length: DAY_COUNT }, (_, offset) => (
          <Tab key={offset} value={offset} label={dayLabel(offset, today)} />
        ))}
      </Tabs>

      {dayOffset === 0 && !isLoading && !error ? <NowNext programs={programs} now={now} /> : null}

      {isLoading ? (
        <Box role="status" aria-live="polite" sx={{ mb: 2 }}>
          <LinearProgress sx={{ mb: 1 }} />
          <Typography variant="body2">Loading schedule…</Typography>
        </Box>
      ) : null}

      {error ? <Alert severity="error">Unable to load the schedule right now.</Alert> : null}

      {!isLoading && !error ? (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {programs.length === 0 ? `No programmes ${dayPhrase}.` : `${programs.length} programme${programs.length === 1 ? '' : 's'} ${dayPhrase}`}
          </Typography>
          {groups.map(([hour, items]) => (
            <Box key={hour} sx={{ mb: 1.5 }}>
              <Typography variant="statusMeta" component="h3" color="text.secondary" sx={{ mb: 0.5 }}>
                {hour}
              </Typography>
              <List disablePadding aria-label={`Programmes from ${hour}`}>
                {items.map((program) => (
                  <ProgramRow key={program.id} program={program} past={dayOffset === 0 && parseISO(program.end_time) <= now} />
                ))}
              </List>
            </Box>
          ))}
        </>
      ) : null}
    </Box>
  );
};

export default ScheduleView;

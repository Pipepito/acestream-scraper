import React from 'react';
import { Alert, Button, Typography } from '@mui/material';
import { addDays, format, parseISO, startOfDay } from 'date-fns';
import { useEPGPrograms, useResolveEPGChannel } from '../../hooks/useEPG';
import type { TVChannel } from '../../types/tvChannelTypes';
import ScheduleView from '../epg/ScheduleView';

export const useChannelGuide = (channel: TVChannel, now: Date) => {
  const mapping = useResolveEPGChannel(channel.epg_source_id, channel.epg_id, { retry: false });
  const day = startOfDay(now);
  const programs = useEPGPrograms(mapping.data?.id ?? 0, addDays(day, -1).toISOString(), addDays(day, 2).toISOString(), {
    refetchInterval: 60_000,
  });
  return { mapping, programs };
};

const ChannelGuide: React.FC<{ channel: TVChannel; now: Date; compact?: boolean }> = ({ channel, now, compact }) => {
  const { mapping, programs } = useChannelGuide(channel, now);
  if (!channel.epg_id || !channel.epg_source_id) return <Typography color="text.secondary">No guide mapped to this channel.</Typography>;
  if (mapping.isLoading || programs.isLoading) return <Typography role="status">Loading programme…</Typography>;
  if (mapping.isError || programs.isError) return <Alert severity="warning" action={<Button color="inherit" onClick={() => { if (mapping.isError) void mapping.refetch(); else void programs.refetch(); }}>Retry</Button>}>Guide unavailable.</Alert>;
  if (!compact && mapping.data) return <ScheduleView epgChannelId={mapping.data.id} now={now} />;
  const current = programs.data?.find((item) => parseISO(item.start_time) <= now && parseISO(item.end_time) > now);
  const next = programs.data?.find((item) => parseISO(item.start_time) > now);
  return <>
    <Typography sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>{current ? `Now · ${current.title}` : 'No current programme listed.'}</Typography>
    {current ? <Typography variant="body2" color="text.secondary">{format(parseISO(current.start_time), 'HH:mm')}–{format(parseISO(current.end_time), 'HH:mm')}</Typography> : null}
    {next ? <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>Next · {format(parseISO(next.start_time), 'HH:mm')} · {next.title}</Typography> : null}
  </>;
};

export default ChannelGuide;

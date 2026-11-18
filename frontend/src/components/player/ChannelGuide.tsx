import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Box, Button, Typography } from '@mui/material';
import { addDays, format, parseISO, startOfDay } from 'date-fns';
import { useEPGPrograms, useResolveEPGChannel } from '../../hooks/useEPG';
import type { TVChannel } from '../../types/tvChannelTypes';
import type { TVChannelNowNext } from '../../services/tvChannelService';
import ScheduleView from '../epg/ScheduleView';

export const useChannelGuide = (channel: TVChannel, now: Date, options: { enabled?: boolean } = {}) => {
  const enabled = options.enabled ?? true;
  const mapping = useResolveEPGChannel(channel.epg_source_id, channel.epg_id, { retry: false, enabled: enabled && Boolean(channel.epg_source_id && channel.epg_id) });
  const day = startOfDay(now);
  const programs = useEPGPrograms(mapping.data?.id ?? 0, addDays(day, -1).toISOString(), addDays(day, 2).toISOString(), {
    refetchInterval: 60_000,
    enabled: enabled && Boolean(mapping.data?.id),
  });
  return { mapping, programs };
};

interface ChannelGuideProps {
  channel: TVChannel;
  now: Date;
  compact?: boolean;
  /**
   * Batched Now/Next for this channel (Live TV list). A row skips the per-channel
   * queries; `null` means the batch knows no guide for it; undefined keeps the queries.
   */
  nowNext?: TVChannelNowNext | null;
  /** Render only the "TV guide & recordings" expander; the caller shows Now/Next itself. */
  expanderOnly?: boolean;
}

const ChannelGuide: React.FC<ChannelGuideProps> = ({ channel, now, compact, nowNext, expanderOnly = false }) => {
  const tUi = useUiText();
  const batched = nowNext !== undefined;
  const { mapping, programs } = useChannelGuide(channel, now, { enabled: !batched });
  const [expanded, setExpanded] = useState(false);
  const canRecord = channel.is_active && channel.acestream_channels.some(stream => stream.is_active);
  if (!channel.epg_id || !channel.epg_source_id) return expanderOnly ? null : <Typography color="text.secondary">{tUi("No guide mapped to this channel.")}</Typography>;
  const epgChannelId = batched ? nowNext?.epg_channel_id : mapping.data?.id;
  if (!batched && (mapping.isLoading || programs.isLoading)) return <Typography role="status">{tUi("Loading programme…")}</Typography>;
  if (!batched && (mapping.isError || programs.isError)) return <Alert severity="warning" action={<Button color="inherit" onClick={() => { if (mapping.isError) void mapping.refetch(); else void programs.refetch(); }}>{tUi("Retry")}</Button>}>{tUi("Guide unavailable.")}</Alert>;
  if (!compact && epgChannelId) return <ScheduleView tvChannelId={canRecord ? channel.id : undefined} tvChannelName={channel.name} epgChannelId={epgChannelId} now={now} />;
  const current = batched ? nowNext?.now : programs.data?.find((item) => parseISO(item.start_time) <= now && parseISO(item.end_time) > now);
  const next = batched ? nowNext?.next : programs.data?.find((item) => parseISO(item.start_time) > now);
  const span = (slot: { start?: string; end?: string; start_time?: string; end_time?: string }) => [slot.start ?? slot.start_time ?? '', slot.end ?? slot.end_time ?? ''];
  return <>
    {!expanderOnly ? <>
      <Typography sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>{current ? tUi("Now · {{value0}}", { value0: current.title }) : tUi("No current programme listed.")}</Typography>
      {current ? <Typography variant="body2" color="text.secondary">{format(parseISO(span(current)[0]), 'HH:mm')}–{format(parseISO(span(current)[1]), 'HH:mm')}</Typography> : null}
      {next ? <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>{tUi("Next ·")}{' '}{format(parseISO(span(next)[0]), 'HH:mm')} · {next.title}</Typography> : null}
    </> : null}
    {compact && epgChannelId ? <>
      <Button aria-label={tUi("TV guide for {{value0}}", { value0: channel.name })} aria-expanded={expanded} aria-controls={`channel-guide-${channel.id}`} onClick={() => setExpanded(value => !value)} sx={{ mt: 1 }}>
        {expanded ? tUi("Hide TV guide") : tUi("TV guide & recordings")}
      </Button>
      {expanded ? <Box id={`channel-guide-${channel.id}`} role="region" aria-label={tUi("TV guide for {{value0}}", { value0: channel.name })} sx={{ mt: 2 }}>
        {!canRecord ? <Alert severity="info" sx={{ mb: 2 }}>{tUi("Enable a stream assigned to this TV channel to schedule recordings.")}</Alert> : null}
        <ScheduleView tvChannelId={canRecord ? channel.id : undefined} tvChannelName={channel.name} epgChannelId={epgChannelId} now={now} />
      </Box> : null}
    </> : null}
  </>;
};

export default ChannelGuide;

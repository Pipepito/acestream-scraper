import { useAppPreferences } from '../../preferences/AppPreferences';
import ProgrammeArtwork from '../ProgrammeArtwork';
import React, { useEffect, useRef } from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import { format, parseISO } from 'date-fns';
import type { TVChannel } from '../../types/tvChannelTypes';
import type { GuideSlot, TVChannelNowNext } from '../../services/tvChannelService';
import RecordButton from '../recordings/RecordButton';
import PlayOnMenu from '../player/PlayOnMenu';
import ChannelGuide from '../player/ChannelGuide';

interface TVChannelListProps {
  channels: TVChannel[];
  selectedId: number;
  now: Date;
  /** Batched Now/Next by TV channel id; undefined while loading, a Map once known. */
  nowNext?: Map<number, TVChannelNowNext>;
  /** The batched read failed: rows fall back to their own guide queries, which carry Retry. */
  nowNextFailed?: boolean;
  onWatch: (channel: TVChannel) => void;
}

const time = (value: string) => format(parseISO(value), 'HH:mm');

const NowNextLines: React.FC<{ row: TVChannelNowNext | null | undefined; hasGuide: boolean }> = ({ row, hasGuide }) => {
  if (!hasGuide) return <Typography color="text.secondary">No guide mapped to this channel.</Typography>;
  if (row === undefined) return <Typography role="status">Loading programme…</Typography>;
  const current: GuideSlot | null | undefined = row?.now;
  const next: GuideSlot | null | undefined = row?.next;
  return <>
    <Typography sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>{current ? `Now · ${current.title}` : 'No current programme listed.'}</Typography>
    {current ? <Typography variant="body2" color="text.secondary">{time(current.start)}–{time(current.end)}</Typography> : null}
    {next ? <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>Next · {time(next.start)} · {next.title}</Typography> : null}
  </>;
};

const ChannelRow: React.FC<{ channel: TVChannel; selected: boolean; now: Date; row: TVChannelNowNext | null | undefined; fallback: boolean; onWatch: (channel: TVChannel) => void }> = ({ channel, selected, now, row, fallback, onWatch }) => {
  const { interface: preset } = useAppPreferences();
  const ref = useRef<HTMLElement>(null);
  useEffect(() => { if (selected) ref.current?.scrollIntoView?.({ block: 'nearest' }); }, [selected]);
  // A batched row proves the server resolved a guide mapping, whatever the catalogue copy carries.
  const onlineStreams = channel.acestream_channels.filter(stream => stream.is_active !== false && stream.is_online === true);
  const bestStream = onlineStreams[0] ?? channel.acestream_channels.find(stream => stream.is_active !== false) ?? channel.acestream_channels[0];
  const hasGuide = Boolean(row) || Boolean(channel.epg_id && channel.epg_source_id);
  return <Box component="article" ref={ref} aria-label={channel.name} aria-current={selected ? 'true' : undefined}
    sx={{ py: 2, px: preset === 'lime' ? 1 : 2, mx: preset === 'lime' ? -1 : 0, minWidth: 0, border: preset === 'lime' ? 0 : 1, borderBottom: 1, borderRadius: preset === 'lime' ? 0 : 2, borderColor: 'divider', contentVisibility: 'auto', containIntrinsicSize: 'auto 140px',
      ...(selected ? { bgcolor: 'action.selected', borderRadius: 1 } : {}) }}>
    <Box sx={{ display: preset === 'lime' ? 'none' : 'block' }}><ProgrammeArtwork src={row?.now?.image_url} /></Box>
    <Stack direction="row" spacing={1.5} useFlexGap flexWrap="wrap" alignItems="center" sx={{ mb: 1 }}>
      <Box sx={{ flex: '1 1 180px', minWidth: 0 }}>
        <Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{channel.channel_number != null ? `${channel.channel_number}. ` : ''}{channel.name}</Typography>
        <Typography variant="body2" color="text.secondary">{onlineStreams.length ? `${onlineStreams.length} online stream${onlineStreams.length === 1 ? '' : 's'}` : 'No stream verified online'}{channel.category ? ` · ${channel.category}` : ''}</Typography>
      </Box>
      <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap">
        <Button variant="contained" startIcon={<PlayArrowRounded />} aria-pressed={selected} aria-label={`Watch ${channel.name}`} onClick={() => onWatch(channel)}>{selected ? 'Selected' : 'Watch'}</Button>
        <RecordButton channelId={channel.id} channelName={channel.name} disabled={!channel.acestream_channels.some(stream => stream.is_active)} />
        <PlayOnMenu contentId={bestStream.id} title={channel.name} label="Send to player" />
      </Stack>
    </Stack>
    {fallback ? null : <NowNextLines row={row} hasGuide={hasGuide} />}
    {/* Same slot in every state, so an opened guide (and its dialogs) survives the batch loading or failing.
        While the batch loads, `null` keeps the guide's own per-channel queries off: the batch is the only read. */}
    {hasGuide || fallback ? <ChannelGuide channel={channel} now={now} compact nowNext={fallback ? undefined : (row ?? null)} expanderOnly={!fallback} /> : null}
  </Box>;
};

/** The whole TV catalogue, no pagination: the list scrolls and the playing row stays highlighted. */
const TVChannelList: React.FC<TVChannelListProps> = ({ channels, selectedId, now, nowNext, nowNextFailed = false, onWatch }) => (
  <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: 'minmax(0, 1fr)', '[data-interface=coral] &': { gridTemplateColumns: { xs: 'minmax(0, 1fr)', xl: 'repeat(2, minmax(0, 1fr))' } }, '[data-interface=cyan] &': { gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'repeat(2, minmax(0, 1fr))', xl: 'repeat(3, minmax(0, 1fr))' } } }}>
    {channels.map((channel) => <ChannelRow key={channel.id} channel={channel} selected={selectedId === channel.id} now={now}
      row={nowNext ? nowNext.get(channel.id) ?? null : undefined} fallback={nowNextFailed} onWatch={onWatch} />)}
  </Box>
);

export default TVChannelList;

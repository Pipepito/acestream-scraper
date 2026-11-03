import React from 'react';
import { Box, Chip, Stack, Typography } from '@mui/material';
import { networkStatusLabel } from '../channels/NetworkStatusChip';
import type { TVChannel } from '../../types/tvChannelTypes';
import { formatBitrate } from '../../utils/format';

type SourceStream = TVChannel['acestream_channels'][number];

interface SourceChipsProps {
  streams: SourceStream[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const signalText = (stream: SourceStream) => stream.is_online === true ? 'signal verified' : stream.is_online === false ? 'no signal verified' : 'signal not checked';
const dotColor = (stream: SourceStream) => stream.is_online === true ? 'success.main' : stream.is_online === false ? 'error.main' : 'text.disabled';

/** The playing channel's streams as one visible row: the active one is filled, any other switches the source. */
const SourceChips: React.FC<SourceChipsProps> = ({ streams, selectedId, onSelect }) => {
  if (!streams.length) return null;
  return (
    <Stack spacing={0.5}>
      <Typography variant="caption" color="text.secondary" id="player-sources-label">Sources</Typography>
      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" role="group" aria-label="Sources">
        {streams.map((stream, index) => {
          const selected = stream.id === selectedId;
          const name = stream.name || stream.id.slice(0, 8);
          const detail = [networkStatusLabel(stream.network_status), signalText(stream), stream.bitrate_bps ? formatBitrate(stream.bitrate_bps) : null].filter(Boolean).join(', ');
          return <Chip key={stream.id} clickable component="button" role="button" aria-pressed={selected}
            aria-label={`Source ${index + 1}: ${name}, ${detail}`} title={detail}
            color={selected ? 'primary' : 'default'} variant={selected ? 'filled' : 'outlined'}
            onClick={() => { if (!selected) onSelect(stream.id); }}
            icon={<Box component="span" aria-hidden sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: dotColor(stream), ml: 1 }} />}
            label={`${index + 1}. ${name}`} sx={{ maxWidth: '100%', '& .MuiChip-label': { overflowWrap: 'anywhere', whiteSpace: 'normal' } }} />;
        })}
      </Stack>
    </Stack>
  );
};

export default SourceChips;

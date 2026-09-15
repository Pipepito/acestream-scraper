import React from 'react';
import { Box, Tooltip, Typography } from '@mui/material';
import type { AcestreamChannel } from '../../services/channelService';
import { formatRelativeTime } from '../../utils/format';
import { formatDateTime } from '../../utils/formatters';

interface StreamStatisticsProps {
  channel: AcestreamChannel;
}

const speed = (value: number | null | undefined) => value == null ? 'Unknown' : `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })} KB/s`;

/** Engine observations and encoded media bitrate have independent timestamps. */
const StreamStatistics: React.FC<StreamStatisticsProps> = ({ channel }) => {
  const stats = channel.stream_stats;
  const details = stats
    ? `Engine sample: ${formatDateTime(stats.observed_at)}. Upload: ${speed(stats.upload_speed_kbytes_sec)}. Media bitrate: ${channel.bitrate_checked_at ? formatDateTime(channel.bitrate_checked_at) : 'not measured'}. These are short probe observations, not sustained throughput or a playback guarantee.`
    : 'No engine statistics sampled yet. Run Check status, or enable scheduled stream checks in Settings → Automation. An engine must be configured.';
  return (
    <Tooltip title={details} describeChild>
      <Box tabIndex={0} aria-label={`Stream statistics for ${channel.name}`} sx={{ minWidth: 0, py: 0.5 }}>
        <Typography variant="body2">
          {stats ? `${stats.peers == null ? 'Unknown peers' : `${stats.peers} peers`} · Down ${speed(stats.download_speed_kbytes_sec)}` : 'Not sampled'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Media {channel.bitrate_bps == null ? 'unknown' : `${(channel.bitrate_bps / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })} Mbps`}
          {stats ? ` · Up ${speed(stats.upload_speed_kbytes_sec)}` : ''}
        </Typography>
        {stats ? <Typography variant="caption" color="text.secondary">Sample {formatRelativeTime(stats.observed_at)}</Typography> : null}
      </Box>
    </Tooltip>
  );
};

export default StreamStatistics;

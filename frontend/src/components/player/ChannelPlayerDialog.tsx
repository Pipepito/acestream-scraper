import { networkStatusLabel } from '../channels/NetworkStatusChip';
import React, { useState } from 'react';
import { Alert, MenuItem, TextField, Typography } from '@mui/material';
import { useAcestreamChannel } from '../../hooks/useChannels';
import { useTVChannel } from '../../hooks/useTVChannels';
import { useNow } from '../../hooks/useNow';
import StreamPlayerDialog, { type StreamPlayerDialogProps } from './StreamPlayerDialog';
import ChannelGuide from './ChannelGuide';
import PlayOnMenu from './PlayOnMenu';
import { formatBitrate } from '../../utils/format';

interface ChannelPlayerDialogProps extends Omit<StreamPlayerDialogProps, 'extraActions' | 'details'> {
  tvChannelId?: number;
}

/** Preserve TV context when changing streams; a raw ID can discover its assigned channel. */
const OpenChannelPlayer: React.FC<ChannelPlayerDialogProps> = (props) => {
  const [selectedId, setSelectedId] = useState(props.contentId);
  const stream = useAcestreamChannel(props.contentId ?? '', { enabled: !props.tvChannelId && Boolean(props.contentId), retry: false });
  const tv = useTVChannel(props.tvChannelId ?? stream.data?.tv_channel_id ?? 0);
  const now = useNow();
  const channel = tv.data;
  return <StreamPlayerDialog {...props} contentId={selectedId} title={channel?.name ?? props.title}
    extraActions={selectedId ? <PlayOnMenu contentId={selectedId} title={channel?.name ?? props.title} /> : undefined}
    details={<>
      {tv.isError ? <Alert severity="warning">Channel details are unavailable. You can still play this stream.</Alert> : null}
      {channel ? <>
        <TextField select fullWidth label="Stream" value={selectedId ?? ''} onChange={(event) => setSelectedId(event.target.value)}
          helperText="Default order: online status, then available logo and EPG metadata. Picture quality and buffering are not measured.">
          {!channel.acestream_channels.some((item) => item.id === selectedId) && selectedId ? <MenuItem value={selectedId}>Opened stream · {selectedId}</MenuItem> : null}
          {channel.acestream_channels.map((item, index) => <MenuItem key={item.id} value={item.id} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere' }}>
            {index + 1}. {item.name} · {networkStatusLabel(item.network_status)} · {item.is_online === true ? 'Signal verified' : item.is_online === false ? 'No signal verified' : 'Signal not checked'} · {item.id.slice(0, 8)}{item.bitrate_bps ? ` · ${formatBitrate(item.bitrate_bps)}` : ''}{item.audio_tracks?.length ? ` · ${item.audio_tracks.length} audio track${item.audio_tracks.length === 1 ? '' : 's'}` : ''}
          </MenuItem>)}
        </TextField>
        <Typography component="h3" variant="h6">Schedule</Typography>
        <ChannelGuide channel={channel} now={now} />
      </> : null}
    </>} />;
};

const ChannelPlayerDialog: React.FC<ChannelPlayerDialogProps> = (props) => props.open
  ? <OpenChannelPlayer key={`${props.tvChannelId ?? ''}:${props.contentId}`} {...props} /> : null;
export default ChannelPlayerDialog;

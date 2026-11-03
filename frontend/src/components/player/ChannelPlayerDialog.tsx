import RecordButton from '../recordings/RecordButton';
import React, { useState } from 'react';
import { Alert } from '@mui/material';
import { useAcestreamChannel } from '../../hooks/useChannels';
import { useTVChannel } from '../../hooks/useTVChannels';
import { useNow } from '../../hooks/useNow';
import StreamPlayerDialog, { type StreamPlayerDialogProps } from './StreamPlayerDialog';
import ChannelGuide from './ChannelGuide';
import PlayOnMenu from './PlayOnMenu';
import SourceChips from './SourceChips';

interface ChannelPlayerDialogProps extends Omit<StreamPlayerDialogProps, 'extraActions' | 'details' | 'schedule' | 'sources'> {
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
    extraActions={<>{channel ? <RecordButton channelId={channel.id} channelName={channel.name} disabled={!channel.is_active || !channel.acestream_channels.some(stream => stream.is_active)} /> : null}{selectedId && !selectedId.startsWith('url:') ? <PlayOnMenu contentId={selectedId} title={channel?.name ?? props.title} /> : null}</>}
    schedule={channel ? <ChannelGuide channel={channel} now={now} /> : undefined}
    sources={channel ? <SourceChips streams={channel.acestream_channels} selectedId={selectedId} onSelect={setSelectedId} /> : undefined}
    details={tv.isError ? <Alert severity="warning">Channel details are unavailable. You can still play this stream.</Alert> : undefined} />;
};

const ChannelPlayerDialog: React.FC<ChannelPlayerDialogProps> = (props) => props.open
  ? <OpenChannelPlayer key={`${props.tvChannelId ?? ''}:${props.contentId}`} {...props} /> : null;
export default ChannelPlayerDialog;

import React from 'react';
import { Alert, Chip, List, ListItem, ListItemText, Stack, Typography } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import InlineStatusNotice from '../state/InlineStatusNotice';
import { useActiveStreams, usePlayerCapabilities } from '../../hooks/usePlayer';
import type { ActiveStream } from '../../services/playerService';
import { formatRelativeTime } from '../../utils/format';
import { getErrorMessage } from '../../utils/errorUtils';

/** The chip each stream earns. Relays only ever stream — they exist while bytes move. */
const STATE_LABEL: Record<ActiveStream['state'], string> = {
  starting: 'Starting',
  ready: 'Playing',
  error: 'Failed',
  stopped: 'Stopped',
  streaming: 'Streaming',
};

/** First 8 characters of the id, for a channel this server has no name for. */
const shortId = (contentId: string): string => `${contentId.slice(0, 8)}…`;

/** What to call a stream: its channel name, or the head of the id when we know no name. */
const streamTitle = (stream: ActiveStream): string => stream.channel_name ?? `Unnamed channel ${shortId(stream.content_id)}`;

/** Where a relay's bytes are going: "tuner:192.168.1.5" is one client's address. */
const relayClient = (label: string | null): string => (label ? label.replace(/^tuner:/, '') : 'unknown address');

/** The facts line under a stream's name. */
const streamFacts = (stream: ActiveStream): string => {
  if (stream.kind === 'relay') {
    return `Media server or player at ${relayClient(stream.client_label)} · started ${formatRelativeTime(stream.started_at)}`;
  }
  const viewers = `${stream.viewers} ${stream.viewers === 1 ? 'viewer' : 'viewers'}`;
  return stream.peers === null ? `In a browser · ${viewers}` : `In a browser · ${viewers} · ${stream.peers} peers`;
};

/** ffmpeg availability and everything the server is streaming right now. */
const WebPlayerSection: React.FC = () => {
  const { data: caps, isError: capsFailed, error: capsError } = usePlayerCapabilities();
  const { data: active, isError: streamsFailed, error: streamsError } = useActiveStreams();
  const list = active?.streams ?? [];

  // Never state a capability we could not read: without an answer the line says
  // it is still checking, and a failed read says so with the reason.
  const ffmpegLine = (): React.ReactNode => {
    if (capsFailed) {
      return <InlineStatusNotice severity="error" title="Unable to check the web player" description={getErrorMessage(capsError)} />;
    }
    if (!caps) {
      return (
        <Typography variant="body2" color="text.secondary">
          Checking ffmpeg…
        </Typography>
      );
    }
    if (!caps.ffmpeg_available) {
      return (
        <Alert severity="warning">
          ffmpeg is not available on this server, so channels cannot play in the browser. Set FFMPEG_BINARY_PATH or use the bundled image.
        </Alert>
      );
    }
    return (
      <Typography variant="body2" color="text.secondary">
        ffmpeg {caps.ffmpeg_path ? `at ${caps.ffmpeg_path}` : 'ready'} · up to {caps.max_sessions} channels at once
      </Typography>
    );
  };

  return (
    <ContentSection
      title="Web player"
      description="Channels play in the browser through a small server-side conversion (video copied, audio re-encoded). Media servers and remote players are relayed as they are."
    >
      <Stack spacing={1.5}>
        {ffmpegLine()}
        {streamsFailed ? (
          <InlineStatusNotice severity="error" title="Unable to load what is playing" description={getErrorMessage(streamsError)} />
        ) : list.length === 0 ? (
          <Typography variant="body2">Nothing is playing right now.</Typography>
        ) : (
          <List dense>
            {list.map((stream) => (
              <ListItem key={`${stream.kind}-${stream.id}`} secondaryAction={<Chip size="small" label={STATE_LABEL[stream.state]} />}>
                <ListItemText
                  primary={streamTitle(stream)}
                  secondary={
                    <>
                      {streamFacts(stream)}
                      <Typography component="span" variant="caption" sx={{ display: 'block', fontFamily: 'monospace', overflowWrap: 'anywhere' }}>
                        {stream.content_id}
                      </Typography>
                    </>
                  }
                  secondaryTypographyProps={{ component: 'div' }}
                />
              </ListItem>
            ))}
          </List>
        )}
      </Stack>
    </ContentSection>
  );
};

export default WebPlayerSection;

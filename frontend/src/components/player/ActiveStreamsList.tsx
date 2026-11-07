import React from 'react';
import { Box, Chip, List, ListItem, Typography } from '@mui/material';
import type { ActiveStream } from '../../services/playerService';
import { formatRelativeTime } from '../../utils/format';

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
const streamTitle = (stream: ActiveStream): string => stream.channel_name ?? `Unnamed stream ${shortId(stream.content_id)}`;

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

/** Read-only presentation: rendering never joins or keeps a session alive. */
export default function ActiveStreamsList({ streams, showContentId = false }: { streams: ActiveStream[]; showContentId?: boolean }) {
  if (!streams.length) return <Typography variant="body2">Nothing is playing through this app right now.</Typography>;
  return <List disablePadding aria-label="Playback sessions">
    {streams.map(stream => <ListItem key={`${stream.kind}-${stream.id}`} disableGutters sx={{ alignItems: 'flex-start', gap: 2, py: 1.5, borderBottom: 1, borderColor: 'divider' }}>
      <Box sx={{ flex: 1, minWidth: 0, overflowWrap: 'anywhere' }}>
        <Typography fontWeight={600}>{streamTitle(stream)}</Typography>
        <Typography variant="body2" color="text.secondary">{streamFacts(stream)}</Typography>
        {showContentId ? <Typography variant="caption" sx={{ overflowWrap: 'anywhere' }}>{stream.content_id}</Typography> : null}
      </Box>
      <Chip size="small" variant="outlined" label={STATE_LABEL[stream.state]} sx={{ flexShrink: 0 }} />
    </ListItem>)}
  </List>;
}

import React from 'react';
import { Alert, Chip, List, ListItem, ListItemText, Stack, Typography } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import InlineStatusNotice from '../state/InlineStatusNotice';
import { usePlayerCapabilities, usePlayerSessions } from '../../hooks/usePlayer';
import { getErrorMessage } from '../../utils/errorUtils';

/** ffmpeg availability and what is playing in browsers right now. */
const WebPlayerSection: React.FC = () => {
  const { data: caps, isError: capsFailed, error: capsError } = usePlayerCapabilities();
  const { data: sessions, isError: sessionsFailed, error: sessionsError } = usePlayerSessions();
  const list = sessions?.sessions ?? [];

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
      description="Channels play in the browser through a small server-side conversion (video copied, audio re-encoded)."
    >
      <Stack spacing={1.5}>
        {ffmpegLine()}
        {sessionsFailed ? (
          <InlineStatusNotice severity="error" title="Unable to load what is playing" description={getErrorMessage(sessionsError)} />
        ) : list.length === 0 ? (
          <Typography variant="body2">Nothing is playing right now.</Typography>
        ) : (
          <List dense>
            {list.map((session) => (
              <ListItem key={session.id} secondaryAction={<Chip size="small" label={session.state} />}>
                <ListItemText
                  primary={session.content_id}
                  secondary={`${session.viewers} viewer${session.viewers === 1 ? '' : 's'}${session.stats ? ` · ${session.stats.peers} peers` : ''}`}
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

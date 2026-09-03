import React from 'react';
import { Alert, Chip, List, ListItem, ListItemText, Stack, Typography } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import { usePlayerCapabilities, usePlayerSessions } from '../../hooks/usePlayer';

/** ffmpeg availability and what is playing in browsers right now. */
const WebPlayerSection: React.FC = () => {
  const { data: caps } = usePlayerCapabilities();
  const { data: sessions } = usePlayerSessions();
  const list = sessions?.sessions ?? [];
  return (
    <ContentSection
      title="Web player"
      description="Channels play in the browser through a small server-side conversion (video copied, audio re-encoded)."
    >
      <Stack spacing={1.5}>
        {caps && !caps.ffmpeg_available ? (
          <Alert severity="warning">
            ffmpeg is not available on this server, so channels cannot play in the browser. Set FFMPEG_BINARY_PATH or use the bundled image.
          </Alert>
        ) : (
          <Typography variant="body2" color="text.secondary">
            ffmpeg {caps?.ffmpeg_path ? `at ${caps.ffmpeg_path}` : 'ready'} · up to {caps?.max_sessions ?? '…'} channels at once
          </Typography>
        )}
        {list.length === 0 ? (
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

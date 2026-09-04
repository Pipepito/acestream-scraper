import React, { useState } from 'react';
import { Alert, Box, Snackbar } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import StatusLine from '../components/StatusLine';
import PublicAddressSection from '../components/integrations/PublicAddressSection';
import WebPlayerSection from '../components/integrations/WebPlayerSection';
import RemotePlayersSection from '../components/integrations/RemotePlayersSection';
import MediaServersSection from '../components/integrations/MediaServersSection';
import type { PlayerNotify } from '../components/player/playerCopy';
import { usePublicUrl } from '../hooks/useSystemServices';
import { useActiveStreams } from '../hooks/usePlayer';
import { useRemotePlayers } from '../hooks/useRemotePlayers';
import { useMediaServers } from '../hooks/useMediaServers';

type Feedback = { message: string; severity: 'success' | 'warning' | 'error' } | null;

/** Play channels in the browser and on players in your network. */
const Integrations: React.FC = () => {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const notify: PlayerNotify = (message, severity) => setFeedback({ message, severity });
  const { data: publicUrl } = usePublicUrl();
  const { data: players } = useRemotePlayers();
  const { data: servers } = useMediaServers();
  const { data: active } = useActiveStreams();

  return (
    <Box>
      <PageHeader
        title="Integrations"
        subtitle="Play channels in the browser, on players in your network, and in Jellyfin or Plex."
      />
      <StatusLine
        aria-label="Integration summary"
        items={[
          {
            label: 'Public address',
            value: publicUrl?.url ?? '…',
            tone: publicUrl && publicUrl.warnings.length > 0 ? 'warning' : 'default',
          },
          { label: 'Players', value: players ? String(players.length) : '…' },
          { label: 'Media servers', value: servers ? String(servers.length) : '…' },
          { label: 'Active streams', value: active ? String(active.streams.length) : '…' },
        ]}
      />
      <PublicAddressSection notify={notify} />
      <WebPlayerSection />
      <RemotePlayersSection notify={notify} />
      <MediaServersSection notify={notify} />
      <Snackbar
        open={feedback !== null}
        autoHideDuration={5000}
        onClose={() => setFeedback(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setFeedback(null)} severity={feedback?.severity ?? 'success'} variant="filled" sx={{ width: '100%' }}>
          {feedback?.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Integrations;

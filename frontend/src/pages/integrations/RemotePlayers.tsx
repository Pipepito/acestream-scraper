import React from 'react';
import { Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import RemotePlayersSection from '../../components/integrations/RemotePlayersSection';
import { useRemotePlayers } from '../../hooks/useRemotePlayers';

export default function RemotePlayers() {
  const players = useRemotePlayers();
  return <IntegrationPage title="Remote players" summary={[
    { label: 'Players', value: players.error ? 'Unavailable' : players.data?.length ?? 'Loading…' },
  ]}>{notify => <>
    <RemotePlayersSection notify={notify} />
    <Button component={RouterLink} to="/integrations/public-address">Configure public address</Button>
  </>}</IntegrationPage>;
}

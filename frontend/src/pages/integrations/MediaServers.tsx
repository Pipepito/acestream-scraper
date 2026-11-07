import React from 'react';
import { Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import MediaServersSection from '../../components/integrations/MediaServersSection';
import { useMediaServers } from '../../hooks/useMediaServers';

export default function MediaServers() {
  const servers = useMediaServers();
  return <IntegrationPage title="Media servers" summary={[
    { label: 'Media servers', value: servers.error ? 'Unavailable' : servers.data?.length ?? 'Loading…' },
  ]}>{notify => <>
    <MediaServersSection notify={notify} />
    <Button component={RouterLink} to="/integrations/public-address">Configure public address</Button>
  </>}</IntegrationPage>;
}

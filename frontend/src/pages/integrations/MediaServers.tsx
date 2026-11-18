import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import MediaServersSection from '../../components/integrations/MediaServersSection';
import { useMediaServers } from '../../hooks/useMediaServers';

export default function MediaServers() {
  const tUi = useUiText();
  const servers = useMediaServers();
  return <IntegrationPage title={tUi("Media servers")} summary={[
    { label: uiText("Media servers"), value: servers.error ? uiText("Unavailable") : servers.data?.length ?? 'Loading…' },
  ]}>{notify => <>
    <MediaServersSection notify={notify} />
    <Button component={RouterLink} to="/integrations/public-address">{tUi("Configure public address")}</Button>
  </>}</IntegrationPage>;
}

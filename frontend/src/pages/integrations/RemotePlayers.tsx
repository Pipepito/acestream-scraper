import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Button } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import RemotePlayersSection from '../../components/integrations/RemotePlayersSection';
import { useRemotePlayers } from '../../hooks/useRemotePlayers';

export default function RemotePlayers() {
  const tUi = useUiText();
  const players = useRemotePlayers();
  return <IntegrationPage title={tUi("Remote players")} summary={[
    { label: uiText("Players"), value: players.error ? uiText("Unavailable") : players.data?.length ?? 'Loading…' },
  ]}>{notify => <>
    <RemotePlayersSection notify={notify} />
    <Button component={RouterLink} to="/integrations/public-address">{tUi("Configure public address")}</Button>
  </>}</IntegrationPage>;
}

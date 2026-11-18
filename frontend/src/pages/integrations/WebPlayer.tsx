import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import WebPlayerSection from '../../components/integrations/WebPlayerSection';
import { useActiveStreams } from '../../hooks/usePlayer';

export default function WebPlayer() {
  const tUi = useUiText();
  const streams = useActiveStreams();
  return <IntegrationPage title={tUi("Web player")} summary={[
    { label: uiText("Sessions"), value: streams.error ? uiText("Unavailable") : streams.data?.streams.length ?? 'Loading…' },
  ]}>{() => <WebPlayerSection />}</IntegrationPage>;
}

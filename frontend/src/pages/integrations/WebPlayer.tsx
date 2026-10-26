import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import WebPlayerSection from '../../components/integrations/WebPlayerSection';
import { useActiveStreams } from '../../hooks/usePlayer';

export default function WebPlayer() {
  const streams = useActiveStreams();
  return <IntegrationPage title="Web player" summary={[
    { label: 'Sessions', value: streams.error ? 'Unavailable' : streams.data?.streams.length ?? 'Loading…' },
  ]}>{() => <WebPlayerSection />}</IntegrationPage>;
}

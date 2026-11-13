import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import PublicAddressSection from '../../components/integrations/PublicAddressSection';
import { usePublicUrl } from '../../hooks/useSystemServices';

export default function PublicAddress() {
  const tUi = useUiText();
  const address = usePublicUrl();
  return <IntegrationPage title={tUi("Public address")} summary={[
    { label: uiText("Address source"), value: address.error ? uiText("Unavailable") : !address.data ? uiText("Loading…") : address.data.source === 'setting' ? uiText("Saved address") : address.data.source === 'forwarded' ? uiText("Proxy headers") : uiText("Browser request") },
  ]}>{notify => <PublicAddressSection notify={notify} />}</IntegrationPage>;
}

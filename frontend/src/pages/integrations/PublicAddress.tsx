import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import PublicAddressSection from '../../components/integrations/PublicAddressSection';
import { usePublicUrl } from '../../hooks/useSystemServices';

export default function PublicAddress() {
  const address = usePublicUrl();
  return <IntegrationPage title="Public address" summary={[
    { label: 'Address source', value: address.error ? 'Unavailable' : !address.data ? 'Loading…' : address.data.source === 'setting' ? 'Saved address' : address.data.source === 'forwarded' ? 'Proxy headers' : 'Browser request' },
  ]}>{notify => <PublicAddressSection notify={notify} />}</IntegrationPage>;
}

import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import NotificationsSection from '../../components/NotificationsSection';
import { useTranslation } from 'react-i18next';

export default function Notifications() {
  const { t } = useTranslation();
  return <IntegrationPage title={t('notifications')}>{notify => <NotificationsSection notify={notify} />}</IntegrationPage>;
}

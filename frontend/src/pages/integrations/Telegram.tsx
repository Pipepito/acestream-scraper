import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import TelegramSection from '../../components/integrations/TelegramSection';

export default function Telegram() {
  return <IntegrationPage title="Telegram">{() => <TelegramSection />}</IntegrationPage>;
}

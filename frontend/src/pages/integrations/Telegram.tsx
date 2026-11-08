import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import TelegramSection from '../../components/integrations/TelegramSection';

export default function Telegram() {
  const tUi = useUiText();
  return <IntegrationPage title={tUi("Telegram")}>{() => <TelegramSection />}</IntegrationPage>;
}

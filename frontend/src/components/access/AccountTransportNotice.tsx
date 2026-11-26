import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Alert } from '@mui/material';
import { useAccess } from './AccessContext';

export default function AccountTransportNotice() {
  const tUi = useUiText();
  const transport = useAccess()?.status.account_transport;
  if (transport === 'blocked') return <Alert severity="warning">{tUi("To use accounts, open HTTPS or the server’s private IP address from your home network.")}</Alert>;
  if (transport === 'local_http') return <Alert severity="info">{tUi("Accounts are available on this local connection. HTTP is not encrypted; use it only on a home network you trust.")}</Alert>;
  return null;
}

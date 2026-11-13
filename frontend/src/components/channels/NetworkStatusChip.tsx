import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Chip, Tooltip } from '@mui/material';

export const networkStatusLabel = (status?: string | null): string =>
  status === 'found' ? uiText("ID found") : status === 'not_found' ? uiText("ID not found") : uiText("ID unverified");

const NetworkStatusChip: React.FC<{ status?: string | null }> = ({ status }) => { const tUi = useUiText(); return (
  <Tooltip title={tUi("Engine lookup at the last check. A timeout does not prove an ID no longer exists.")}>
    <Chip size="small" variant="outlined" label={networkStatusLabel(status)} />
  </Tooltip>
); };
export default NetworkStatusChip;

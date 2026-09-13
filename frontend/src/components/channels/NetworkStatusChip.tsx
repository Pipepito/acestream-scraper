import React from 'react';
import { Chip, Tooltip } from '@mui/material';

export const networkStatusLabel = (status?: string | null): string =>
  status === 'found' ? 'ID found' : status === 'not_found' ? 'ID not found' : 'ID unverified';

const NetworkStatusChip: React.FC<{ status?: string | null }> = ({ status }) => (
  <Tooltip title="Engine lookup at the last check. A timeout does not prove an ID no longer exists.">
    <Chip size="small" variant="outlined" label={networkStatusLabel(status)} />
  </Tooltip>
);
export default NetworkStatusChip;

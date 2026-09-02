import React from 'react';
import { Chip, useTheme } from '@mui/material';

export interface OnlineChipProps {
  isOnline: boolean | null | undefined;
}

/** Fixed-width online/offline/unknown chip so rows line up. */
const OnlineChip: React.FC<OnlineChipProps> = ({ isOnline }) => {
  const theme = useTheme();
  const tone = isOnline === true ? theme.appTokens.status.success : isOnline === false ? theme.appTokens.status.error : null;
  const label = isOnline === true ? 'Online' : isOnline === false ? 'Offline' : 'Unknown';
  return (
    <Chip
      label={label}
      size="small"
      variant="outlined"
      sx={{
        minWidth: 80,
        justifyContent: 'center',
        fontWeight: 600,
        ...(tone ? { borderColor: tone.border, backgroundColor: tone.bg, color: tone.text } : {}),
      }}
    />
  );
};

export default OnlineChip;

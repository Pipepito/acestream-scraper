import React from 'react';
import { Chip, useTheme } from '@mui/material';

export interface OnlineChipProps {
  isOnline: boolean | null | undefined;
}

/** Keep the full signal status readable, including in narrow cards. */
const OnlineChip: React.FC<OnlineChipProps> = ({ isOnline }) => {
  const theme = useTheme();
  const tone = isOnline === true ? theme.appTokens.status.success : isOnline === false ? theme.appTokens.status.error : null;
  const label = isOnline === true ? 'Signal verified' : isOnline === false ? 'No signal verified' : 'Not checked';
  return (
    <Chip
      label={label}
      size="small"
      variant="outlined"
      sx={{
        minWidth: 80,
        height: 'auto',
        minHeight: 24,
        '& .MuiChip-label': { whiteSpace: 'normal', py: 0.25 },
        justifyContent: 'center',
        fontWeight: 600,
        ...(tone ? { borderColor: tone.border, backgroundColor: tone.bg, color: tone.text } : {}),
      }}
    />
  );
};

export default OnlineChip;

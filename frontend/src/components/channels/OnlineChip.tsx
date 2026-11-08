import { useUiText } from '../../i18n/useUiText';
import { uiText } from '../../i18n/text';
import React from 'react';
import { Chip, useTheme } from '@mui/material';

export interface OnlineChipProps {
  isOnline: boolean | null | undefined;
}

/** Keep the full signal status readable, including in narrow cards. */
const OnlineChip: React.FC<OnlineChipProps> = ({ isOnline }) => {
  useUiText();
  const theme = useTheme();
  const tone = isOnline === true ? theme.appTokens.status.success : isOnline === false ? theme.appTokens.status.error : null;
  const label = isOnline === true ? uiText("Signal verified") : isOnline === false ? uiText("No signal verified") : uiText("Not checked");
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

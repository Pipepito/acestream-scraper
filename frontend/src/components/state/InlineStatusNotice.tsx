import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import type { AppStatusToken } from '../../theme.d';

export type InlineStatusSeverity = 'error' | 'warning' | 'info' | 'success';

interface InlineStatusNoticeProps {
  severity: InlineStatusSeverity;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

const getRole = (severity: InlineStatusSeverity) =>
  severity === 'error' || severity === 'warning' ? 'alert' : 'status';

const InlineStatusNotice: React.FC<InlineStatusNoticeProps> = ({ severity, title, description, action }) => {
  const theme = useTheme();
  const tokens: AppStatusToken = theme.appTokens.status[severity];

  return (
    <Box
      role={getRole(severity)}
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', sm: 'row' },
        alignItems: { xs: 'flex-start', sm: 'center' },
        gap: 1.5,
        p: 1.5,
        border: '1px solid',
        borderColor: tokens.border,
        borderRadius: theme.appTokens.layout.cardRadius,
        backgroundColor: tokens.bg,
        color: tokens.text,
      }}
    >
      <Box data-testid="inline-status-notice-text" sx={{ minWidth: 0, flex: '1 1 auto' }}>
        <Typography variant="sectionTitle" component="p" sx={{ color: 'inherit', fontSize: '1rem', overflowWrap: 'break-word' }}>
          {title}
        </Typography>
        {description ? (
          <Typography
            variant="helperText"
            sx={{ mt: 0.5, color: 'inherit', minWidth: 0, overflowWrap: 'break-word' }}
          >
            {description}
          </Typography>
        ) : null}
      </Box>
      {action ? (
        <Box
          data-testid="inline-status-notice-action"
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1,
            width: { xs: '100%', sm: 'auto' },
            minWidth: 0,
            flexShrink: 0,
          }}
        >
          {action}
        </Box>
      ) : null}
    </Box>
  );
};

export default InlineStatusNotice;

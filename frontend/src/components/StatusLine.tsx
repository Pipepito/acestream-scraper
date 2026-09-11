import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';

export type StatusTone = 'default' | 'success' | 'warning' | 'error';

export interface StatusItem {
  label: string;
  value: React.ReactNode;
  tone?: StatusTone;
}

export interface StatusLineProps {
  items: StatusItem[];
  action?: React.ReactNode;
  'aria-label'?: string;
}

/**
 * One compact strip of labelled facts ("Sources 2 enabled · Last scrape 12 min ago").
 * Replaces the per-page hero: it only shows state, never prose.
 */
const StatusLine: React.FC<StatusLineProps> = ({ items, action, 'aria-label': ariaLabel }) => {
  const theme = useTheme();
  const toneColor: Record<StatusTone, string> = {
    default: theme.palette.text.primary,
    success: theme.palette.success.main,
    warning: theme.palette.warning.main,
    error: theme.palette.error.main,
  };
  return (
    <Box
      role="status"
      aria-label={ariaLabel}
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        columnGap: 2,
        rowGap: 0.5,
        px: 1.5,
        py: 1,
        mb: 2,
        borderRadius: 1.5,
        border: `1px solid ${theme.appTokens.surface.border}`,
        backgroundColor: theme.appTokens.surface.raised,
      }}
    >
      {items.map((item, index) => (
        <React.Fragment key={item.label}>
          {index > 0 ? (
            <Typography component="span" aria-hidden sx={{ color: 'text.disabled' }}>
              ·
            </Typography>
          ) : null}
          <Typography component="span" variant="body2" sx={{ display: 'inline-flex', gap: 0.75, alignItems: 'baseline' }}>
            <Typography component="span" variant="caption" sx={{ color: 'text.secondary', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              {item.label}
            </Typography>
            <Typography component="span" variant="body2" data-tone={item.tone ?? 'default'} sx={{ fontWeight: 600, color: toneColor[item.tone ?? 'default'] }}>
              {item.value}
            </Typography>
          </Typography>
        </React.Fragment>
      ))}
      {action ? <Box sx={{ ml: 'auto' }}>{action}</Box> : null}
    </Box>
  );
};

export default StatusLine;

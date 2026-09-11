import React, { useId } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

export interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action }) => {
  const theme = useTheme();
  const titleId = useId();

  return (
    <Paper
      component="section"
      aria-labelledby={titleId}
      variant="outlined"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: 1.25,
        p: 2,
        borderColor: theme.appTokens.surface.border,
        backgroundColor: theme.appTokens.surface.raised,
        borderRadius: theme.appTokens.layout.cardRadius,
        boxShadow: 'none',
        maxWidth: 480,
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Typography id={titleId} variant="sectionTitle" component="h2" sx={{ overflowWrap: 'break-word' }}>
          {title}
        </Typography>
        <Typography variant="helperText" color="text.secondary" sx={{ mt: 0.75, minWidth: 0, overflowWrap: 'break-word' }}>
          {description}
        </Typography>
      </Box>
      {action ? (
        <Box
          data-testid="empty-state-action"
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1,
            width: '100%',
            minWidth: 0,
          }}
        >
          {action}
        </Box>
      ) : null}
    </Paper>
  );
};

export default EmptyState;

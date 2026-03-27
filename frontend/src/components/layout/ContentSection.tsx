import React, { useId } from 'react';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

interface ContentSectionProps {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

const ContentSection: React.FC<ContentSectionProps> = ({ title, description, actions, children }) => {
  const theme = useTheme();
  const titleId = useId();

  return (
    <Paper
      component="section"
      aria-labelledby={title ? titleId : undefined}
      variant="outlined"
      sx={{
        p: { xs: 2, sm: theme.appTokens.layout.panelPadding },
        mb: theme.appTokens.layout.pageGap,
        minWidth: 0,
        bgcolor: theme.appTokens.surface.raised,
        borderColor: theme.appTokens.surface.border,
        boxShadow: 'none',
      }}
    >
      {title ? (
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          alignItems="flex-start"
          justifyContent="space-between"
          spacing={1.5}
          sx={{ mb: theme.appTokens.layout.sectionGap, minWidth: 0 }}
        >
          <Box data-testid="content-section-copy" sx={{ minWidth: 0, flex: '1 1 auto', overflowWrap: 'break-word' }}>
            <Typography id={titleId} variant="sectionTitle" component="h2" color="text.primary" sx={{ overflowWrap: 'break-word' }}>
              {title}
            </Typography>
            {description ? (
              <Typography
                variant="helperText"
                color="text.secondary"
                sx={{ mt: 0.75, overflowWrap: 'break-word' }}
              >
                {description}
              </Typography>
            ) : null}
          </Box>
          {actions ? (
            <Box
              data-testid="content-section-actions"
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: { xs: 'flex-start', md: 'flex-end' },
                alignItems: 'center',
                gap: 1,
                minWidth: 0,
                flexShrink: 0,
                width: { xs: '100%', md: 'auto' },
                alignSelf: { xs: 'stretch', md: 'flex-start' },
              }}
            >
              {actions}
            </Box>
          ) : null}
        </Stack>
      ) : null}
      {children}
    </Paper>
  );
};

export default ContentSection;

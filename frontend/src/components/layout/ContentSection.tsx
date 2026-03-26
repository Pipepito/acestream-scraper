import React from 'react';
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

  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 2, sm: theme.appTokens.layout.panelPadding },
        mb: theme.appTokens.layout.pageGap,
        bgcolor: theme.appTokens.surface.raised,
        borderColor: theme.appTokens.surface.border,
        boxShadow: theme.appTokens.layout.elevatedShadow,
      }}
    >
      {title ? (
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          alignItems={{ xs: 'flex-start', md: 'center' }}
          justifyContent="space-between"
          spacing={1.5}
          sx={{ mb: theme.appTokens.layout.sectionGap }}
        >
          <Box sx={{ minWidth: 0, flex: '1 1 auto' }}>
            <Typography variant="sectionTitle" component="h2" color="text.primary">
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
          {actions ? <Box sx={{ flexShrink: 0, width: { xs: '100%', md: 'auto' } }}>{actions}</Box> : null}
        </Stack>
      ) : null}
      {children}
    </Paper>
  );
};

export default ContentSection;

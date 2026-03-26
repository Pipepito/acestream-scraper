import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, subtitle, actions }) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        justifyContent: 'space-between',
        alignItems: { xs: 'flex-start', md: 'center' },
        gap: theme.appTokens.layout.sectionGap,
        mb: theme.appTokens.layout.pageGap,
      }}
    >
      <Box sx={{ minWidth: 0, flex: '1 1 auto' }}>
        <Typography variant="pageTitle" component="h1" color="text.primary">
          {title}
        </Typography>
        {subtitle ? (
          <Typography
            variant="helperText"
            color="text.secondary"
            sx={{ mt: 1, maxWidth: 720, overflowWrap: 'break-word' }}
          >
            {subtitle}
          </Typography>
        ) : null}
      </Box>
      {actions ? (
        <Box sx={{ width: { xs: '100%', md: 'auto' }, flexShrink: 0 }}>
          {actions}
        </Box>
      ) : null}
    </Box>
  );
};

export default PageHeader;

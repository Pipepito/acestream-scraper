import React, { useId } from 'react';
import Paper from '@mui/material/Paper';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

interface ContentSectionProps {
  title?: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  wideLayout?: 'default' | 'primary' | 'supporting';
}

const ContentSection: React.FC<ContentSectionProps> = ({ title, description, actions, children, wideLayout = 'default' }) => {
  const theme = useTheme();
  const titleId = useId();
  const layout = theme.appTokens.layout.shell;
  const isPhone = useMediaQuery(`(max-width:${layout.phoneMaxWidth}px)`);
  const isDesktop = useMediaQuery(`(min-width:${layout.desktopMinWidth}px)`);
  const isWideDesktop = useMediaQuery(`(min-width:${layout.wideMinWidth}px)`);
  const wideLayoutStyles =
    isWideDesktop && wideLayout !== 'default'
      ? {
          gridArea: wideLayout,
          alignSelf: 'start',
        }
      : undefined;

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
        width: '100%',
        height: '100%',
        ...wideLayoutStyles,
      }}
    >
      {title ? (
        <Stack
          direction={isDesktop ? 'row' : 'column'}
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
                flexDirection: isPhone ? 'column' : 'row',
                justifyContent: isDesktop ? 'flex-end' : 'flex-start',
                alignItems: isPhone ? 'stretch' : 'center',
                gap: 1,
                minWidth: 0,
                flexShrink: 0,
                width: isDesktop ? 'auto' : '100%',
                alignSelf: isDesktop ? 'flex-start' : 'stretch',
                justifySelf: isDesktop ? 'end' : 'stretch',
                '& > *': {
                  minWidth: 0,
                  maxWidth: '100%',
                  width: isPhone ? '100%' : 'auto',
                },
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

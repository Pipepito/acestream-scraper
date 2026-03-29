import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  primaryActions?: React.ReactNode;
  actions?: React.ReactNode;
  wideActionsAlignment?: 'start' | 'end';
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  primaryActions,
  actions,
  wideActionsAlignment = 'end',
}) => {
  const theme = useTheme();
  const layout = theme.appTokens.layout.shell;
  const isPhone = useMediaQuery(`(max-width:${layout.phoneMaxWidth}px)`);
  const isDesktop = useMediaQuery(`(min-width:${layout.desktopMinWidth}px)`);
  const isWideDesktop = useMediaQuery(`(min-width:${layout.wideMinWidth}px)`);
  const groupedPrimaryActions = primaryActions ?? actions;
  const groupedSecondaryActions = primaryActions ? actions : null;
  const desktopActionAlignment = isWideDesktop ? wideActionsAlignment : 'end';
  const desktopJustifyContent = desktopActionAlignment === 'start' ? 'flex-start' : 'flex-end';
  const desktopJustifySelf = desktopActionAlignment === 'start' ? 'start' : 'end';

  return (
    <Box
      component="header"
      sx={{
        display: 'grid',
        gridTemplateColumns: isDesktop ? 'minmax(0, 1fr) auto' : '1fr',
        alignItems: 'flex-start',
        columnGap: theme.appTokens.layout.sectionGap,
        rowGap: theme.appTokens.layout.sectionGap,
        mb: theme.appTokens.layout.pageGap,
        width: '100%',
      }}
    >
      <Box data-testid="page-header-copy" sx={{ minWidth: 0, flex: '1 1 auto', overflowWrap: 'break-word' }}>
        <Typography variant="pageTitle" component="h1" color="text.primary" sx={{ overflowWrap: 'break-word' }}>
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
      {groupedPrimaryActions || groupedSecondaryActions ? (
        <Box
          data-testid="page-header-actions"
          sx={{
            display: 'flex',
            flexWrap: isPhone ? 'nowrap' : 'wrap',
            flexDirection: isPhone ? 'column' : 'row',
            justifyContent: isDesktop ? desktopJustifyContent : 'flex-start',
            alignItems: isPhone ? 'stretch' : 'center',
            gap: 1,
            minWidth: 0,
            width: isDesktop ? 'auto' : '100%',
            flexShrink: 0,
            alignSelf: isDesktop ? 'flex-start' : 'stretch',
            justifySelf: isDesktop ? desktopJustifySelf : 'stretch',
          }}
        >
          {groupedPrimaryActions ? (
            <Box
              data-testid="page-header-primary-actions"
              sx={{
                display: 'flex',
                flexWrap: isPhone ? 'nowrap' : 'wrap',
                flexDirection: isPhone ? 'column' : 'row',
                justifyContent: isDesktop ? desktopJustifyContent : 'flex-start',
                alignItems: isPhone ? 'stretch' : 'center',
                gap: 1,
                minWidth: 0,
                width: isPhone ? '100%' : 'auto',
                '& > *': {
                  minWidth: 0,
                  maxWidth: '100%',
                  width: isPhone ? '100%' : 'auto',
                },
              }}
            >
              {groupedPrimaryActions}
            </Box>
          ) : null}
          {groupedSecondaryActions ? (
            <Box
              data-testid="page-header-secondary-actions"
              sx={{
                display: 'flex',
                flexWrap: isPhone ? 'nowrap' : 'wrap',
                flexDirection: isPhone ? 'column' : 'row',
                justifyContent: isDesktop ? desktopJustifyContent : 'flex-start',
                alignItems: isPhone ? 'stretch' : 'center',
                gap: 1,
                minWidth: 0,
                width: isPhone ? '100%' : 'auto',
                '& > *': {
                  minWidth: 0,
                  maxWidth: '100%',
                  width: isPhone ? '100%' : 'auto',
                },
              }}
            >
              {groupedSecondaryActions}
            </Box>
          ) : null}
        </Box>
      ) : null}
    </Box>
  );
};

export default PageHeader;

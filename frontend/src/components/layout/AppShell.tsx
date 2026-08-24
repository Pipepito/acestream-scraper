import React from 'react';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import { useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import NavBar from '../NavBar';
import { getShellContentMaxWidth, getShellLayout } from '../../styles/layout';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const theme = useTheme();
  const layout = getShellLayout(theme);
  const isDesktop = useMediaQuery(`(min-width:${layout.desktopMinWidth}px)`);
  const isWideDesktop = useMediaQuery(`(min-width:${layout.wideMinWidth}px)`);
  const contentMaxWidth = getShellContentMaxWidth(theme, isWideDesktop ? 'wide' : 'standard');

  return (
    <Box data-testid="app-shell-root" sx={{ display: 'flex', minHeight: '100vh', minWidth: 0, bgcolor: theme.appTokens.surface.canvas }}>
      <NavBar drawerWidth={layout.navWidth} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          overflowX: 'hidden',
          width: isDesktop ? `calc(100% - ${layout.navWidth}px)` : '100%',
          px: layout.pagePaddingX,
          py: layout.pagePaddingY,
          bgcolor: theme.appTokens.surface.canvas,
          backgroundImage: theme.appTokens.shell.contentGlow,
          backgroundRepeat: 'no-repeat',
          backgroundSize: '100% 100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Toolbar />
        <Box
          data-testid="app-shell-content"
          sx={{
            maxWidth: contentMaxWidth,
            mr: 'auto',
            width: '100%',
            minWidth: 0,
            bgcolor: theme.appTokens.surface.raised,
            border: `1px solid ${theme.appTokens.surface.border}`,
            borderRadius: `calc(${theme.appTokens.layout.cardRadius}px + 6px)`,
            boxShadow: theme.appTokens.layout.elevatedShadow,
            px: { xs: 1.5, sm: 2.5, md: 3 },
            py: { xs: 2, sm: 2.5, md: 3 },
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default AppShell;

import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import { Link, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import NavBar from '../NavBar';
import { getShellContentMaxWidth, getShellLayout } from '../../styles/layout';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [navCollapsed, setNavCollapsed] = useState(false);
  const { pathname } = useLocation();
  const theme = useTheme();
  const layout = getShellLayout(theme);
  const isDesktop = !useMediaQuery(`(max-width:${layout.phoneMaxWidth}px)`);
  const isWideDesktop = useMediaQuery(`(min-width:${layout.wideMinWidth}px)`);
  const contentMaxWidth = getShellContentMaxWidth(theme, isWideDesktop ? 'wide' : 'standard');

  return (
    <Box data-testid="app-shell-root" sx={{ display: 'flex', minHeight: '100vh', minWidth: 0, bgcolor: theme.appTokens.surface.canvas }}>
      <Link href="#main-content" sx={{ position: 'fixed', top: -100, left: 16, zIndex: 1600, p: 1.5, bgcolor: 'background.paper', color: 'text.primary', '&:focus': { top: 8 } }}>Skip to content</Link>
      <NavBar drawerWidth={layout.navWidth} collapsed={navCollapsed} onToggleCollapsed={() => setNavCollapsed((value) => !value)} />
      <Box
        component="main"
        id="main-content"
        tabIndex={-1}
        sx={{
          flexGrow: 1,
          minWidth: 0,
          overflowX: 'hidden',
          width: isDesktop && !navCollapsed ? `calc(100% - ${layout.navWidth}px)` : '100%',
          px: { xs: 1.5, sm: layout.pagePaddingX },
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
            maxWidth: pathname === '/live-tv' ? 'none' : contentMaxWidth,
            mr: 'auto',
            width: '100%',
            minWidth: 0,
            bgcolor: { xs: 'transparent', sm: theme.appTokens.surface.raised },
            border: { xs: 0, sm: `1px solid ${theme.appTokens.surface.border}` },
            borderRadius: `calc(${theme.appTokens.layout.cardRadius}px + 6px)`,
            boxShadow: { xs: 'none', sm: theme.appTokens.layout.elevatedShadow },
            px: { xs: 0, sm: 2.5, md: 3 },
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

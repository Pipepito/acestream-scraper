import React from 'react';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import { useTheme } from '@mui/material/styles';
import NavBar from '../NavBar';
import { getShellLayout } from '../../styles/layout';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const theme = useTheme();
  const layout = getShellLayout(theme);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', minWidth: 0, bgcolor: theme.appTokens.surface.canvas }}>
      <NavBar drawerWidth={layout.navWidth} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          overflowX: 'hidden',
          width: { sm: `calc(100% - ${layout.navWidth}px)` },
          px: layout.pagePaddingX,
          py: layout.pagePaddingY,
          bgcolor: theme.appTokens.surface.canvas,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Toolbar />
        <Box sx={{ maxWidth: layout.contentMaxWidth, mr: 'auto', width: '100%', minWidth: 0 }}>{children}</Box>
      </Box>
    </Box>
  );
};

export default AppShell;

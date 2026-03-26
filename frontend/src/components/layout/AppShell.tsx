import React from 'react';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import { useTheme } from '@mui/material/styles';
import NavBar from '../NavBar';
import { layout } from '../../styles/layout';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const theme = useTheme();

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: theme.appTokens.surface.canvas }}>
      <NavBar drawerWidth={layout.navWidth} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${layout.navWidth}px)` },
          px: layout.pagePadding,
          py: 2,
          bgcolor: theme.appTokens.surface.canvas,
        }}
      >
        <Toolbar />
        <Box sx={{ maxWidth: layout.contentMaxWidth, mx: 'auto', width: '100%' }}>{children}</Box>
      </Box>
    </Box>
  );
};

export default AppShell;

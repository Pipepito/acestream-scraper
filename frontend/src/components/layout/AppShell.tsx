import React from 'react';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import NavBar from '../NavBar';
import { layout } from '../../styles/layout';

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <NavBar drawerWidth={layout.navWidth} />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${layout.navWidth}px)` },
          px: layout.pagePadding,
          py: 2,
        }}
      >
        <Toolbar />
        <Box sx={{ maxWidth: layout.contentMaxWidth, mx: 'auto', width: '100%' }}>{children}</Box>
      </Box>
    </Box>
  );
};

export default AppShell;


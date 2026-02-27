import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
  Chip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { getNavTitle, navItems } from './layout/navItems';

interface NavBarProps {
  drawerWidth?: number;
}

const NavBar: React.FC<NavBarProps> = ({ drawerWidth = 264 }) => {
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const operations = navItems.filter((item) => item.section === 'Operations');
  const system = navItems.filter((item) => item.section === 'System');

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700 }}>
          Acestream Scraper
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ py: 1 }}>
        <ListItem>
          <Chip label="Operations" size="small" variant="outlined" />
        </ListItem>
        {operations.map((item) => {
          const isSelected =
            (item.path === '/' && location.pathname === '/') ||
            (item.path !== '/' && location.pathname.startsWith(item.path)) ||
            (item.matchPrefixes && item.matchPrefixes.some((prefix) => location.pathname.startsWith(prefix)));
          return (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                component={RouterLink}
                to={item.path}
                selected={Boolean(isSelected)}
                onClick={() => setMobileOpen(false)}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  '&.Mui-selected': {
                    bgcolor: 'rgba(15, 118, 110, 0.14)',
                    '&:hover': { bgcolor: 'rgba(15, 118, 110, 0.22)' },
                  },
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      <Divider sx={{ mt: 1 }} />
      <List sx={{ py: 1, mt: 'auto' }}>
        <ListItem>
          <Chip label="System" size="small" variant="outlined" />
        </ListItem>
        {system.map((item) => {
          const isSelected =
            (item.path === '/' && location.pathname === '/') ||
            (item.path !== '/' && location.pathname.startsWith(item.path));
          return (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                component={RouterLink}
                to={item.path}
                selected={Boolean(isSelected)}
                onClick={() => setMobileOpen(false)}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  '&.Mui-selected': {
                    bgcolor: 'rgba(15, 118, 110, 0.14)',
                    '&:hover': { bgcolor: 'rgba(15, 118, 110, 0.22)' },
                  },
                }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {getNavTitle(location.pathname)}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="navigation menu"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRightColor: 'divider',
              backgroundColor: 'background.paper',
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
    </>
  );
};

export default NavBar;

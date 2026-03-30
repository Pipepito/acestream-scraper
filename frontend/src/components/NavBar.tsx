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
  useMediaQuery,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import MenuIcon from '@mui/icons-material/Menu';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import { isNavItemSelected, navItems } from './layout/navItems';
import { getShellLayout } from '../styles/layout';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

interface NavBarProps {
  drawerWidth?: number;
}

const NavBar: React.FC<NavBarProps> = ({ drawerWidth = 264 }) => {
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const location = useLocation();
  const theme = useTheme();
  const { mode, toggleMode } = useAppThemeMode();
  const shellLayout = getShellLayout(theme);
  const isPhone = useMediaQuery(`(max-width:${shellLayout.phoneMaxWidth}px)`);
  const isDesktop = !isPhone;

  const selectedStyles = {
    bgcolor: theme.appTokens.shell.activeNavBg,
    color: theme.appTokens.shell.activeNavText,
    boxShadow: `inset 0 0 0 1px ${theme.appTokens.shell.activeNavBorder}`,
    '& .MuiListItemIcon-root': {
      color: theme.appTokens.shell.activeNavText,
    },
    '& .MuiListItemText-primary': {
      color: theme.appTokens.shell.activeNavText,
      fontWeight: 600,
    },
    '&:hover': {
      bgcolor: alpha(theme.appTokens.shell.activeNavBg, 0.9),
    },
  };

  const handleDrawerOpen = () => {
    setMobileOpen(true);
  };

  const handleDrawerClose = () => {
    setMobileOpen(false);
  };

  const operations = navItems.filter((item) => item.section === 'Operations');
  const system = navItems.filter((item) => item.section === 'System');

  const renderNavItems = (items: typeof navItems) =>
    items.map((item) => {
      const isSelected = isNavItemSelected(item, location.pathname);

      return (
        <ListItem key={item.text} disablePadding>
          <ListItemButton
            component={RouterLink}
            to={item.path}
            selected={Boolean(isSelected)}
            aria-current={isSelected ? 'page' : undefined}
            onClick={isPhone ? handleDrawerClose : undefined}
            sx={{
              mx: 1,
              borderRadius: 2,
              color: theme.appTokens.text.secondary,
              '& .MuiListItemIcon-root': {
                minWidth: 40,
                color: theme.appTokens.text.muted,
              },
              '&:hover': {
                bgcolor: theme.appTokens.surface.muted,
              },
              '&.Mui-selected': {
                ...selectedStyles,
              },
            }}
          >
            <ListItemIcon sx={{ color: isSelected ? theme.appTokens.action.secondaryText : theme.appTokens.text.muted }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItemButton>
        </ListItem>
      );
    });

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: theme.appTokens.shell.navBg,
        color: theme.appTokens.text.primary,
        boxShadow: 'none',
        borderRight: `1px solid ${theme.appTokens.shell.navBorder}`,
      }}
    >
      <Toolbar>
        <Typography variant="sectionTitle" noWrap component="div" sx={{ color: theme.appTokens.text.primary }}>
          Acestream Scraper
        </Typography>
      </Toolbar>
      <Divider sx={{ borderColor: theme.appTokens.shell.navBorder }} />
      <List sx={{ py: 1 }}>
        <ListItem>
          <Chip
            label="Operations"
            size="small"
            variant="outlined"
            sx={{
              borderColor: theme.appTokens.surface.border,
              bgcolor: alpha(theme.appTokens.shell.accent, 0.08),
              color: theme.appTokens.text.secondary,
            }}
          />
        </ListItem>
        {renderNavItems(operations)}
      </List>
      <Divider sx={{ mt: 1, borderColor: theme.appTokens.shell.navBorder }} />
      <List sx={{ py: 1, mt: 'auto' }}>
        <ListItem>
          <Chip
            label="System"
            size="small"
            variant="outlined"
            sx={{
              borderColor: theme.appTokens.surface.border,
              bgcolor: alpha(theme.appTokens.shell.accent, 0.08),
              color: theme.appTokens.text.secondary,
            }}
          />
        </ListItem>
        {renderNavItems(system)}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: isDesktop ? `calc(100% - ${drawerWidth}px)` : '100%',
          ml: isDesktop ? `${drawerWidth}px` : 0,
          bgcolor: theme.appTokens.shell.appBarBg,
          color: theme.appTokens.text.primary,
          borderBottom: `1px solid ${theme.appTokens.shell.appBarBorder}`,
          boxShadow: 'none',
          backgroundImage: 'none',
        }}
      >
        <Toolbar>
          {isPhone ? (
            <IconButton color="inherit" aria-label="open drawer" edge="start" onClick={handleDrawerOpen} sx={{ mr: 2 }}>
              <MenuIcon />
            </IconButton>
          ) : null}
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton
              color="inherit"
              onClick={toggleMode}
              aria-label={mode === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
            >
              {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: isDesktop ? drawerWidth : 0, flexShrink: isDesktop ? 0 : 1 }}
        aria-label="navigation menu"
      >
        {isPhone ? (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerClose}
            ModalProps={{
              keepMounted: true,
            }}
            sx={{
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
                borderRightColor: theme.appTokens.shell.navBorder,
                backgroundColor: theme.appTokens.shell.navBg,
              },
            }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
                borderRightColor: theme.appTokens.shell.navBorder,
                backgroundColor: theme.appTokens.shell.navBg,
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        )}
      </Box>
    </>
  );
};

export default NavBar;

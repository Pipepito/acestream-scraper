import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Button,
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
  useMediaQuery,
} from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import MenuIcon from '@mui/icons-material/Menu';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { getNavTitle, isNavItemSelected, navItems } from './layout/navItems';
import { getShellLayout } from '../styles/layout';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

interface NavBarProps {
  drawerWidth?: number;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
}

const NavBar: React.FC<NavBarProps> = ({ drawerWidth = 264, collapsed = false, onToggleCollapsed }) => {
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
        minHeight: '100%',
        pb: 'env(safe-area-inset-bottom)',
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
      {(['Watch', 'Manage', 'System'] as const).map((section) => <React.Fragment key={section}>
        <List sx={{ py: 1 }} aria-label={section}>
          <ListItem><Typography variant="overline" color="text.secondary">{section}</Typography></ListItem>
          {renderNavItems(navItems.filter((item) => item.section === section))}
        </List>
        {section !== 'System' ? <Divider /> : null}
      </React.Fragment>)}
    </Box>
  );

  return (
    <>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: isDesktop && !collapsed ? `calc(100% - ${drawerWidth}px)` : '100%',
          ml: isDesktop && !collapsed ? `${drawerWidth}px` : 0,
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
          {isDesktop && onToggleCollapsed ? <IconButton color="inherit" aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'} aria-expanded={!collapsed} onClick={onToggleCollapsed} edge="start" sx={{ mr: 2 }}><MenuIcon /></IconButton> : null}
          <Typography noWrap sx={{ minWidth: 0, fontWeight: 600 }}>{getNavTitle(location.pathname)}</Typography>
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1, flexShrink: 0 }}>
            <Button
              component="a"
              href="https://github.com/Pipepito/acestream-scraper/wiki"
              target="_blank"
              rel="noopener noreferrer"
              variant="text"
              color="inherit"
              size="small"
              endIcon={<OpenInNewIcon />}
              aria-label="Wiki (opens in a new tab)"
              sx={{ minHeight: 44 }}
            >
              Wiki
            </Button>
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
        sx={{ width: isDesktop && !collapsed ? drawerWidth : 0, flexShrink: isDesktop ? 0 : 1 }}
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
        ) : !collapsed ? (
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
        ) : null}
      </Box>
    </>
  );
};

export default NavBar;

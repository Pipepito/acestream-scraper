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
import { getNavTitle, isNavItemSelected, navItems } from './layout/navItems';
import { getShellLayout } from '../styles/layout';

interface NavBarProps {
  drawerWidth?: number;
}

const NavBar: React.FC<NavBarProps> = ({ drawerWidth = 264 }) => {
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const location = useLocation();
  const theme = useTheme();
  const shellLayout = getShellLayout(theme);
  const isPhone = useMediaQuery(`(max-width:${shellLayout.phoneMaxWidth}px)`);
  const isDesktop = !isPhone;

  const selectedStyles = {
    bgcolor: theme.appTokens.action.secondaryBg,
    color: theme.appTokens.action.secondaryText,
    boxShadow: `inset 0 0 0 1px ${theme.appTokens.surface.border}`,
    '& .MuiListItemIcon-root': {
      color: theme.appTokens.action.secondaryText,
    },
    '& .MuiListItemText-primary': {
      color: theme.appTokens.action.secondaryText,
      fontWeight: 600,
    },
    '&:hover': {
      bgcolor: alpha(theme.appTokens.action.secondaryBg, 0.88),
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
        bgcolor: theme.appTokens.surface.panel,
        color: theme.appTokens.text.primary,
        boxShadow: 'none',
      }}
    >
      <Toolbar>
        <Typography variant="sectionTitle" noWrap component="div" sx={{ color: theme.appTokens.text.primary }}>
          Acestream Scraper
        </Typography>
      </Toolbar>
      <Divider sx={{ borderColor: theme.appTokens.layout.divider }} />
      <List sx={{ py: 1 }}>
        <ListItem>
          <Chip
            label="Operations"
            size="small"
            variant="outlined"
            sx={{
              borderColor: theme.appTokens.surface.border,
              bgcolor: theme.appTokens.surface.muted,
              color: theme.appTokens.text.secondary,
            }}
          />
        </ListItem>
        {renderNavItems(operations)}
      </List>
      <Divider sx={{ mt: 1, borderColor: theme.appTokens.layout.divider }} />
      <List sx={{ py: 1, mt: 'auto' }}>
        <ListItem>
          <Chip
            label="System"
            size="small"
            variant="outlined"
            sx={{
              borderColor: theme.appTokens.surface.border,
              bgcolor: theme.appTokens.surface.muted,
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
          bgcolor: theme.appTokens.surface.panel,
          color: theme.appTokens.text.primary,
          borderBottom: `1px solid ${theme.appTokens.layout.divider}`,
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
          <Typography variant="h6" noWrap component="div">
            {getNavTitle(location.pathname)}
          </Typography>
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
                borderRightColor: theme.appTokens.layout.divider,
                backgroundColor: theme.appTokens.surface.panel,
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
                borderRightColor: theme.appTokens.layout.divider,
                backgroundColor: theme.appTokens.surface.panel,
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

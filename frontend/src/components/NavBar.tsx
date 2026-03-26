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
import { alpha, useTheme } from '@mui/material/styles';
import MenuIcon from '@mui/icons-material/Menu';
import { getNavTitle, navItems } from './layout/navItems';

interface NavBarProps {
  drawerWidth?: number;
}

const NavBar: React.FC<NavBarProps> = ({ drawerWidth = 264 }) => {
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const location = useLocation();
  const theme = useTheme();

  const selectedStyles = {
    bgcolor: theme.appTokens.action.secondaryBg,
    color: theme.appTokens.text.primary,
    boxShadow: `inset 0 0 0 1px ${theme.appTokens.surface.border}`,
    '& .MuiListItemIcon-root': {
      color: theme.appTokens.action.secondaryText,
    },
    '&:hover': {
      bgcolor: alpha(theme.appTokens.action.secondaryBg, 0.88),
    },
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const operations = navItems.filter((item) => item.section === 'Operations');
  const system = navItems.filter((item) => item.section === 'System');

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: theme.appTokens.surface.panel,
        color: theme.appTokens.text.primary,
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
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          );
        })}
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
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
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
      </Box>
    </>
  );
};

export default NavBar;

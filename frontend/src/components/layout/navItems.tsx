import React from 'react';
import { matchPath } from 'react-router-dom';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import TravelExploreRoundedIcon from '@mui/icons-material/TravelExploreRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import LiveTvRoundedIcon from '@mui/icons-material/LiveTvRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import PlaylistPlayRoundedIcon from '@mui/icons-material/PlaylistPlayRounded';
import CloudRoundedIcon from '@mui/icons-material/CloudRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';
import HealthAndSafetyRoundedIcon from '@mui/icons-material/HealthAndSafetyRounded';

export interface NavItem {
  text: string;
  path: string;
  icon: React.ReactElement;
  section: 'Operations' | 'System';
  matchPrefixes?: string[];
}

export const navItems: NavItem[] = [
  {
    text: 'Dashboard',
    path: '/',
    icon: <DashboardRoundedIcon />,
    section: 'Operations',
  },
  {
    text: 'Scraper',
    path: '/scraper',
    icon: <TravelExploreRoundedIcon />,
    section: 'Operations',
  },
  {
    text: 'Acestream Search',
    path: '/search',
    icon: <SearchRoundedIcon />,
    section: 'Operations',
  },
  {
    text: 'Acestream Channels',
    path: '/acestream-channels',
    icon: <LiveTvRoundedIcon />,
    section: 'Operations',
  },
  {
    text: 'EPG Sources',
    path: '/epg',
    icon: <EventNoteRoundedIcon />,
    section: 'Operations',
    matchPrefixes: ['/epg', '/epg/channels'],
  },
  {
    text: 'TV Channels',
    path: '/tv-channels',
    icon: <LiveTvRoundedIcon />,
    section: 'Operations',
    matchPrefixes: ['/tv-channels'],
  },
  {
    text: 'Playlist',
    path: '/playlist',
    icon: <PlaylistPlayRoundedIcon />,
    section: 'Operations',
  },
  {
    text: 'WARP Status',
    path: '/warp',
    icon: <CloudRoundedIcon />,
    section: 'System',
  },
  {
    text: 'Settings',
    path: '/settings',
    icon: <SettingsRoundedIcon />,
    section: 'System',
  },
  {
    text: 'Health',
    path: '/health',
    icon: <HealthAndSafetyRoundedIcon />,
    section: 'System',
  },
];

const matchesSegmentPath = (pathname: string, candidatePath: string) => {
  if (candidatePath === '/') {
    return pathname === '/';
  }

  return Boolean(
    matchPath({ path: candidatePath, end: true }, pathname) ||
      matchPath({ path: `${candidatePath}/*`, end: false }, pathname)
  );
};

export function isNavItemSelected(item: NavItem, pathname: string): boolean {
  const candidatePaths = [item.path, ...(item.matchPrefixes ?? [])];

  return candidatePaths.some((candidatePath) => matchesSegmentPath(pathname, candidatePath));
}

export function getNavTitle(pathname: string): string {
  const matched = navItems.find((item) => isNavItemSelected(item, pathname));

  return matched?.text ?? 'Not Found';
}

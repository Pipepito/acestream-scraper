import React from 'react';
import { matchPath } from 'react-router-dom';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import TravelExploreRoundedIcon from '@mui/icons-material/TravelExploreRounded';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import LiveTvRoundedIcon from '@mui/icons-material/LiveTvRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import PlaylistPlayRoundedIcon from '@mui/icons-material/PlaylistPlayRounded';
import HubRoundedIcon from '@mui/icons-material/HubRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';

export interface NavItem {
  text: string;
  path: string;
  icon: React.ReactElement;
  section: 'Operations' | 'System';
  matchPrefixes?: string[];
}

export const navItems: NavItem[] = [
  { text: 'Overview', path: '/', icon: <DashboardRoundedIcon />, section: 'Operations' },
  { text: 'Scraper', path: '/scraper', icon: <TravelExploreRoundedIcon />, section: 'Operations' },
  { text: 'Search', path: '/search', icon: <SearchRoundedIcon />, section: 'Operations' },
  { text: 'Acestream Channels', path: '/acestream-channels', icon: <LiveTvRoundedIcon />, section: 'Operations' },
  { text: 'TV Channels', path: '/tv-channels', icon: <LiveTvRoundedIcon />, section: 'Operations', matchPrefixes: ['/tv-channels'] },
  { text: 'EPG', path: '/epg', icon: <EventNoteRoundedIcon />, section: 'Operations', matchPrefixes: ['/epg/channels'] },
  { text: 'Playlist', path: '/playlist', icon: <PlaylistPlayRoundedIcon />, section: 'Operations' },
  { text: 'Integrations', path: '/integrations', icon: <HubRoundedIcon />, section: 'System' },
  { text: 'Settings', path: '/settings', icon: <SettingsRoundedIcon />, section: 'System' },
];

/** Routable pages that are reached from within another page rather than the nav. */
export const hiddenRouteTitles: Array<{ path: string; title: string }> = [
  { path: '/warp', title: 'WARP' },
];

const matchesSegmentPath = (pathname: string, candidatePath: string, allowDescendants = false) => {
  if (candidatePath === '/') {
    return pathname === '/';
  }

  if (matchPath({ path: candidatePath, end: true }, pathname)) {
    return true;
  }

  if (!allowDescendants) {
    return false;
  }

  return Boolean(matchPath({ path: `${candidatePath}/*`, end: false }, pathname));
};

export function isNavItemSelected(item: NavItem, pathname: string): boolean {
  if (matchesSegmentPath(pathname, item.path)) {
    return true;
  }

  return (item.matchPrefixes ?? []).some((candidatePath) =>
    matchesSegmentPath(pathname, candidatePath, true)
  );
}

export function getNavTitle(pathname: string): string {
  const matched = navItems.find((item) => isNavItemSelected(item, pathname));
  if (matched) return matched.text;
  const hidden = hiddenRouteTitles.find((item) => matchesSegmentPath(pathname, item.path, true));
  return hidden?.title ?? 'Not Found';
}

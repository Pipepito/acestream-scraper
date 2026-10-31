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
import HistoryRoundedIcon from '@mui/icons-material/HistoryRounded';

export interface NavItem {
  text: string;
  path: string;
  icon: React.ReactElement;
  section: 'Watch' | 'Manage' | 'Integrations' | 'System';
  matchPrefixes?: string[];
}

export const navItems: NavItem[] = [
  { text: 'TV dashboard', path: '/', icon: <DashboardRoundedIcon />, section: 'Watch' },
  { text: 'Live TV', path: '/live-tv', icon: <LiveTvRoundedIcon />, section: 'Watch' },
  { text: 'Recordings', path: '/recordings', icon: <HistoryRoundedIcon />, section: 'Watch' },
  { text: 'Catalogues', path: '/catalogues', icon: <PlaylistPlayRoundedIcon />, section: 'Watch' },


  { text: 'Events', path: '/events', icon: <EventNoteRoundedIcon />, section: 'Watch' },
  { text: 'System status', path: '/system', icon: <DashboardRoundedIcon />, section: 'System' },
  { text: 'Scraper', path: '/scraper', icon: <TravelExploreRoundedIcon />, section: 'Manage' },
  { text: 'Search', path: '/search', icon: <SearchRoundedIcon />, section: 'Manage' },
  { text: 'Acestream Channels', path: '/acestream-channels', icon: <LiveTvRoundedIcon />, section: 'Manage' },
  { text: 'TV Channels', path: '/tv-channels', icon: <LiveTvRoundedIcon />, section: 'Manage', matchPrefixes: ['/tv-channels'] },
  { text: 'EPG', path: '/epg', icon: <EventNoteRoundedIcon />, section: 'Manage', matchPrefixes: ['/epg/channels'] },
  { text: 'Playlist', path: '/playlist', icon: <PlaylistPlayRoundedIcon />, section: 'Manage' },
  { text: 'Public address', path: '/integrations/public-address', icon: <HubRoundedIcon />, section: 'Integrations' },
  { text: 'Web player', path: '/integrations/web-player', icon: <HubRoundedIcon />, section: 'Integrations' },
  { text: 'Remote players', path: '/integrations/remote-players', icon: <HubRoundedIcon />, section: 'Integrations' },
  { text: 'Media servers', path: '/integrations/media-servers', icon: <HubRoundedIcon />, section: 'Integrations' },
  { text: 'Telegram', path: '/integrations/telegram', icon: <HubRoundedIcon />, section: 'Integrations' },
  { text: 'WARP', path: '/warp', icon: <HubRoundedIcon />, section: 'System' },
  { text: 'Settings', path: '/settings', icon: <SettingsRoundedIcon />, section: 'System' },
  { text: 'Changelog', path: '/changelog', icon: <HistoryRoundedIcon />, section: 'System' },
];

/** Routable pages that are reached from within another page rather than the nav. */
export const hiddenRouteTitles: Array<{ path: string; title: string }> = [
  { path: '/setup', title: 'Set up scraper' },
  { path: '/scraper/builder', title: 'Extraction builder' },
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

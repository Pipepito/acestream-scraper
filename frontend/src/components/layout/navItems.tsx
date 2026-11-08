import React from 'react';
import type { CommonLabel } from '../../i18n/resources';
import i18n from '../../i18n';
import { matchPath } from 'react-router-dom';
import DashboardRoundedIcon from '@mui/icons-material/DashboardRounded';
import LiveTvRoundedIcon from '@mui/icons-material/LiveTvRounded';
import EventNoteRoundedIcon from '@mui/icons-material/EventNoteRounded';
import HubRoundedIcon from '@mui/icons-material/HubRounded';
import SettingsRoundedIcon from '@mui/icons-material/SettingsRounded';
import HistoryRoundedIcon from '@mui/icons-material/HistoryRounded';

export interface NavItem {
  text: string;
  label: CommonLabel;
  path: string;
  icon: React.ReactElement;
  section: 'Watch' | 'Manage' | 'Integrations' | 'System';
  matchPrefixes?: string[];
}

export const navItems: NavItem[] = [
  { text: 'Watch', label: 'watch', path: '/', icon: <LiveTvRoundedIcon />, section: 'Watch', matchPrefixes: ['/live-tv'] },
  { text: 'Recordings', label: 'recordings', path: '/recordings', icon: <HistoryRoundedIcon />, section: 'Watch' },
  { text: 'Events', label: 'events', path: '/events', icon: <EventNoteRoundedIcon />, section: 'Watch' },
  { text: 'Channels', label: 'channels', path: '/tv-channels', icon: <LiveTvRoundedIcon />, section: 'Manage', matchPrefixes: ['/tv-channels', '/scraper', '/search', '/epg', '/acestream-channels'] },
  { text: 'Connections', label: 'connections', path: '/connections', icon: <HubRoundedIcon />, section: 'Integrations', matchPrefixes: ['/integrations', '/playlist'] },
  { text: 'Settings', label: 'settings', path: '/settings', icon: <SettingsRoundedIcon />, section: 'System' },
  { text: 'System', label: 'system', path: '/system', icon: <DashboardRoundedIcon />, section: 'System', matchPrefixes: ['/warp', '/setup', '/changelog'] },
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
  if (matched) return i18n.t(matched.label);
  const hidden = hiddenRouteTitles.find((item) => matchesSegmentPath(pathname, item.path, true));
  return hidden?.title ?? 'Not Found';
}

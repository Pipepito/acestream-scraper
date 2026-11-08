import React from 'react';
import { Box, Button } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import type { CommonLabel } from '../../i18n/resources';

export interface SectionLink { label: CommonLabel; to: string }
export const channelLinks: SectionLink[] = [
  { label: 'tvChannels', to: '/tv-channels' }, { label: 'sources', to: '/scraper' },
  { label: 'guide', to: '/epg' }, { label: 'streams', to: '/acestream-channels' }, { label: 'search', to: '/search' },
];
export const connectionLinks: SectionLink[] = [
  { label: 'thisBrowser', to: '/integrations/web-player' }, { label: 'tvsPlayers', to: '/integrations/tv-casting' },
  { label: 'remotePlayers', to: '/integrations/remote-players' }, { label: 'mediaServers', to: '/integrations/media-servers' },
  { label: 'playlists', to: '/playlist' }, { label: 'publicAddress', to: '/integrations/public-address' },
  { label: 'notifications', to: '/connections/notifications' },
];
export default function SectionNavigation({ links, label }: { links: SectionLink[]; label: CommonLabel }) {
  const { pathname } = useLocation();
  const { t } = useTranslation();
  return <Box component="nav" aria-label={t(label)} sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
    {links.map(link => <Button key={link.to} component={Link} to={link.to} color="inherit" aria-current={pathname === link.to || pathname.startsWith(`${link.to}/`) ? 'page' : undefined}
      sx={{ minHeight: 44, '&[aria-current]': { bgcolor: 'action.selected', textDecoration: 'underline', textUnderlineOffset: 5 } }}>{t(link.label)}</Button>)}
  </Box>;
}

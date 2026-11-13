import { useUiText } from './i18n/useUiText';
import React from 'react';
import { Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom';
import RouteBoundary from './components/layout/RouteBoundary';
import AppShell from './components/layout/AppShell';
import ApiTokenNotice from './components/ApiTokenNotice';
const WatchHome = React.lazy(() => import('./pages/WatchHome'));
import SettingsIndex from './pages/SettingsIndex';
import Connections from './pages/Connections';
const AcestreamChannels = React.lazy(() => import('./pages/AcestreamChannels'));
const TVChannels = React.lazy(() => import('./pages/TVChannels'));
const TVChannelDetail = React.lazy(() => import('./pages/TVChannelDetail'));
const Scraper = React.lazy(() => import('./pages/Scraper'));
const EPG = React.lazy(() => import('./pages/EPG'));
const EPGChannelDetail = React.lazy(() => import('./pages/EPGChannelDetail'));
const Playlist = React.lazy(() => import('./pages/Playlist'));
const WARP = React.lazy(() => import('./pages/WARP'));
const Search = React.lazy(() => import('./pages/Search'));
const Settings = React.lazy(() => import('./pages/Settings'));
const LiveTV = React.lazy(() => import('./pages/LiveTV'));
import NotFound from './pages/NotFound';
import SetupNotice from './components/SetupNotice';
import { Button, Stack, Typography } from '@mui/material';
import { useAccess } from './components/access/AccessContext';
import SectionNavigation, { channelLinks, connectionLinks } from './components/layout/SectionNavigation';
import { accessService } from './services/accessService';
const Setup = React.lazy(() => import('./pages/Setup'));
import UpdateAvailableNotice from './components/UpdateAvailableNotice';
const PublicAddress = React.lazy(() => import('./pages/integrations/PublicAddress'));
const WebPlayer = React.lazy(() => import('./pages/integrations/WebPlayer'));
const TvCasting = React.lazy(() => import('./pages/integrations/TvCasting'));
const RemotePlayers = React.lazy(() => import('./pages/integrations/RemotePlayers'));
const MediaServers = React.lazy(() => import('./pages/integrations/MediaServers'));
const Notifications = React.lazy(() => import('./pages/integrations/Notifications'));
const SystemRuntime = React.lazy(() => import('./pages/SystemRuntime'));
const Telegram = React.lazy(() => import('./pages/integrations/Telegram'));
const SystemDashboard = React.lazy(() => import('./pages/SystemDashboard'));

const Recordings = React.lazy(() => import('./pages/Recordings'));
const Events = React.lazy(() => import('./pages/Events'));
const Changelog = React.lazy(() => import('./pages/Changelog'));
const ExtractionBuilder = React.lazy(() => import('./pages/ExtractionBuilder'));

/** Old URLs keep working: they land on the page that now holds that information. */
export const LEGACY_REDIRECTS: Array<{ from: string; to: string }> = [
  { from: '/dashboard', to: '/' },
  { from: '/integrations', to: '/integrations/public-address' },
  { from: '/health', to: '/system' },
  { from: '/stats', to: '/' },
  { from: '/channels', to: '/tv-channels' },
  { from: '/channels/:id', to: '/tv-channels' },
  { from: '/search-new', to: '/search' },
  { from: '/epg/mappings', to: '/epg?tab=rules' },
  { from: '/catalogues', to: '/scraper?tab=w3u' },
];

/** The redirect target plus the old URL's query string; the target's own keys win. */
export function redirectTarget(to: string, search: string): string {
  const [path, targetQuery = ''] = to.split('?');
  const params = new URLSearchParams(targetQuery);
  const targetKeys = new Set(Array.from(params.keys()));
  new URLSearchParams(search).forEach((value, key) => { if (!targetKeys.has(key)) params.append(key, value); });
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

const RedirectTo: React.FC<{ to: string }> = ({ to }) => {
  // Consume params so patterns like /channels/:id can redirect without them.
  useParams();
  const { search } = useLocation();
  return <Navigate to={redirectTarget(to, search)} replace />;
};

const App: React.FC = () => {
  const tUi = useUiText();
  const access = useAccess();
  const location = useLocation();
  const channelsSection = channelLinks.some(link => location.pathname === link.to || location.pathname.startsWith(`${link.to}/`));
  const connectionsSection = connectionLinks.some(link => location.pathname === link.to);
  const settingsTab = new URLSearchParams(location.search).get('tab');
  return (
    <AppShell>
      {access?.status.user ? <Stack direction="row" spacing={2} justifyContent="flex-end" alignItems="center" sx={{ mb: 1 }}><Typography variant="body2">{access.status.user.username}</Typography><Button onClick={() => void accessService.logout().then(access.refresh)}>{tUi("Sign out")}</Button></Stack> : null}
      <ApiTokenNotice />
      <UpdateAvailableNotice />
      <SetupNotice />
      {channelsSection ? <SectionNavigation links={channelLinks} label="channels" /> : null}
      {connectionsSection ? <SectionNavigation links={connectionLinks} label="connections" /> : null}
      <RouteBoundary key={location.pathname}><Routes>
        <Route path="/" element={<WatchHome />} />
        <Route path="/system" element={<React.Suspense fallback={<p role="status">{tUi("Loading system status…")}</p>}><SystemDashboard /></React.Suspense>} />
        <Route path="/acestream-channels" element={<AcestreamChannels />} />
        <Route path="/live-tv" element={<LiveTV />} />
        <Route path="/recordings" element={<React.Suspense fallback={<p role="status">{tUi("Loading recordings…")}</p>}><Recordings /></React.Suspense>} />
        <Route path="/events" element={<React.Suspense fallback={<p role="status">{tUi("Loading events…")}</p>}><Events /></React.Suspense>} />
        <Route path="/tv-channels" element={<TVChannels />} />
        <Route path="/tv-channels/:id" element={<TVChannelDetail />} />
        <Route path="/scraper" element={<Scraper />} />
        <Route path="/scraper/builder" element={<React.Suspense fallback={<p role="status">{tUi("Loading extraction builder…")}</p>}><ExtractionBuilder /></React.Suspense>} />
        <Route path="/epg" element={<EPG />} />
        <Route path="/epg/channels/:id" element={<EPGChannelDetail />} />
        <Route path="/playlist" element={<Playlist />} />
        <Route path="/warp" element={<WARP />} />
        <Route path="/search" element={<Search />} />
        <Route path="/integrations/public-address" element={<React.Suspense fallback={<p role="status">{tUi("Loading integration…")}</p>}><PublicAddress /></React.Suspense>} />
        <Route path="/integrations/web-player" element={<React.Suspense fallback={<p role="status">{tUi("Loading integration…")}</p>}><WebPlayer /></React.Suspense>} />
        <Route path="/integrations/tv-casting" element={<React.Suspense fallback={<p role="status">{tUi("Loading integration…")}</p>}><TvCasting /></React.Suspense>} />
        <Route path="/integrations/remote-players" element={<React.Suspense fallback={<p role="status">{tUi("Loading integration…")}</p>}><RemotePlayers /></React.Suspense>} />
        <Route path="/integrations/media-servers" element={<React.Suspense fallback={<p role="status">{tUi("Loading integration…")}</p>}><MediaServers /></React.Suspense>} />
        <Route path="/connections/notifications" element={<React.Suspense fallback={<p role="status">{tUi("Loading…")}</p>}><Notifications /></React.Suspense>} />
        <Route path="/system/runtime" element={<React.Suspense fallback={<p role="status">{tUi("Loading…")}</p>}><SystemRuntime /></React.Suspense>} />
        <Route path="/scraper/telegram" element={<React.Suspense fallback={<p role="status">{tUi("Loading…")}</p>}><Telegram /></React.Suspense>} />
        <Route path="/integrations/telegram" element={<RedirectTo to="/scraper/telegram" />} />
        <Route path="/setup" element={<React.Suspense fallback={<p role="status">{tUi("Loading setup…")}</p>}><Setup /></React.Suspense>} />
        <Route path="/connections" element={<Connections />} />
        <Route path="/settings" element={settingsTab ? <Settings /> : <SettingsIndex />} />
        <Route path="/changelog" element={<React.Suspense fallback={<p role="status">{tUi("Loading changelog…")}</p>}><Changelog /></React.Suspense>} />
        {LEGACY_REDIRECTS.map((redirect) => (
          <Route key={redirect.from} path={redirect.from} element={<RedirectTo to={redirect.to} />} />
        ))}
        <Route path="*" element={<NotFound />} />
      </Routes></RouteBoundary>
    </AppShell>
  );
};

export default App;

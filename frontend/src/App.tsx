import React from 'react';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import ApiTokenNotice from './components/ApiTokenNotice';
import TVDashboard from './pages/TVDashboard';
import AcestreamChannels from './pages/AcestreamChannels';
import TVChannels from './pages/TVChannels';
import TVChannelDetail from './pages/TVChannelDetail';
import Scraper from './pages/Scraper';
import EPG from './pages/EPG';
import EPGChannelDetail from './pages/EPGChannelDetail';
import Playlist from './pages/Playlist';
import WARP from './pages/WARP';
import Search from './pages/Search';
import Settings from './pages/Settings';
import LiveTV from './pages/LiveTV';
import NotFound from './pages/NotFound';
import SetupNotice from './components/SetupNotice';
const Setup = React.lazy(() => import('./pages/Setup'));
import UpdateAvailableNotice from './components/UpdateAvailableNotice';
const PublicAddress = React.lazy(() => import('./pages/integrations/PublicAddress'));
const WebPlayer = React.lazy(() => import('./pages/integrations/WebPlayer'));
const RemotePlayers = React.lazy(() => import('./pages/integrations/RemotePlayers'));
const MediaServers = React.lazy(() => import('./pages/integrations/MediaServers'));
const Telegram = React.lazy(() => import('./pages/integrations/Telegram'));
const SystemDashboard = React.lazy(() => import('./pages/SystemDashboard'));
const Catalogues = React.lazy(() => import('./pages/Catalogues'));


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
];

const RedirectTo: React.FC<{ to: string }> = ({ to }) => {
  // Consume params so patterns like /channels/:id can redirect without them.
  useParams();
  return <Navigate to={to} replace />;
};

const App: React.FC = () => {
  return (
    <AppShell>
      <ApiTokenNotice />
      <UpdateAvailableNotice />
      <SetupNotice />
      <Routes>
        <Route path="/" element={<TVDashboard />} />
        <Route path="/system" element={<React.Suspense fallback={<p role="status">Loading system status…</p>}><SystemDashboard /></React.Suspense>} />
        <Route path="/acestream-channels" element={<AcestreamChannels />} />
        <Route path="/catalogues" element={<React.Suspense fallback={<p role="status">Loading catalogues…</p>}><Catalogues /></React.Suspense>} />
        <Route path="/live-tv" element={<LiveTV />} />
        <Route path="/recordings" element={<React.Suspense fallback={<p role="status">Loading recordings…</p>}><Recordings /></React.Suspense>} />
        <Route path="/events" element={<React.Suspense fallback={<p role="status">Loading events…</p>}><Events /></React.Suspense>} />
        <Route path="/tv-channels" element={<TVChannels />} />
        <Route path="/tv-channels/:id" element={<TVChannelDetail />} />
        <Route path="/scraper" element={<Scraper />} />
        <Route path="/scraper/builder" element={<React.Suspense fallback={<p>Loading extraction builder…</p>}><ExtractionBuilder /></React.Suspense>} />
        <Route path="/epg" element={<EPG />} />
        <Route path="/epg/channels/:id" element={<EPGChannelDetail />} />
        <Route path="/playlist" element={<Playlist />} />
        <Route path="/warp" element={<WARP />} />
        <Route path="/search" element={<Search />} />
        <Route path="/integrations/public-address" element={<React.Suspense fallback={<p role="status">Loading integration…</p>}><PublicAddress /></React.Suspense>} />
        <Route path="/integrations/web-player" element={<React.Suspense fallback={<p role="status">Loading integration…</p>}><WebPlayer /></React.Suspense>} />
        <Route path="/integrations/remote-players" element={<React.Suspense fallback={<p role="status">Loading integration…</p>}><RemotePlayers /></React.Suspense>} />
        <Route path="/integrations/media-servers" element={<React.Suspense fallback={<p role="status">Loading integration…</p>}><MediaServers /></React.Suspense>} />
        <Route path="/integrations/telegram" element={<React.Suspense fallback={<p role="status">Loading integration…</p>}><Telegram /></React.Suspense>} />
        <Route path="/setup" element={<React.Suspense fallback={<p role="status">Loading setup…</p>}><Setup /></React.Suspense>} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/changelog" element={<React.Suspense fallback={<p role="status">Loading changelog…</p>}><Changelog /></React.Suspense>} />
        {LEGACY_REDIRECTS.map((redirect) => (
          <Route key={redirect.from} path={redirect.from} element={<RedirectTo to={redirect.to} />} />
        ))}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  );
};

export default App;

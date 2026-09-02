import React from 'react';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import ApiTokenNotice from './components/ApiTokenNotice';
import Overview from './pages/Overview';
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
import NotFound from './pages/NotFound';

/** Old URLs keep working: they land on the page that now holds that information. */
export const LEGACY_REDIRECTS: Array<{ from: string; to: string }> = [
  { from: '/dashboard', to: '/' },
  { from: '/health', to: '/' },
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
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/acestream-channels" element={<AcestreamChannels />} />
        <Route path="/tv-channels" element={<TVChannels />} />
        <Route path="/tv-channels/:id" element={<TVChannelDetail />} />
        <Route path="/scraper" element={<Scraper />} />
        <Route path="/epg" element={<EPG />} />
        <Route path="/epg/channels/:id" element={<EPGChannelDetail />} />
        <Route path="/playlist" element={<Playlist />} />
        <Route path="/warp" element={<WARP />} />
        <Route path="/search" element={<Search />} />
        <Route path="/settings" element={<Settings />} />
        {LEGACY_REDIRECTS.map((redirect) => (
          <Route key={redirect.from} path={redirect.from} element={<RedirectTo to={redirect.to} />} />
        ))}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppShell>
  );
};

export default App;

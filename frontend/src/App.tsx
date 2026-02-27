import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
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
import Health from './pages/Health';
import NotFound from './pages/NotFound';

const App: React.FC = () => {
  return (
    <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
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
          <Route path="/health" element={<Health />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
    </AppShell>
  );
};

export default App;

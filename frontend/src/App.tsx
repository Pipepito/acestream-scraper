import React from 'react';
import { Routes, Route } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import ApiTokenNotice from './components/ApiTokenNotice';
import Dashboard from './pages/Dashboard';
import AcestreamChannels from './pages/AcestreamChannels';
import TVChannels from './pages/TVChannels';
import TVChannelDetail from './pages/TVChannelDetail';
import Channels from './pages/Channels';
import ChannelDetail from './pages/ChannelDetail';
import Scraper from './pages/Scraper';
import EPG from './pages/EPG';
import EPGMappings from './pages/EPGMappings';
import EPGChannelDetail from './pages/EPGChannelDetail';
import Playlist from './pages/Playlist';
import WARP from './pages/WARP';
import Search from './pages/Search';
import SearchNew from './pages/SearchNew';
import Settings from './pages/Settings';
import Health from './pages/Health';
import Stats from './pages/Stats';
import NotFound from './pages/NotFound';

const App: React.FC = () => {
  return (
    <AppShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/acestream-channels" element={<AcestreamChannels />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/channels/:id" element={<ChannelDetail />} />
          <Route path="/tv-channels" element={<TVChannels />} />
          <Route path="/tv-channels/:id" element={<TVChannelDetail />} />
          <Route path="/scraper" element={<Scraper />} />
          <Route path="/epg" element={<EPG />} />
          <Route path="/epg/mappings" element={<EPGMappings />} />
          <Route path="/epg/channels/:id" element={<EPGChannelDetail />} />
          <Route path="/playlist" element={<Playlist />} />
          <Route path="/warp" element={<WARP />} />
          <Route path="/search" element={<Search />} />
          <Route path="/search-new" element={<SearchNew />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/health" element={<Health />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
        <ApiTokenNotice />
    </AppShell>
  );
};

export default App;

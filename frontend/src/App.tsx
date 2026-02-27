import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Box from '@mui/material/Box';

import NavBar from './components/NavBar';
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
  console.log('App component rendering...');

  return (
    <Box sx={{ display: 'flex' }}>
      <NavBar />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        {/* Toolbar spacer */}
        <Box sx={{ height: '64px' }} />

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
      </Box>
    </Box>
  );
}

export default App;

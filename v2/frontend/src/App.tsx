import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Box from '@mui/material/Box';

import NavBar from './components/NavBar';
import Dashboard from './pages/Dashboard';
import Channels from './pages/Channels';
import Scraper from './pages/Scraper';
import EPG from './pages/EPG';
import Playlist from './pages/Playlist';
import NotFound from './pages/NotFound';

const App: React.FC = () => {
  return (
    <Box sx={{ display: 'flex' }}>
      <NavBar />
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        {/* Toolbar spacer */}
        <Box sx={{ height: '64px' }} />
        
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/scraper" element={<Scraper />} />
          <Route path="/epg" element={<EPG />} />
          <Route path="/playlist" element={<Playlist />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;

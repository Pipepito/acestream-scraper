import React from 'react';
import { Box } from '@mui/material';
import LiveTV from './LiveTV';
import TVDashboard from './TVDashboard';
import { useAppPreferences } from '../preferences/AppPreferences';

/** One viewing/controller tree for every preset, with independent overview reads. */
export default function WatchHome() {
  const { interface: preset } = useAppPreferences();
  return <Box>
    <Box aria-hidden sx={{ display: { xs: 'none', md: preset === 'lime' ? 'none' : 'block' }, mb: 3, overflow: 'hidden', borderRadius: preset === 'cyan' ? 3 : 1, height: preset === 'cyan' ? 180 : 120 }}>
      <Box component="img" src="/static/visuals/coast-800.webp" srcSet="/static/visuals/coast-800.webp 800w, /static/visuals/coast-1600.webp 1600w" sizes="(min-width: 1280px) 1200px, 100vw" alt="" width={1600} height={901} decoding="async" sx={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 55%' }} />
    </Box>
    <LiveTV home /><TVDashboard embedded />
  </Box>;
}

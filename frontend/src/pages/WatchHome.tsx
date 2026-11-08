import React from 'react';
import { Box, Typography } from '@mui/material';
import { useUiText } from '../i18n/useUiText';
import LiveTV from './LiveTV';
import TVDashboard from './TVDashboard';
import { useAppPreferences } from '../preferences/AppPreferences';

/** One viewing/controller tree for every preset, with independent overview reads. */
export default function WatchHome() {
  const { interface: preset } = useAppPreferences();
  const tUi = useUiText();
  return <Box>
    <Box component="figure" sx={{ display: { xs: 'none', md: preset === 'lime' ? 'none' : 'block' }, m: 0, mb: 3 }}>
    <Box sx={{ overflow: 'hidden', borderRadius: preset === 'cyan' ? 3 : 1, height: preset === 'cyan' ? 180 : 120, bgcolor: 'action.hover' }}>
      <Box component="img" src="/static/visuals/coast-800.webp" srcSet="/static/visuals/coast-800.webp 800w, /static/visuals/coast-1600.webp 1600w" sizes="(min-width: 1280px) 1200px, 100vw" alt="" width={1600} height={901} decoding="async" sx={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: '50% 55%' }} />
    </Box>
    <Typography component="figcaption" variant="caption" color="text.secondary">{tUi('Generic nature illustration')}</Typography>
    </Box>
    <LiveTV home /><TVDashboard embedded />
  </Box>;
}

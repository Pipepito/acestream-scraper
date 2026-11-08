import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useUiText } from '../../i18n/useUiText';
import { useAppPreferences } from '../../preferences/AppPreferences';

/** Decoration follows source taxonomy. It never stands in for event artwork or signal. */
export default function SportIllustration({ sport }: { sport?: string }) {
  const tUi = useUiText();
  const { interface: preset } = useAppPreferences();
  const [failedSource, setFailedSource] = useState('');
  const name = (sport ?? '').trim().toLocaleLowerCase('en');
  const category = ['football', 'soccer', 'fútbol', 'futbol'].includes(name) ? 'football'
    : ['tennis', 'tenis'].includes(name) ? 'tennis' : null;
  if (!category) return null;
  const src = `/static/visuals/${category}-480.webp`;
  const failed = failedSource === src;
  return <Box component="figure" sx={{ m: 0, width: '100%', maxWidth: preset === 'lime' ? 240 : preset === 'coral' ? 480 : 720 }}>
    <Box sx={{ aspectRatio: preset === 'lime' ? '3 / 1' : '16 / 8', bgcolor: 'action.hover', overflow: 'hidden', borderRadius: preset === 'cyan' ? 2 : 0.5, display: 'grid', placeItems: 'center' }}>
      {failed ? <Typography variant="body2" color="text.secondary">{tUi('Illustration unavailable')}</Typography> : <Box component="img" src={src}
        srcSet={category === 'football' ? '/static/visuals/football-480.webp 480w, /static/visuals/football-960.webp 960w' : undefined}
        sizes={preset === 'lime' ? '240px' : '(max-width: 600px) 100vw, 720px'}
        width={480} height={category === 'football' ? 322 : 360} alt="" loading="lazy" decoding="async"
        onError={() => setFailedSource(src)} sx={{ width: '100%', height: '100%', objectFit: 'cover' }} />}
    </Box>
    <Typography component="figcaption" variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
      {category === 'football' ? tUi('Generic football illustration') : tUi('Generic tennis illustration')}
    </Typography>
  </Box>;
}

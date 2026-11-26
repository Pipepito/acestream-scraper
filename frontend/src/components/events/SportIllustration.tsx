import React from 'react';
import { Box } from '@mui/material';
import { useUiText } from '../../i18n/useUiText';
import { useAppPreferences } from '../../preferences/AppPreferences';
import { sportArtwork } from '../../artwork/categoryArtwork';
import CategoryArtwork from '../CategoryArtwork';

/** Decoration follows source taxonomy. It never stands in for event artwork or signal. */
export default function SportIllustration({ sport }: { sport?: string }) {
  const tUi = useUiText();
  const { interface: preset } = useAppPreferences();
  const category = sportArtwork(sport);
  if (!category) return null;
  return <Box sx={{ width: '100%', maxWidth: preset === 'lime' ? 240 : preset === 'coral' ? 480 : 720 }}>
    <CategoryArtwork artwork={category} compact={preset === 'lime'}
      sizes={preset === 'lime' ? '240px' : '(max-width: 600px) 100vw, 720px'}
      caption={category === 'football' ? tUi('Generic football illustration') : category === 'tennis' ? tUi('Generic tennis illustration') : tUi('Generic sport illustration')} />
  </Box>;
}

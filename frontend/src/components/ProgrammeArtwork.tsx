import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useUiText } from '../i18n/useUiText';

/** Optional metadata image. Failure never removes the programme name or actions. */
export default function ProgrammeArtwork({ src, alt = '' }: { src?: string | null; alt?: string }) {
  const [failed, setFailed] = useState<string | null>(null);
  const tUi = useUiText();
  if (!src) return null;
  try {
    if (!['http:', 'https:'].includes(new URL(src, window.location.href).protocol)) return null;
  } catch { return null; }
  if (failed === src) return <Box sx={{ aspectRatio: '16 / 9', bgcolor: 'action.hover', borderRadius: 'inherit', mb: 1.5, display: 'grid', placeItems: 'center' }}>
    <Typography variant="caption" color="text.secondary">{tUi('Artwork unavailable')}</Typography>
  </Box>;
  return <Box component="img" src={src} alt={alt} loading="lazy" decoding="async" referrerPolicy="no-referrer"
    onError={() => setFailed(src)} width={480} height={270}
    sx={{ display: 'block', width: '100%', height: 'auto', aspectRatio: '16 / 9', objectFit: 'cover', borderRadius: 'inherit', mb: 1.5 }} />;
}

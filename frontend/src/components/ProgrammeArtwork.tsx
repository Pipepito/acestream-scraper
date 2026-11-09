import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { useUiText } from '../i18n/useUiText';

interface ProgrammeArtworkProps {
  src?: string | null;
  alt?: string;
  fallback?: React.ReactNode;
}

/** Real programme artwork wins; optional decoration stays explicitly labelled by its owner. */
export default function ProgrammeArtwork({ src, alt = '', fallback }: ProgrammeArtworkProps) {
  const [failed, setFailed] = useState<string | null>(null);
  const tUi = useUiText();
  if (!src) return <>{fallback ?? null}</>;
  try {
    if (!['http:', 'https:'].includes(new URL(src, window.location.href).protocol)) return <>{fallback ?? null}</>;
  } catch { return <>{fallback ?? null}</>; }
  if (failed === src) return <>{fallback ?? <Box sx={{ aspectRatio: '16 / 9', bgcolor: 'action.hover', borderRadius: 'inherit', mb: 1.5, display: 'grid', placeItems: 'center' }}>
    <Typography variant="caption" color="text.secondary">{tUi('Artwork unavailable')}</Typography>
  </Box>}</>;
  return <Box component="img" src={src} alt={alt} loading="lazy" decoding="async" referrerPolicy="no-referrer"
    onError={() => setFailed(src)} width={480} height={270}
    sx={{ display: 'block', width: '100%', height: 'auto', aspectRatio: '16 / 9', objectFit: 'cover', borderRadius: 'inherit', mb: 1.5 }} />;
}

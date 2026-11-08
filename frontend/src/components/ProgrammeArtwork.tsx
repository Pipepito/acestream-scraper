import React, { useState } from 'react';
import { Box } from '@mui/material';

/** Optional metadata image. Failure never removes the programme name or actions. */
export default function ProgrammeArtwork({ src, alt = '' }: { src?: string | null; alt?: string }) {
  const [failed, setFailed] = useState<string | null>(null);
  if (!src || failed === src) return null;
  try {
    if (!['http:', 'https:'].includes(new URL(src, window.location.href).protocol)) return null;
  } catch { return null; }
  return <Box component="img" src={src} alt={alt} loading="lazy" decoding="async" referrerPolicy="no-referrer"
    onError={() => setFailed(src)} width={480} height={270}
    sx={{ display: 'block', width: '100%', height: 'auto', aspectRatio: '16 / 9', objectFit: 'cover', borderRadius: 'inherit', mb: 1.5 }} />;
}

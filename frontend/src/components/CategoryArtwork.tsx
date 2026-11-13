import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { artworkSource, type ArtworkKey } from '../artwork/categoryArtwork';
import { useUiText } from '../i18n/useUiText';

interface CategoryArtworkProps {
  artwork: ArtworkKey;
  caption: string;
  sizes?: string;
  compact?: boolean;
}

/** Local decoration only; never a programme poster, channel logo or signal indicator. */
export default function CategoryArtwork({ artwork, caption, sizes = '(max-width: 600px) 100vw, 480px', compact = false }: CategoryArtworkProps) {
  const tUi = useUiText();
  const [failed, setFailed] = useState<ReadonlySet<string>>(() => new Set());
  const selected = artworkSource(artwork);
  const source = failed.has(selected.src) ? artworkSource('neutral') : selected;
  const unavailable = failed.has(source.src);
  return <Box component="figure" sx={{ m: 0, mb: 1.5, minWidth: 0 }}>
    <Box sx={{ aspectRatio: compact ? '3 / 1' : '16 / 9', borderRadius: 1, overflow: 'hidden', bgcolor: 'action.hover', display: 'grid', placeItems: 'center' }}>
      {unavailable ? <Typography variant="caption" color="text.secondary">{tUi('Illustration unavailable')}</Typography> :
        <Box component="img" src={source.src} srcSet={source.srcSet} sizes={sizes} width={source.width} height={source.height}
          alt="" loading="lazy" decoding="async"
          onError={() => setFailed(previous => new Set(previous).add(source.src))}
          sx={{ display: 'block', width: '100%', height: '100%', objectFit: compact ? 'contain' : 'cover' }} />}
    </Box>
    <Typography component="figcaption" variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, overflowWrap: 'anywhere' }}>{caption}</Typography>
  </Box>;
}

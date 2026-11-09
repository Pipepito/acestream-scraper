import React, { useState } from 'react';
import { Box } from '@mui/material';
import type { TVChannel } from '../../types/tvChannelTypes';
import { useUiText } from '../../i18n/useUiText';
import { channelArtwork } from '../../artwork/categoryArtwork';
import CategoryArtwork from '../CategoryArtwork';

/** Channel identity never depends on the current programme or its artwork. */
export default function ChannelArtwork({ channel, compact = false }: { channel: TVChannel; compact?: boolean }) {
  const tUi = useUiText();
  const [failed, setFailed] = useState<string[]>([]);
  const source = [channel.logo_url, channel.epg_logo_url].find(url => {
    if (!url || failed.includes(url)) return false;
    try { return ['http:', 'https:'].includes(new URL(url, window.location.href).protocol); } catch { return false; }
  });
  return <Box sx={{ width: compact ? 72 : '100%', flexShrink: 0, aspectRatio: compact ? '1' : '16/9', overflow: 'hidden', borderRadius: 1.5, bgcolor: 'background.default', display: 'grid', placeItems: 'center' }}>
    {source ? <Box component="img" key={source} src={source} alt={channel.name} loading="lazy" decoding="async" referrerPolicy="no-referrer"
      onError={() => setFailed(previous => [...previous, source])}
      sx={{ display: 'block', width: '100%', height: '100%', minHeight: 0, objectFit: 'contain', p: compact ? 1 : 3 }} />
      : <CategoryArtwork artwork={channelArtwork(channel.category_id ?? channel.category)}
        caption={channel.category ? tUi('Channel category illustration · {{category}}', { category: channel.category }) : tUi('Generic channel illustration')}
        sizes={compact ? '72px' : '(min-width: 900px) 33vw, 100vw'} />}
  </Box>;
}

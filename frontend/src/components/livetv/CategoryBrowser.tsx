import React from 'react';
import { Alert, Box, Button, Card, CardActionArea, LinearProgress, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import ArrowBackRounded from '@mui/icons-material/ArrowBackRounded';
import { useTranslation } from 'react-i18next';
import { useUiText } from '../../i18n/useUiText';
import type { CategoryInventory } from '../../services/tvChannelService';
import { resolvedArtwork } from '../../artwork/categoryArtwork';
import CategoryArtwork from '../CategoryArtwork';

interface Props {
  basis: 'channel' | 'now';
  selected: string;
  data?: CategoryInventory;
  loading: boolean;
  error: boolean;
  onRetry: () => void;
  onBasis: (basis: 'channel' | 'now') => void;
  onSelect: (id: string) => void;
}

export default function CategoryBrowser({ basis, selected, data, loading, error, onRetry, onBasis, onSelect }: Props) {
  const tUi = useUiText();
  const { i18n } = useTranslation();
  const label = (item: CategoryInventory['items'][number]) => i18n.resolvedLanguage?.startsWith('es') ? item.label_es : item.label;
  const active = data?.items.find(item => item.id === selected);
  return <Stack spacing={2} sx={{ mb: 2 }}>
    <ToggleButtonGroup exclusive size="small" value={basis} aria-label={tUi('Category browsing')} onChange={(_, value: 'channel' | 'now' | null) => { if (value) onBasis(value); }}>
      <ToggleButton value="channel">{tUi('Channel categories')}</ToggleButton>
      <ToggleButton value="now">{tUi('On now')}</ToggleButton>
    </ToggleButtonGroup>
    <Typography variant="body2" color="text.secondary">{basis === 'channel' ? tUi('Browse by the channel’s usual content.') : tUi('Discover current programmes by genre. Channel categories stay unchanged.')}</Typography>
    {loading ? <LinearProgress aria-label={tUi('Loading categories')} /> : null}
    {error ? <Alert severity="error" action={<Button onClick={onRetry}>{tUi('Retry')}</Button>}>{tUi('Unable to load categories.')}</Alert> : null}
    {selected ? <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
      <Button startIcon={<ArrowBackRounded />} onClick={() => onSelect('')}>{tUi('Categories')}</Button>
      <Typography component="h2" variant="h6">{selected === 'all' ? tUi('All channels') : active ? label(active) : tUi('Selected category')}</Typography>
    </Stack> : data ? <>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography component="h2" variant="h6">{basis === 'channel' ? tUi('Channel categories') : tUi('On now')}</Typography>
        <Button onClick={() => onSelect('all')}>{tUi('All channels')} · {data.total}</Button>
      </Stack>
      {!data.items.length ? <Alert severity="info">{tUi('No channels match these filters.')}</Alert> : null}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, minmax(0, 1fr))', sm: 'repeat(3, minmax(0, 1fr))', lg: 'repeat(4, minmax(0, 1fr))' }, gap: { xs: 1, sm: 2 } }}>
        {data.items.map(item => <Card key={item.id} variant="outlined" sx={{ minWidth: 0 }}>
          <CardActionArea onClick={() => onSelect(item.id)} sx={{ height: '100%' }}>
            <CategoryArtwork artwork={resolvedArtwork(item.artwork)} caption={tUi('Category illustration')} sizes="(min-width: 1200px) 25vw, (min-width: 600px) 33vw, 50vw" />
            <Box sx={{ p: { xs: 1.5, sm: 2 } }}>
              <Typography component="h3" variant="h6" sx={{ overflowWrap: 'anywhere' }}>{label(item)}</Typography>
              <Typography variant="body2" color="text.secondary">{tUi('{{count}} channels', { count: item.count })}</Typography>
            </Box>
          </CardActionArea>
        </Card>)}
      </Box>
    </> : null}
  </Stack>;
}

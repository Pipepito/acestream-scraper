import { formatCount } from '../../i18n/locale';
import { translateKnown } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import { uiText } from '../../i18n/text';
import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { Stats, TvChannelStats } from '../../services/configService';

export interface InventoryTotalsProps {
  stats?: Stats;
  tvStats?: TvChannelStats;
}

interface Group {
  title: string;
  rows: Array<[string, number | string]>;
}

/** Three short definition lists: what the app holds right now. */
const InventoryTotals: React.FC<InventoryTotalsProps> = ({ stats, tvStats }) => {
  useUiText();
  const theme = useTheme();
  const groups: Group[] = [
    {
      title: uiText("Streams"),
      rows: stats ? [
        ['Total', stats.channels.total],
        ['Online', stats.channels.online],
        ['Offline', stats.channels.offline],
        ['Not checked yet', stats.channels.unknown],
      ] : [['Total', 'Unavailable']],
    },
    {
      title: uiText("TV channels"),
      rows: tvStats
        ? [
            ['Total', tvStats.total],
            ['Active', tvStats.active],
            ['With EPG', tvStats.with_epg],
            ['Streams linked', tvStats.acestreams],
          ]
        : [['Total', '—']],
    },
    {
      title: uiText("Sources and guide"),
      rows: stats ? [
        ['Source URLs', stats.urls.error ? uiText('{{total}} ({{enabled}} enabled, {{failing}} failing)', { total: stats.urls.total, enabled: stats.urls.active, failing: stats.urls.error }) : uiText('{{total}} ({{enabled}} enabled)', { total: stats.urls.total, enabled: stats.urls.active })],
        ['EPG sources', stats.epg.sources],
        ['Guide channels', stats.epg.channels],
        ['Programmes', stats.epg.programs],
      ] : [['Sources and guide', 'Unavailable']],
    },
  ];
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' }, gap: 3 }}>
      {groups.map((group) => (
        <Box key={translateKnown(group.title)} component="section" aria-label={translateKnown(group.title)}>
          <Typography variant="subtitle2" component="h3" sx={{ mb: 1 }}>
            {translateKnown(group.title)}
          </Typography>
          <Box component="dl" sx={{ m: 0, display: 'grid', gridTemplateColumns: 'auto 1fr', columnGap: 2, rowGap: 0.5 }}>
            {group.rows.map(([label, value]) => (
              <React.Fragment key={translateKnown(label)}>
                <Typography component="dt" variant="body2" sx={{ color: 'text.secondary' }}>
                  {translateKnown(label)}
                </Typography>
                <Typography component="dd" variant="body2" sx={{ m: 0, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: theme.palette.text.primary }}>
                  {typeof value === 'number' ? formatCount(value) : translateKnown(value)}
                </Typography>
              </React.Fragment>
            ))}
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export default InventoryTotals;

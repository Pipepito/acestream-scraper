import React from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { Stats, TvChannelStats } from '../../services/configService';

export interface InventoryTotalsProps {
  stats: Stats;
  tvStats?: TvChannelStats;
}

interface Group {
  title: string;
  rows: Array<[string, number | string]>;
}

/** Three short definition lists: what the app holds right now. */
const InventoryTotals: React.FC<InventoryTotalsProps> = ({ stats, tvStats }) => {
  const theme = useTheme();
  const groups: Group[] = [
    {
      title: 'Streams',
      rows: [
        ['Total', stats.channels.total],
        ['Online', stats.channels.online],
        ['Offline', stats.channels.offline],
        ['Not checked yet', stats.channels.unknown],
      ],
    },
    {
      title: 'TV channels',
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
      title: 'Sources and guide',
      rows: [
        ['Source URLs', `${stats.urls.total} (${stats.urls.active} enabled${stats.urls.error ? `, ${stats.urls.error} failing` : ''})`],
        ['EPG sources', stats.epg.sources],
        ['Guide channels', stats.epg.channels],
        ['Programmes', stats.epg.programs],
      ],
    },
  ];
  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, minmax(0, 1fr))' }, gap: 3 }}>
      {groups.map((group) => (
        <Box key={group.title} component="section" aria-label={group.title}>
          <Typography variant="subtitle2" component="h3" sx={{ mb: 1 }}>
            {group.title}
          </Typography>
          <Box component="dl" sx={{ m: 0, display: 'grid', gridTemplateColumns: 'auto 1fr', columnGap: 2, rowGap: 0.5 }}>
            {group.rows.map(([label, value]) => (
              <React.Fragment key={label}>
                <Typography component="dt" variant="body2" sx={{ color: 'text.secondary' }}>
                  {label}
                </Typography>
                <Typography component="dd" variant="body2" sx={{ m: 0, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: theme.palette.text.primary }}>
                  {value}
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

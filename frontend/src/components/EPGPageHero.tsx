import React from 'react';
import { Box, Stack, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';

interface EPGPageHeroProps {
  sourceCount: number;
  enabledSourceCount: number;
  unmappedVisibleCount: number;
}

const EPGPageHero: React.FC<EPGPageHeroProps> = ({ sourceCount, enabledSourceCount, unmappedVisibleCount }) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        mb: 3,
        p: { xs: 2, md: 2.5 },
        borderRadius: 2.5,
        bgcolor: theme.appTokens.hero.bg,
        border: `1px solid ${theme.appTokens.hero.border}`,
        backgroundImage: theme.appTokens.hero.spotlight,
      }}
    >
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'space-between' }}>
        <Box sx={{ minWidth: 0, maxWidth: 760 }}>
          <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent, mb: 1 }}>
            EPG pulse
          </Typography>
          <Typography variant="h4" sx={{ letterSpacing: '-0.03em', mb: 1 }}>
            Source inventory is ready for matching and XML output.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Use this page to confirm source coverage, review unmapped channels, and move into XML generation only when the feed inventory looks reliable.
          </Typography>
        </Box>
        <Stack spacing={1} sx={{ minWidth: { xs: '100%', sm: 300 } }}>
          <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha(theme.appTokens.shell.accent, 0.08), border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}` }}>
            <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>Source count</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>{sourceCount} sources total, {enabledSourceCount} enabled.</Typography>
          </Box>
          <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha(theme.appTokens.hero.accent, 0.1), border: `1px solid ${alpha(theme.appTokens.hero.accent, 0.24)}` }}>
            <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>Matching status</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>{unmappedVisibleCount} visible channels still need review or creation.</Typography>
          </Box>
          <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: theme.appTokens.surface.panel, border: `1px solid ${theme.appTokens.surface.border}` }}>
            <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>Next step</Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Review unmapped channels or generate XML when source coverage looks right.
            </Typography>
          </Box>
        </Stack>
      </Box>
    </Box>
  );
};

export default EPGPageHero;

import React, { useMemo } from 'react';
import { Box, Stack, Typography, useTheme } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { TVChannel } from '../types/tvChannelTypes';

interface TVChannelsPageHeroProps {
  channelCount: number;
  filteredChannels: TVChannel[];
}

const TVChannelsPageHero: React.FC<TVChannelsPageHeroProps> = ({ channelCount, filteredChannels }) => {
  const theme = useTheme();

  const totalChannels = filteredChannels.length;
  const filteredActiveCount = useMemo(() => filteredChannels.filter((channel) => channel.is_active).length, [filteredChannels]);
  const filteredInactiveCount = totalChannels - filteredActiveCount;
  const filteredCategoryCount = useMemo(
    () => new Set(filteredChannels.map((channel) => channel.category).filter(Boolean)).size,
    [filteredChannels]
  );
  const outputReadinessLabel =
    channelCount === 0
      ? 'No TV channels are organized yet, so downstream output work cannot start.'
      : totalChannels === 0
        ? 'The current filters hide the organized catalog, so reset them before continuing downstream.'
        : `${totalChannels} organized TV channel${totalChannels === 1 ? '' : 's'} in view with ${filteredActiveCount} active and ${filteredInactiveCount} inactive.`;
  const organizationSupportLabel =
    filteredCategoryCount > 0
      ? `${filteredCategoryCount} categor${filteredCategoryCount === 1 ? 'y is' : 'ies are'} represented in this working set.`
      : 'Categories appear here once channel metadata is organized.';
  const nextStepLabel =
    totalChannels === 0
      ? 'Reset filters or add channels so you can continue organizing the catalog.'
      : 'Organize the final catalog before moving into EPG and output workflows.';

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
      <Stack spacing={2}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'space-between' }}>
          <Box sx={{ minWidth: 0, maxWidth: 760 }}>
            <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent, mb: 1 }}>
              TV organization stage
            </Typography>
            <Typography variant="h4" sx={{ letterSpacing: '-0.03em', mb: 1 }}>
              Organize the downstream catalog before you hand it off to EPG and output workflows.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Keep the inventory first, confirm what stays active, and use filters as a support tool when the catalog needs cleanup.
            </Typography>
          </Box>
          <Stack spacing={1} sx={{ minWidth: { xs: '100%', sm: 320 } }}>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: alpha(theme.appTokens.shell.accent, 0.08),
                border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}`,
              }}
            >
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                Output readiness
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {outputReadinessLabel}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {organizationSupportLabel}
              </Typography>
            </Box>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: theme.appTokens.surface.panel,
                border: `1px solid ${theme.appTokens.surface.border}`,
              }}
            >
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                Next step guidance
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {nextStepLabel}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Use the organized inventory to spot stale entries, confirm active channels, and prepare safer downstream decisions.
              </Typography>
            </Box>
          </Stack>
        </Box>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.25 }}>
          {[
            {
              title: 'Sources',
              label: 'Upstream intake stage',
              body: 'Source intake feeds the catalog that eventually reaches TV organization.',
              active: false,
            },
            {
              title: 'Extracted channels',
              label: 'Upstream review stage',
              body: 'Extracted-channel review shapes what enters the organized TV catalog.',
              active: false,
            },
            {
              title: 'TV organization',
              label: 'Current downstream stage',
              body: 'Organize the final catalog for EPG and output workflows.',
              active: true,
            },
          ].map((stage) => (
            <Box
              key={stage.title}
              sx={{
                flex: '1 1 180px',
                minWidth: { xs: '100%', sm: 180 },
                p: 1.5,
                borderRadius: 2,
                bgcolor: stage.active ? alpha(theme.appTokens.hero.accent, 0.10) : theme.appTokens.surface.panel,
                border: `1px solid ${stage.active ? alpha(theme.appTokens.hero.accent, 0.24) : theme.appTokens.surface.border}`,
              }}
            >
              <Typography variant="statusMeta" sx={{ color: stage.active ? theme.appTokens.hero.accent : 'text.secondary', mb: 0.75 }}>
                {stage.label}
              </Typography>
              <Typography variant="sectionTitle" sx={{ mb: 0.5 }}>
                {stage.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stage.body}
              </Typography>
            </Box>
          ))}
        </Box>
      </Stack>
    </Box>
  );
};

export default TVChannelsPageHero;

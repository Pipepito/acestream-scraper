import React from 'react';
import { Box, Stack, Typography } from '@mui/material';
import PageHeader from './layout/PageHeader';
import ContentSection from './layout/ContentSection';

interface LegacyRouteRecoveryProps {
  title: string;
  summary: string;
  sectionTitle: string;
  sectionDescription: string;
  actions: React.ReactNode;
  statusLine: string;
  supportingText: string;
}

const LegacyRouteRecovery: React.FC<LegacyRouteRecoveryProps> = ({
  title,
  summary,
  sectionTitle,
  sectionDescription,
  actions,
  statusLine,
  supportingText,
}) => {
  return (
    <Box sx={{ maxWidth: 760 }}>
      <PageHeader title={title} subtitle={summary} />

      <ContentSection title={sectionTitle} description={sectionDescription}>
        <Stack spacing={1}>
          <Typography variant="body2" color="text.primary">
            {statusLine}
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 1,
              alignItems: 'center',
              '& > *': {
                minWidth: 0,
                maxWidth: '100%',
              },
            }}
          >
            {actions}
          </Box>
          <Typography variant="body2" color="text.secondary">
            {supportingText}
          </Typography>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default LegacyRouteRecovery;

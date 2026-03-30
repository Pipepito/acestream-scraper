import React from 'react';
import { Box, Typography } from '@mui/material';
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

      <ContentSection title={sectionTitle} description={sectionDescription} actions={actions}>
        <Box>
          <Typography variant="body2" color="text.primary" sx={{ mb: 1 }}>
            {statusLine}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {supportingText}
          </Typography>
        </Box>
      </ContentSection>
    </Box>
  );
};

export default LegacyRouteRecovery;

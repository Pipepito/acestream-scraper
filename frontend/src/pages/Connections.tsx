import React from 'react';
import { Box, Button, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { connectionLinks } from '../components/layout/SectionNavigation';

export default function Connections() {
  const { t } = useTranslation();
  return <>
    <PageHeader title={t('connections')} />
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))' }, gap: 2 }}>
      {connectionLinks.map(link => <ContentSection key={link.to}>
        <Typography component="h2" variant="h6">{t(link.label)}</Typography>
        <Button component={Link} to={link.to} sx={{ mt: 2 }}>{t(link.label)} →</Button>
      </ContentSection>)}
    </Box>
  </>;
}

import React from 'react';
import { Box, Button, Stack } from '@mui/material';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import InterfaceSelector from '../components/InterfaceSelector';
import type { SectionLink } from '../components/layout/SectionNavigation';

const editors: SectionLink[] = [
  { label: 'access', to: '/settings?tab=access' }, { label: 'automation', to: '/settings?tab=automation' },
  { label: 'recordings', to: '/recordings?tab=settings' }, { label: 'thisBrowser', to: '/integrations/web-player' },
  { label: 'streamLinks', to: '/settings?tab=links' }, { label: 'connections', to: '/connections' },
  { label: 'runtime', to: '/system/runtime' }, { label: 'system', to: '/system' },
];
export default function SettingsIndex() {
  const { t } = useTranslation();
  return <Box><PageHeader title={t('settings')} />
    <ContentSection title={t('interface')}><InterfaceSelector /></ContentSection>
    <Stack component="nav" aria-label={t('settings')} spacing={1}>
      {editors.map(editor => <Button key={editor.to} component={Link} to={editor.to} variant="outlined" sx={{ justifyContent: 'space-between', p: 2 }}>{t(editor.label)} <span aria-hidden>→</span></Button>)}
    </Stack>
  </Box>;
}

import { useUiText } from '../i18n/useUiText';
import React from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const NotFound: React.FC = () => {
  const tUi = useUiText();
  const navigate = useNavigate();
  
  return (
    <Box sx={{ maxWidth: 720 }}>
      <PageHeader
        title={tUi("Page not found")}
        subtitle={tUi("This is an unsupported or outdated route, so restart from a supported workspace.")}
      />
      <ContentSection
        title={tUi("Go to a supported workflow")}
        description={tUi("If this came from an old bookmark, stale link, or unsupported path, use one of the current routes below.")}
      >
        <Stack spacing={1}>
          <Typography variant="body2" color="text.primary">
            {tUi("Unsupported route: restart from Dashboard, TV Channels, or Search.")}</Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="contained" color="primary" onClick={() => navigate('/', { replace: true })}>
              {tUi("Open Dashboard")}</Button>
            <Button variant="outlined" color="primary" onClick={() => navigate('/tv-channels', { replace: true })}>
              {tUi("Open TV Channels")}</Button>
            <Button variant="outlined" color="primary" onClick={() => navigate('/search', { replace: true })}>
              {tUi("Open Search")}</Button>
          </Stack>
          <Typography variant="body2" color="text.secondary">
            {tUi("Use one of the supported routes below to recover quickly from an outdated link or path.")}</Typography>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default NotFound;

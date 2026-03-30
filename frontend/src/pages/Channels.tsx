import React from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const Channels: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{ maxWidth: 760 }}>
      <PageHeader
        title="Channels"
        subtitle="This legacy route has moved. Use the current inventory pages to manage channels and continue with a supported workflow."
      />
      <ContentSection
        title="Continue in TV Channels"
        description="Legacy channels route. Open TV Channels for the active channel workflow."
        actions={
          <Button variant="contained" onClick={() => navigate('/tv-channels')}>
            Open TV Channels
          </Button>
        }
      >
        <Stack spacing={2}>
          <Typography variant="body2" color="text.primary">
            Channel management moved into the current inventory views.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Acestream Channels remains available for source inventory checks after you get back into the supported flow.
          </Typography>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default Channels;

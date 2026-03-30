import React from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const ChannelDetail: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{ maxWidth: 760 }}>
      <PageHeader
        title="Channel detail"
        subtitle="This legacy detail route is no longer the active workflow. Use the current list pages to reopen supported channel detail views."
      />
      <ContentSection
        title="Continue in TV Channels"
        description="Legacy channel detail route. Open TV Channels to return to the supported channel detail path."
        actions={
          <Button variant="contained" onClick={() => navigate('/tv-channels')}>
            Open TV Channels
          </Button>
        }
      >
        <Stack spacing={2}>
          <Typography variant="body2" color="text.primary">
            This route is no longer the active workflow for single-channel work.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            EPG is the secondary path when you need schedule data or guide mapping.
          </Typography>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default ChannelDetail;

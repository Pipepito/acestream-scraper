import React from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <Box sx={{ maxWidth: 720 }}>
      <PageHeader
        title="Page not found"
        subtitle="This is an unsupported or outdated route. Return to the dashboard to restart from a supported operational view."
      />
      <ContentSection
        title="Go to a supported workflow"
        description="If this came from an old bookmark, stale link, or unsupported path, use one of the current routes below."
        actions={
          <>
            <Button variant="contained" color="primary" onClick={() => navigate('/', { replace: true })}>
              Open Dashboard
            </Button>
            <Button variant="outlined" color="primary" onClick={() => navigate('/tv-channels', { replace: true })}>
              Open TV Channels
            </Button>
            <Button variant="outlined" color="primary" onClick={() => navigate('/search', { replace: true })}>
              Open Search
            </Button>
          </>
        }
      >
        <Stack spacing={1} sx={{ color: 'text.secondary' }}>
          <Typography variant="body2">
            Dashboard is the fastest recovery path when you need to reorient or confirm the current workflow.
          </Typography>
          <Typography variant="body2">
            TV Channels and Search are also likely destinations if you were trying to recover inventory or continue lookup work.
          </Typography>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default NotFound;

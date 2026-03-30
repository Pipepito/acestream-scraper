import React from 'react';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const SearchNew: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box sx={{ maxWidth: 760 }}>
      <PageHeader
        title="Search"
        subtitle="This old search path has moved. Continue in the current Search workflow to find channels with the supported tools."
      />
      <ContentSection
        title="Continue in Search"
        description="Legacy search route. Open Search to continue in the current channel lookup workflow."
        actions={
          <Button variant="contained" onClick={() => navigate('/search')}>
            Open Search
          </Button>
        }
      >
        <Stack spacing={2}>
          <Typography variant="body2" color="text.primary">
            The active search workflow now lives on the main Search page.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Old bookmarks can still land here, but this route is no longer the active search entry.
          </Typography>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default SearchNew;

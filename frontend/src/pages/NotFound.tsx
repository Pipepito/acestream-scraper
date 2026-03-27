import React from 'react';
import { Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <Box sx={{ maxWidth: 720 }}>
      <PageHeader
        title="Page not found"
        subtitle="The address you opened does not match a current route. Use the action below to return to the main operational view."
      />
      <ContentSection
        title="Get back on track"
        description="Return to the dashboard, then use the left navigation to continue with a supported workflow."
        actions={
          <Button variant="contained" color="primary" onClick={() => navigate('/')}>
            Return to dashboard
          </Button>
        }
      >
        <Box sx={{ typography: 'body2', color: 'text.secondary' }}>
          Error code: 404. If you followed an old bookmark or external link, refresh your starting point from the dashboard.
        </Box>
      </ContentSection>
    </Box>
  );
};

export default NotFound;

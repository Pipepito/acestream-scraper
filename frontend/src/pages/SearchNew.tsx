import React from 'react';
import { Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LegacyRouteRecovery from '../components/LegacyRouteRecovery';

const SearchNew: React.FC = () => {
  const navigate = useNavigate();

  return (
    <LegacyRouteRecovery
      title="Search"
      summary="This legacy route has moved. Continue in the current Search workflow to find channels from the supported path."
      sectionTitle="Continue in the supported search flow"
      sectionDescription="Open the main Search page to keep working with the active search experience."
      actions={
        <Button variant="contained" onClick={() => navigate('/search')}>
          Open Search
        </Button>
      }
      statusLine="Legacy route: search now runs from the main Search workflow."
      supportingText="Use the current search page instead of this older entry point."
    />
  );
};

export default SearchNew;

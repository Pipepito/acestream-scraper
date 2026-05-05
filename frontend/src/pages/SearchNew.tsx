/**
 * Legacy redirect page mounted at /search-new. The original v1 search route
 * lived here; v2 consolidated everything into the canonical /search page.
 * This component renders LegacyRouteRecovery (the shared shell used by the
 * other legacy redirects under src/components/LegacyRouteRecovery.tsx) and
 * exposes a single "Open Search" affordance that bumps the user to /search.
 *
 * Keep this file as a route handler — inlining the redirect into App.tsx
 * would lose the operator-facing recovery messaging, which is the point of
 * the LegacyRouteRecovery pattern: explain to the user *why* they were sent
 * elsewhere instead of bouncing them silently.
 */
import React from 'react';
import { Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LegacyRouteRecovery from '../components/LegacyRouteRecovery';

const SearchNew: React.FC = () => {
  const navigate = useNavigate();

  return (
    <LegacyRouteRecovery
      title="Search"
      summary="This route moved, so continue in Search from the supported path."
      sectionTitle="Continue in the supported search flow"
      sectionDescription="Open the main Search page to keep working with the active search experience."
      actions={
        <Button variant="contained" onClick={() => navigate('/search')}>
          Open Search
        </Button>
      }
      statusLine="Legacy route: continue from the main Search workflow."
      supportingText="Use the current search page instead of this older entry point."
    />
  );
};

export default SearchNew;

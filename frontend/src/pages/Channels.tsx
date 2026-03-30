import React from 'react';
import { Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LegacyRouteRecovery from '../components/LegacyRouteRecovery';

const Channels: React.FC = () => {
  const navigate = useNavigate();

  return (
    <LegacyRouteRecovery
      title="Channels"
      summary="This route now redirects to the supported channel inventory so you can restart from the current workflow."
      sectionTitle="Go to the current channel views"
      sectionDescription="Open TV Channels for the primary inventory path. Acestream Channels remains separate when you need source-level context."
      actions={
        <Button variant="contained" onClick={() => navigate('/tv-channels')}>
          Open TV Channels
        </Button>
      }
      statusLine="Legacy route: recover channel work from TV Channels."
      supportingText="Use the supported inventory routes instead of this older entry point."
    />
  );
};

export default Channels;

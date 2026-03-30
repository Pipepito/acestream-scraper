import React from 'react';
import { Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LegacyRouteRecovery from '../components/LegacyRouteRecovery';

const Channels: React.FC = () => {
  const navigate = useNavigate();

  return (
    <LegacyRouteRecovery
      title="Channels"
      summary="This legacy route has moved. Use the current channel inventory views to keep working in a supported workflow."
      sectionTitle="Go to the current channel views"
      sectionDescription="Open TV Channels for the main inventory path. If you need source-level context, check Acestream Channels separately."
      actions={
        <Button variant="contained" onClick={() => navigate('/tv-channels')}>
          Open TV Channels
        </Button>
      }
      statusLine="Legacy route: channel management now lives in TV Channels."
      supportingText="Use the modern inventory routes instead of this older entry point."
    />
  );
};

export default Channels;

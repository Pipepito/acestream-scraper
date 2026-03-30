import React from 'react';
import { Button, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LegacyRouteRecovery from '../components/LegacyRouteRecovery';

const ChannelDetail: React.FC = () => {
  const navigate = useNavigate();

  return (
    <LegacyRouteRecovery
      title="Channel detail"
      summary="This detail route is no longer active, so reopen the item from a supported list before continuing."
      sectionTitle="Choose a supported channel workflow"
      sectionDescription="Open TV Channels for the main recovery path, or open EPG if you were returning through guide-based channel work."
      actions={
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <Button variant="contained" onClick={() => navigate('/tv-channels')}>
            Open TV Channels
          </Button>
          <Button variant="outlined" onClick={() => navigate('/epg')}>
            Open EPG
          </Button>
        </Stack>
      }
      statusLine="Legacy detail route: reopen the item from TV Channels or EPG."
      supportingText="Use a current list first, then return to the detail screen from there."
    />
  );
};

export default ChannelDetail;

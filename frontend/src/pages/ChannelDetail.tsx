import React from 'react';
import { Button, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import LegacyRouteRecovery from '../components/LegacyRouteRecovery';

const ChannelDetail: React.FC = () => {
  const navigate = useNavigate();

  return (
    <LegacyRouteRecovery
      title="Channel detail"
      summary="This legacy detail route is no longer the active workflow. Use the supported channel lists to reopen the item from a current path."
      sectionTitle="Choose a supported channel workflow"
      sectionDescription="Open TV Channels for the primary recovery path, or open EPG if you were trying to continue through guide-based channel details."
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
      statusLine="Legacy detail route: this page no longer maps directly to a supported detail screen."
      supportingText="Return to the current lists, then open the channel again from TV Channels or EPG."
    />
  );
};

export default ChannelDetail;

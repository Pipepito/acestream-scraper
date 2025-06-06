import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const Channels: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Channels
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          This page will display all available Acestream channels.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Channels;

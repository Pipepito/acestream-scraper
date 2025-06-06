import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const EPG: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        EPG
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          This page will provide Electronic Program Guide (EPG) management functionality.
        </Typography>
      </Paper>
    </Box>
  );
};

export default EPG;

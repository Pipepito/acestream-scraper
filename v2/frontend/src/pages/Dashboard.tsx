import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          Welcome to the Acestream Scraper Dashboard. This is the main control panel for the application.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Dashboard;

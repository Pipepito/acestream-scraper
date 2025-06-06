import React from 'react';
import { Typography, Box, Paper } from '@mui/material';

const Scraper: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Scraper
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">
          This page will provide scraper functionality to discover new Acestream channels.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Scraper;

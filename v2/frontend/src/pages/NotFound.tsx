import React from 'react';
import { Typography, Box, Paper, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const NotFound: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      justifyContent: 'center',
      height: '70vh'
    }}>
      <Typography variant="h1" gutterBottom>
        404
      </Typography>
      <Paper sx={{ p: 3, maxWidth: '500px', textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Page Not Found
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          The page you are looking for doesn't exist or has been moved.
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => navigate('/')}
        >
          Go to Dashboard
        </Button>
      </Paper>
    </Box>
  );
};

export default NotFound;

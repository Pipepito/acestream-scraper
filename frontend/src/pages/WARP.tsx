/**
 * WARP Management Page
 */
import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  TextField,
  Typography,
  Alert,
  Chip,
} from '@mui/material';
import { useWarpStatus, useWarpConnect, useWarpDisconnect, useWarpSetMode, useWarpRegisterLicense } from '../hooks/useWarp';
import { WarpMode } from '../types/warpTypes';

const WarpPage: React.FC = () => {
  const { data: status, isLoading, error } = useWarpStatus();
  const connectMutation = useWarpConnect();
  const disconnectMutation = useWarpDisconnect();
  const setModeMutation = useWarpSetMode();
  const registerLicenseMutation = useWarpRegisterLicense();
  
  const [selectedMode, setSelectedMode] = useState<WarpMode>(WarpMode.WARP);
  const [licenseKey, setLicenseKey] = useState('');
  
  const handleModeChange = (event: SelectChangeEvent) => {
    setSelectedMode(event.target.value as WarpMode);
  };
  
  const handleSetMode = async () => {
    try {
      await setModeMutation.mutateAsync(selectedMode);
    } catch (error) {
      console.error('Failed to set WARP mode:', error);
    }
  };
  
  const handleRegisterLicense = async () => {
    if (!licenseKey.trim()) return;
    
    try {
      await registerLicenseMutation.mutateAsync(licenseKey);
      setLicenseKey('');
    } catch (error) {
      console.error('Failed to register license:', error);
    }
  };
  
  const getConnectionStatusColor = () => {
    if (!status?.running) return 'default';
    return status?.connected ? 'success' : 'warning';
  };
  
  const getConnectionStatusLabel = () => {
    if (!status?.running) return 'Not Running';
    return status?.connected ? 'Connected' : 'Disconnected';
  };
  
  const formatJSONDisplay = (json: Record<string, any>) => {
    return (
      <Box component="pre" sx={{ 
        backgroundColor: 'background.paper', 
        p: 2, 
        borderRadius: 1,
        overflowX: 'auto',
        fontSize: '0.875rem'
      }}>
        {JSON.stringify(json, null, 2)}
      </Box>
    );
  };

  if (isLoading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error">
          Error loading WARP status: {(error as Error).message}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        WARP Management
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="WARP Status" 
              action={
                <Chip 
                  label={getConnectionStatusLabel()} 
                  color={getConnectionStatusColor()} 
                  variant="outlined" 
                />
              }
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Status: {status?.running ? 'Running' : 'Not Running'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Connected: {status?.connected ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Mode: {status?.mode || 'Unknown'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Account Type: {status?.account_type}
              </Typography>
              {status?.ip && (
                <Typography variant="body2" color="text.secondary">
                  IP: {status.ip}
                </Typography>
              )}
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => connectMutation.mutate()}
                  disabled={!status?.running || status?.connected || connectMutation.isLoading}
                  sx={{ mr: 2 }}
                >
                  {connectMutation.isLoading ? <CircularProgress size={24} /> : 'Connect'}
                </Button>
                <Button
                  variant="outlined"
                  color="secondary"
                  onClick={() => disconnectMutation.mutate()}
                  disabled={!status?.running || !status?.connected || disconnectMutation.isLoading}
                >
                  {disconnectMutation.isLoading ? <CircularProgress size={24} /> : 'Disconnect'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="WARP Settings" />
            <CardContent>
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Mode</InputLabel>
                <Select
                  value={selectedMode}
                  onChange={handleModeChange}
                  label="Mode"
                  disabled={!status?.running}
                >
                  <MenuItem value={WarpMode.WARP}>WARP (Full Tunnel)</MenuItem>
                  <MenuItem value={WarpMode.DOT}>DOT (DNS over TLS)</MenuItem>
                  <MenuItem value={WarpMode.PROXY}>PROXY</MenuItem>
                  <MenuItem value={WarpMode.OFF}>OFF</MenuItem>
                </Select>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSetMode}
                  disabled={!status?.running || (status?.mode === selectedMode) || setModeMutation.isLoading}
                  sx={{ mt: 2 }}
                >
                  {setModeMutation.isLoading ? <CircularProgress size={24} /> : 'Set Mode'}
                </Button>
              </FormControl>
              
              <Divider sx={{ my: 3 }} />
              
              <FormControl fullWidth>
                <TextField
                  label="License Key"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  disabled={!status?.running}
                  placeholder="Enter your WARP+ or WARP Teams license key"
                />
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleRegisterLicense}
                  disabled={!status?.running || !licenseKey.trim() || registerLicenseMutation.isLoading}
                  sx={{ mt: 2 }}
                >
                  {registerLicenseMutation.isLoading ? <CircularProgress size={24} /> : 'Register License'}
                </Button>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>
        
        {status?.cf_trace && Object.keys(status.cf_trace).length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Cloudflare Trace Information
              </Typography>
              {formatJSONDisplay(status.cf_trace)}
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default WarpPage;

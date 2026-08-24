/**
 * WARP Management Page
 */
import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
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
  Stack,
} from '@mui/material';
import { useWarpStatus, useWarpConnect, useWarpDisconnect, useWarpSetMode, useWarpRegisterLicense } from '../hooks/useWarp';
import { WarpMode } from '../types/warpTypes';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { alpha, useTheme } from '@mui/material/styles';

const WarpPage: React.FC = () => {
  const theme = useTheme();
  const { data: status, isLoading, error } = useWarpStatus();
  const connectMutation = useWarpConnect();
  const disconnectMutation = useWarpDisconnect();
  const setModeMutation = useWarpSetMode();
  const registerLicenseMutation = useWarpRegisterLicense();
  
  const [selectedMode, setSelectedMode] = useState<WarpMode>(WarpMode.WARP);
  const [licenseKey, setLicenseKey] = useState('');

  useEffect(() => {
    if (status?.mode) {
      setSelectedMode(status.mode);
    }
  }, [status?.mode]);
  
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
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error">
          Error loading WARP status: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="WARP"
        subtitle="Check tunnel status, switch modes, and manage your license from one operational flow."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ width: { xs: '100%', sm: 'auto' } }}>
            <Button variant="contained" color="primary" onClick={() => connectMutation.mutate()} disabled={!status?.running || status?.connected || connectMutation.isPending}>
              {connectMutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Connect'}
            </Button>
            <Button variant="outlined" onClick={() => disconnectMutation.mutate()} disabled={!status?.running || !status?.connected || disconnectMutation.isPending}>
              {disconnectMutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Disconnect'}
            </Button>
          </Stack>
        }
      />

      <Box
        sx={{
          mb: 3,
          p: { xs: 2, md: 2.5 },
          borderRadius: 2.5,
          bgcolor: theme.appTokens.hero.bg,
          border: `1px solid ${theme.appTokens.hero.border}`,
          backgroundImage: theme.appTokens.hero.spotlight,
        }}
      >
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'space-between' }}>
          <Box sx={{ minWidth: 0, maxWidth: 760 }}>
            <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent, mb: 1 }}>
              Tunnel pulse
            </Typography>
            <Typography variant="h4" sx={{ letterSpacing: '-0.03em', mb: 1 }}>
              {status?.connected
                ? 'WARP is connected and ready to protect scraper traffic.'
                : status?.running
                  ? 'WARP is available, but traffic is not currently protected.'
                  : 'WARP is not running yet.'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Use this summary to confirm your protection state before changing modes, refreshing network-sensitive work, or registering a license.
            </Typography>
          </Box>
          <Stack spacing={1} sx={{ minWidth: { xs: '100%', sm: 280 } }}>
            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha(theme.appTokens.shell.accent, 0.08), border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}` }}>
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>Protection state</Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>{status?.connected ? 'Protected and connected' : status?.running ? 'Available but unprotected' : 'Service offline'}</Typography>
            </Box>
            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: theme.appTokens.surface.panel, border: `1px solid ${theme.appTokens.surface.border}` }}>
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>Next step</Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Keep the current tunnel active or change mode before you run more network-sensitive tasks.
              </Typography>
            </Box>
          </Stack>
        </Box>
      </Box>
      
      <ContentSection title="Connection status" description="Use the status summary to confirm whether traffic is protected before changing mode or license settings.">
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ xs: 'flex-start', sm: 'center' }}>
            <Chip label={getConnectionStatusLabel()} color={getConnectionStatusColor()} variant="outlined" />
            <Chip label={status?.running ? 'Service running' : 'Service stopped'} variant="outlined" />
          </Stack>
          <Alert severity={status?.connected ? 'success' : status?.running ? 'warning' : 'error'}>
            {status?.connected ? 'Connected' : status?.running ? 'Disconnected' : 'Not running'} · Mode: {status?.mode || 'Unknown'} · Account: {status?.account_type || 'Unknown'}
          </Alert>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                <Typography variant="sectionTitle" sx={{ mb: 1 }}>Current path</Typography>
                <Typography variant="body2" color="text.secondary">Connected: {status?.connected ? 'Yes' : 'No'}</Typography>
                <Typography variant="body2" color="text.secondary">Mode: {status?.mode || 'Unknown'}</Typography>
                <Typography variant="body2" color="text.secondary">Account Type: {status?.account_type}</Typography>
                {status?.ip ? <Typography variant="body2" color="text.secondary">IP: {status.ip}</Typography> : null}
              </Paper>
            </Grid>
          </Grid>
        </Stack>
      </ContentSection>

      <ContentSection title="Mode and license" description="Change how WARP routes traffic, then register a license key if your account needs it.">
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel id="warp-mode-label">Mode</InputLabel>
                <Select
                  labelId="warp-mode-label"
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
                <Button variant="contained" color="primary" onClick={handleSetMode} disabled={!status?.running || (status?.mode === selectedMode) || setModeMutation.isPending} sx={{ mt: 2 }}>
                  {setModeMutation.isPending ? <CircularProgress size={24} /> : 'Set Mode'}
                </Button>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
                <TextField
                  label="License Key"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  disabled={!status?.running}
                  placeholder="Enter your WARP+ or WARP Teams license key"
                />
                <Button variant="contained" color="primary" onClick={handleRegisterLicense} disabled={!status?.running || !licenseKey.trim() || registerLicenseMutation.isPending} sx={{ mt: 2 }}>
                  {registerLicenseMutation.isPending ? <CircularProgress size={24} /> : 'Register License'}
                </Button>
            </FormControl>
          </Grid>
        </Grid>
        <Divider sx={{ my: 3 }} />
        {status?.cf_trace && Object.keys(status.cf_trace).length > 0 ? (
          <Box>
            <Typography variant="sectionTitle" sx={{ mb: 1.5 }}>Cloudflare Trace Information</Typography>
            {formatJSONDisplay(status.cf_trace)}
          </Box>
        ) : null}
      </ContentSection>
    </Box>
  );
};

export default WarpPage;

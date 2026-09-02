import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { useWarpStatus, useWarpConnect, useWarpDisconnect, useWarpSetMode, useWarpRegisterLicense } from '../hooks/useWarp';
import { WarpMode, WarpStatus } from '../types/warpTypes';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const SUBTITLE = 'Cloudflare WARP tunnel for the scraper’s outbound traffic.';

/** One sentence that says everything a user needs about the tunnel state. */
export const describeWarpStatus = (status: WarpStatus | undefined): string => {
  if (!status?.running) return 'Not running';
  const parts = [status.connected ? 'Connected' : 'Disconnected'];
  if (status.mode) parts.push(`mode ${status.mode}`);
  if (status.account_type) parts.push(`${status.account_type} account`);
  if (status.connected && (status.location || status.colo)) {
    parts.push(`exit ${[status.location, status.colo ? `via ${status.colo}` : null].filter(Boolean).join(' ')}`);
  }
  return parts.join(' · ');
};

const WarpPage: React.FC = () => {
  const { data: status, isLoading, error } = useWarpStatus();
  const connectMutation = useWarpConnect();
  const disconnectMutation = useWarpDisconnect();
  const setModeMutation = useWarpSetMode();
  const registerLicenseMutation = useWarpRegisterLicense();

  const [selectedMode, setSelectedMode] = useState<WarpMode>(WarpMode.WARP);
  const [licenseKey, setLicenseKey] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (status?.mode) setSelectedMode(status.mode);
  }, [status?.mode]);

  const handleModeChange = (event: SelectChangeEvent) => setSelectedMode(event.target.value as WarpMode);

  const handleSetMode = async () => {
    setActionError(null);
    try {
      await setModeMutation.mutateAsync(selectedMode);
    } catch (err) {
      setActionError(`Failed to set the WARP mode: ${err instanceof Error ? err.message : 'unknown error'}`);
    }
  };

  const handleRegisterLicense = async () => {
    if (!licenseKey.trim()) return;
    setActionError(null);
    try {
      await registerLicenseMutation.mutateAsync(licenseKey);
      setLicenseKey('');
    } catch (err) {
      setActionError(`Failed to register the license: ${err instanceof Error ? err.message : 'unknown error'}`);
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }} role="status" aria-label="Loading WARP status">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <PageHeader title="WARP" subtitle={SUBTITLE} />
        <Alert severity="error">Error loading WARP status: {(error as Error).message}</Alert>
      </Box>
    );
  }

  const running = Boolean(status?.running);
  const connected = Boolean(status?.connected);
  const chipColor = !running ? 'default' : connected ? 'success' : 'warning';
  const chipLabel = !running ? 'Not running' : connected ? 'Connected' : 'Disconnected';

  return (
    <Box>
      <PageHeader
        title="WARP"
        subtitle={SUBTITLE}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ width: { xs: '100%', sm: 'auto' } }}>
            <Button component={RouterLink} to="/" variant="text">
              Back to Overview
            </Button>
            <Button variant="contained" color="primary" onClick={() => connectMutation.mutate()} disabled={!running || connected || connectMutation.isPending}>
              {connectMutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Connect'}
            </Button>
            <Button variant="outlined" onClick={() => disconnectMutation.mutate()} disabled={!running || !connected || disconnectMutation.isPending}>
              {disconnectMutation.isPending ? <CircularProgress size={24} color="inherit" /> : 'Disconnect'}
            </Button>
          </Stack>
        }
      />

      <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" useFlexGap role="status" aria-label="WARP status" sx={{ mb: 2 }}>
        <Chip label={chipLabel} color={chipColor} variant="outlined" sx={{ fontWeight: 600, minWidth: 110 }} />
        <Typography variant="body2" color="text.secondary">
          {describeWarpStatus(status)}
        </Typography>
      </Stack>

      {actionError ? (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setActionError(null)}>
          {actionError}
        </Alert>
      ) : null}

      {!running ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          WARP is not running in this container. Start it with <code>ENABLE_WARP=true</code> and give the container the <code>NET_ADMIN</code> and{' '}
          <code>SYS_ADMIN</code> capabilities (see the README). Restart it from the Services panel on the Overview once enabled.
        </Alert>
      ) : null}

      {running ? (
        <ContentSection title="Connection details">
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }} component="section" aria-label="Current path">
                <Typography variant="sectionTitle" sx={{ mb: 1 }}>
                  Current path
                </Typography>
                {status?.ip ? (
                  <Typography variant="body2" color="text.secondary">
                    IP: {status.ip}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {connected ? 'Public IP not reported yet.' : 'Connect to see the public IP and exit location.'}
                  </Typography>
                )}
                {status?.location || status?.colo ? (
                  <Typography variant="body2" color="text.secondary">
                    Exit location: {[status?.location, status?.colo ? `via ${status.colo}` : null].filter(Boolean).join(' ')}
                  </Typography>
                ) : null}
              </Paper>
            </Grid>
            {connected && status?.tunnel && Object.values(status.tunnel).some(Boolean) ? (
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 2, height: '100%' }} component="section" aria-label="Tunnel details">
                  <Typography variant="sectionTitle" sx={{ mb: 1 }}>
                    Tunnel details
                  </Typography>
                  {status.tunnel.protocol ? <Typography variant="body2" color="text.secondary">Protocol: {status.tunnel.protocol}</Typography> : null}
                  {status.tunnel.latency ? <Typography variant="body2" color="text.secondary">Latency: {status.tunnel.latency}</Typography> : null}
                  {status.tunnel.loss ? <Typography variant="body2" color="text.secondary">Packet loss: {status.tunnel.loss}</Typography> : null}
                  {status.tunnel.last_handshake ? <Typography variant="body2" color="text.secondary">Last handshake: {status.tunnel.last_handshake} ago</Typography> : null}
                  {status.tunnel.sent || status.tunnel.received ? (
                    <Typography variant="body2" color="text.secondary">
                      Traffic: {status.tunnel.sent ?? '?'} sent, {status.tunnel.received ?? '?'} received
                    </Typography>
                  ) : null}
                  {status.tunnel.endpoints ? <Typography variant="body2" color="text.secondary">Endpoints: {status.tunnel.endpoints}</Typography> : null}
                  {status.tunnel.tls_version ? <Typography variant="body2" color="text.secondary">TLS: {status.tunnel.tls_version}</Typography> : null}
                </Paper>
              </Grid>
            ) : null}
            {status?.registration && (status.registration.device_id || status.registration.account_id || status.registration.license) ? (
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 2, height: '100%' }} component="section" aria-label="Registration">
                  <Typography variant="sectionTitle" sx={{ mb: 1 }}>
                    Registration
                  </Typography>
                  {status.registration.device_id ? <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>Device ID: {status.registration.device_id}</Typography> : null}
                  {status.registration.account_id ? <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>Account ID: {status.registration.account_id}</Typography> : null}
                  {status.registration.license ? <Typography variant="body2" color="text.secondary">License: {status.registration.license}</Typography> : null}
                </Paper>
              </Grid>
            ) : null}
          </Grid>
        </ContentSection>
      ) : null}

      {running ? (
        <ContentSection title="Mode and license" description="Change how WARP routes traffic, then register a license key if your account needs it.">
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel id="warp-mode-label">Mode</InputLabel>
                <Select labelId="warp-mode-label" value={selectedMode} onChange={handleModeChange} label="Mode">
                  <MenuItem value={WarpMode.WARP}>WARP (Full Tunnel)</MenuItem>
                  <MenuItem value={WarpMode.DOT}>DOT (DNS over TLS)</MenuItem>
                  <MenuItem value={WarpMode.PROXY}>PROXY</MenuItem>
                  <MenuItem value={WarpMode.OFF}>OFF</MenuItem>
                </Select>
                <Button variant="contained" color="primary" onClick={handleSetMode} disabled={status?.mode === selectedMode || setModeMutation.isPending} sx={{ mt: 2 }}>
                  {setModeMutation.isPending ? <CircularProgress size={24} /> : 'Set Mode'}
                </Button>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <TextField label="License Key" value={licenseKey} onChange={(e) => setLicenseKey(e.target.value)} placeholder="Enter your WARP+ or WARP Teams license key" />
                <Button variant="contained" color="primary" onClick={handleRegisterLicense} disabled={!licenseKey.trim() || registerLicenseMutation.isPending} sx={{ mt: 2 }}>
                  {registerLicenseMutation.isPending ? <CircularProgress size={24} /> : 'Register License'}
                </Button>
              </FormControl>
            </Grid>
          </Grid>
        </ContentSection>
      ) : null}
    </Box>
  );
};

export default WarpPage;

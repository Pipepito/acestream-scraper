import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { useWarpStatus, useWarpConnect, useWarpDisconnect, useWarpReconnect, useWarpSetMode, useWarpRegisterLicense } from '../hooks/useWarp';
import { WarpMode, WarpStatus } from '../types/warpTypes';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import WarpExclusionsSection from '../components/WarpExclusionsSection';
import WarpStartupSection from '../components/WarpStartupSection';
import { getErrorDetail } from '../utils/errorUtils';

const SUBTITLE = 'Cloudflare WARP tunnel for the scraper’s outbound traffic.';

/** One sentence that says everything a user needs about the tunnel state. */
export const describeWarpStatus = (status: WarpStatus | undefined): string => {
  if (!status?.running) return uiText("Not running");
  const parts: string[] = [status.connected ? uiText("Connected") : uiText("Disconnected")];
  if (status.mode) parts.push(uiText('mode {{mode}}', { mode: status.mode }));
  if (status.account_type) parts.push(uiText('{{type}} account', { type: status.account_type }));
  if (status.connected && (status.location || status.colo)) {
    parts.push(status.location && status.colo ? uiText('exit {{location}} via {{colo}}', { location: status.location, colo: status.colo })
      : status.colo ? uiText('exit via {{colo}}', { colo: status.colo }) : uiText('exit {{location}}', { location: status.location }));
  }
  return parts.join(' · ');
};

const WarpPage: React.FC = () => {
  const tUi = useUiText();
  const navigate = useNavigate();
  const { data: status, isLoading, error } = useWarpStatus();
  const connectMutation = useWarpConnect();
  const disconnectMutation = useWarpDisconnect();
  const reconnectMutation = useWarpReconnect();
  const setModeMutation = useWarpSetMode();
  const registerLicenseMutation = useWarpRegisterLicense();

  const [selectedMode, setSelectedMode] = useState<WarpMode>(WarpMode.WARP);
  const [licenseKey, setLicenseKey] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    if (status?.mode) setSelectedMode(status.mode);
  }, [status?.mode]);

  const reconnecting = reconnectMutation.isPending;
  const reconnect = async () => {
    setActionError(null);
    try {
      await reconnectMutation.mutateAsync();
    } catch (err) {
      setActionError(uiText('Could not reconnect WARP: {{error}}. Check the connection status and use Connect to retry.', { error: getErrorDetail(err) ?? uiText('unknown error') }));
    }
  };

  const handleModeChange = (event: SelectChangeEvent) => setSelectedMode(event.target.value as WarpMode);

  const handleSetMode = async () => {
    setActionError(null);
    try {
      await setModeMutation.mutateAsync(selectedMode);
    } catch (err) {
      setActionError(uiText('Failed to set the WARP mode: {{error}}', { error: getErrorDetail(err) ?? uiText('unknown error') }));
    }
  };

  const handleRegisterLicense = async () => {
    if (!licenseKey.trim()) return;
    setActionError(null);
    try {
      await registerLicenseMutation.mutateAsync(licenseKey);
      setLicenseKey('');
    } catch (err) {
      setActionError(uiText('Failed to register the license: {{error}}', { error: getErrorDetail(err) ?? uiText('unknown error') }));
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }} role="status" aria-label={tUi("Loading WARP status")}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <PageHeader title={tUi("WARP")} subtitle={tUi(SUBTITLE)} />
        <Alert severity="error">{tUi("Error loading WARP status:")}{' '}{getErrorDetail(error)}</Alert>
      </Box>
    );
  }

  const running = Boolean(status?.running);
  const connected = Boolean(status?.connected);
  const chipColor = !running ? 'default' : connected ? 'success' : 'warning';
  const chipLabel = !running ? uiText("Not running") : connected ? uiText("Connected") : uiText("Disconnected");
  const killSwitch = status?.kill_switch;
  const blocking = killSwitch?.enabled === true && killSwitch.blocking === true;

  return (
    <Box>
      <PageHeader
        title={tUi("WARP")}
        subtitle={tUi(SUBTITLE)}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} sx={{ width: { xs: '100%', sm: 'auto' } }}>
            <Button variant="contained" color="primary" onClick={() => connectMutation.mutate()} disabled={!running || connected || connectMutation.isPending || reconnecting}>
              {connectMutation.isPending ? <CircularProgress size={24} color="inherit" /> : tUi("Connect")}
            </Button>
            <Button variant="outlined" onClick={() => disconnectMutation.mutate()} disabled={!running || !connected || disconnectMutation.isPending || reconnecting}>
              {disconnectMutation.isPending ? <CircularProgress size={24} color="inherit" /> : tUi("Disconnect")}
            </Button>
            <Button disabled={!running || !connected || reconnecting || connectMutation.isPending || disconnectMutation.isPending} onClick={reconnect}>{reconnecting ? tUi("Reconnecting…") : tUi("Reconnect")}</Button>
          </Stack>
        }
        overflowActions={[{ label: uiText("Back to System status"), onClick: () => navigate('/system') }]}
      />

      <Stack direction="row" spacing={1.5} alignItems="center" flexWrap="wrap" useFlexGap role="status" aria-label={tUi("WARP status")} sx={{ mb: 2 }}>
        <Chip label={chipLabel} color={chipColor} variant="outlined" sx={{ fontWeight: 600, minWidth: 110 }} />
        <Typography variant="body2" color="text.secondary">
          {describeWarpStatus(status)}{killSwitch?.enabled ? ` · ${tUi('Kill switch on')}` : ''}
        </Typography>
      </Stack>

      {blocking ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {tUi("Direct internet traffic is blocked until WARP is connected again. The app restarts WARP by itself.")}
        </Alert>
      ) : null}

      {killSwitch?.unavailable ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {tUi("The kill switch could not be set up on this host, so WARP runs without it. If WARP stops, traffic uses your normal connection. It needs nftables support on the host and Docker’s default SETGID capability.")}
        </Alert>
      ) : null}

      {killSwitch?.enabled && killSwitch.unprotected ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {tUi("WARP is not running and direct traffic is not blocked. Restart the container to restore protection.")}
        </Alert>
      ) : null}

      {killSwitch?.enabled && killSwitch.blocking === false && !killSwitch.unprotected && running && !connected ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {tUi("WARP is disconnected, so traffic uses your normal connection. The kill switch covers WARP stopping or restarting, not a disconnect you choose. Connect to protect traffic again.")}
        </Alert>
      ) : null}

      {actionError ? (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setActionError(null)}>
          {actionError}
        </Alert>
      ) : null}

      {!running && !killSwitch?.enabled ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          {tUi("WARP is not running in this container. Enable it with")}{' '}<code>{tUi("ENABLE_WARP=true")}</code>{tUi(". DNS-only startup uses")}{' '}<code>{tUi("WARP_DNS_ONLY=true")}</code> {' '}{tUi("and needs")}{' '}<code>{tUi("NET_ADMIN")}</code>{tUi(". Full tunneling also needs")}{' '}<code>{tUi("/dev/net/tun")}</code>{tUi(". Neither mode needs")}{' '}<code>{tUi("SYS_ADMIN")}</code> {tUi("with the current client. Recreate the container if permissions or devices are missing; saving app settings cannot add them.")}</Alert>
      ) : null}

      {running ? (
        <ContentSection title={tUi("Connection details")}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper variant="outlined" sx={{ p: 2, height: '100%' }} component="section" aria-label={tUi("Current path")}>
                <Typography variant="sectionTitle" sx={{ mb: 1 }}>
                  {tUi("Current path")}</Typography>
                {status?.ip ? (
                  <Typography variant="body2" color="text.secondary">
                    {tUi("IP:")}{' '}{status.ip}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {connected ? tUi("Public IP not reported yet.") : tUi("Connect to see the public IP and exit location.")}
                  </Typography>
                )}
                {status?.location || status?.colo ? (
                  <Typography variant="body2" color="text.secondary">
                    {tUi("Exit location:")}{' '}{[status?.location, status?.colo ? tUi("via {{value0}}", { value0: status.colo }) : null].filter(Boolean).join(' ')}
                  </Typography>
                ) : null}
              </Paper>
            </Grid>
            {connected && status?.tunnel && Object.values(status.tunnel).some(Boolean) ? (
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 2, height: '100%' }} component="section" aria-label={tUi("Tunnel details")}>
                  <Typography variant="sectionTitle" sx={{ mb: 1 }}>
                    {tUi("Tunnel details")}</Typography>
                  {status.tunnel.protocol ? <Typography variant="body2" color="text.secondary">{tUi("Protocol:")}{' '}{status.tunnel.protocol}</Typography> : null}
                  {status.tunnel.latency ? <Typography variant="body2" color="text.secondary">{tUi("Latency:")}{' '}{status.tunnel.latency}</Typography> : null}
                  {status.tunnel.loss ? <Typography variant="body2" color="text.secondary">{tUi("Packet loss:")}{' '}{status.tunnel.loss}</Typography> : null}
                  {status.tunnel.last_handshake ? <Typography variant="body2" color="text.secondary">{tUi("Last handshake:")}{' '}{status.tunnel.last_handshake} {' '}{tUi("ago")}</Typography> : null}
                  {status.tunnel.sent || status.tunnel.received ? (
                    <Typography variant="body2" color="text.secondary">
                      {tUi("Traffic:")}{' '}{status.tunnel.sent ?? '?'} {' '}{tUi("sent,")}{' '}{status.tunnel.received ?? '?'} {tUi("received")}</Typography>
                  ) : null}
                  {status.tunnel.endpoints ? <Typography variant="body2" color="text.secondary">{tUi("Endpoints:")}{' '}{status.tunnel.endpoints}</Typography> : null}
                  {status.tunnel.tls_version ? <Typography variant="body2" color="text.secondary">{tUi("TLS:")}{' '}{status.tunnel.tls_version}</Typography> : null}
                </Paper>
              </Grid>
            ) : null}
            {status?.registration && (status.registration.device_id || status.registration.account_id || status.registration.license) ? (
              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 2, height: '100%' }} component="section" aria-label={tUi("Registration")}>
                  <Typography variant="sectionTitle" sx={{ mb: 1 }}>
                    {tUi("Registration")}</Typography>
                  {status.registration.device_id ? <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>{tUi("Device ID:")}{' '}{status.registration.device_id}</Typography> : null}
                  {status.registration.account_id ? <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>{tUi("Account ID:")}{' '}{status.registration.account_id}</Typography> : null}
                  {status.registration.license ? <Typography variant="body2" color="text.secondary">{tUi("License:")}{' '}{status.registration.license}</Typography> : null}
                </Paper>
              </Grid>
            ) : null}
          </Grid>
        </ContentSection>
      ) : null}

      <WarpExclusionsSection />
      <WarpStartupSection />

      {running ? (
        <ContentSection title={tUi("Mode and license")} description={tUi("Change how WARP routes traffic, then register a license key if your account needs it.")}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel id="warp-mode-label">{tUi("Mode")}</InputLabel>
                <Select labelId="warp-mode-label" value={selectedMode} onChange={handleModeChange} label={tUi("Mode")}>
                  <MenuItem value={WarpMode.WARP}>{tUi("WARP with standard DNS")}</MenuItem>
                  <MenuItem value={WarpMode.WARP_DOH}>{tUi("WARP with DNS over HTTPS")}</MenuItem>
                  <MenuItem value={WarpMode.WARP_DOT}>{tUi("WARP with DNS over TLS")}</MenuItem>
                  <MenuItem value={WarpMode.DOH}>{tUi("DNS over HTTPS only")}</MenuItem>
                  <MenuItem value={WarpMode.TUNNEL_ONLY}>{tUi("Tunnel only, keep current DNS")}</MenuItem>
                  <MenuItem value={WarpMode.DOT}>{tUi("DNS over TLS only")}</MenuItem>
                  <MenuItem value={WarpMode.PROXY}>{tUi("SOCKS5 proxy only")}</MenuItem>
                </Select>
                <Button variant="contained" color="primary" onClick={handleSetMode} disabled={status?.mode === selectedMode || setModeMutation.isPending} sx={{ mt: 2 }}>
                  {setModeMutation.isPending ? <CircularProgress size={24} /> : tUi("Set Mode")}
                </Button>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <TextField label={tUi("License Key")} value={licenseKey} onChange={(e) => setLicenseKey(e.target.value)} placeholder={tUi("Enter your WARP+ or WARP Teams license key")} />
                <Button variant="contained" color="primary" onClick={handleRegisterLicense} disabled={!licenseKey.trim() || registerLicenseMutation.isPending} sx={{ mt: 2 }}>
                  {registerLicenseMutation.isPending ? <CircularProgress size={24} /> : tUi("Register License")}
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

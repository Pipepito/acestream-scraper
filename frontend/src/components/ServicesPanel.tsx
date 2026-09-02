import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Grid,
  Paper,
  Snackbar,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import PauseCircleOutlineIcon from '@mui/icons-material/PauseCircleOutline';
import LinkIcon from '@mui/icons-material/Link';
import BlockIcon from '@mui/icons-material/Block';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { useTheme } from '@mui/material/styles';
import { useRestartService, useSystemServices } from '../hooks/useSystemServices';
import type { ServiceState, ServiceStatus } from '../services/systemService';
import { useSnackbar } from '../hooks/useSnackbar';
import { normalizeApiError } from '../services/apiErrors';

interface StateMeta {
  label: string;
  color: 'success' | 'warning' | 'error' | 'default' | 'info';
  icon: React.ReactElement;
}

const STATE_META: Record<ServiceState, StateMeta> = {
  running: { label: 'Running', color: 'success', icon: <CheckCircleOutlineIcon fontSize="small" /> },
  unhealthy: { label: 'Unhealthy', color: 'warning', icon: <WarningAmberIcon fontSize="small" /> },
  stopped: { label: 'Stopped', color: 'error', icon: <ErrorOutlineIcon fontSize="small" /> },
  disabled: { label: 'Disabled', color: 'default', icon: <PauseCircleOutlineIcon fontSize="small" /> },
  external: { label: 'External', color: 'info', icon: <LinkIcon fontSize="small" /> },
  'not-installed': { label: 'Not installed', color: 'default', icon: <BlockIcon fontSize="small" /> },
};

const RESTART_TIMEOUT_MS = 90_000;

export const formatUptime = (seconds: number | null): string | null => {
  if (seconds === null || seconds === undefined) return null;
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h ${minutes % 60}m`;
  return `${Math.floor(hours / 24)}d ${hours % 24}h`;
};

export const restartDisabledReason = (service: ServiceStatus, supervised: boolean): string | null => {
  if (service.managed) return null;
  if (!service.installed) return 'Not included in this image flavor.';
  if (!service.enabled) return `Turned off; enable it with its ENABLE_* variable and recreate the container.`;
  if (!supervised) return 'Managed outside this container; restart it where it runs.';
  return 'Not running under the container supervisor right now.';
};

interface RestartWatch {
  name: string;
  label: string;
  previousPid: number | null;
  startedAt: number;
}

export interface ServicesPanelProps {
  /** Regular refresh cadence (a faster cadence kicks in while a restart is pending). */
  pollIntervalMs?: number;
}

const ServicesPanel: React.FC<ServicesPanelProps> = ({ pollIntervalMs = 30_000 }) => {
  const theme = useTheme();
  const [watch, setWatch] = useState<RestartWatch | null>(null);
  const [confirming, setConfirming] = useState<ServiceStatus | null>(null);
  const { snackbar, showSnackbar, closeSnackbar } = useSnackbar();
  const { data, isLoading, error, refetch, isFetching } = useSystemServices({
    refetchInterval: watch ? 3_000 : pollIntervalMs,
  });
  const restart = useRestartService();
  const showSnackbarRef = useRef(showSnackbar);
  showSnackbarRef.current = showSnackbar;

  // Resolve a pending restart once the service is back with a new pid, or give up after a while.
  useEffect(() => {
    if (!watch || !data) return;
    const current = data.services.find((s) => s.name === watch.name);
    if (!current) return;
    const relaunched = current.pid !== null && current.pid !== watch.previousPid;
    if (relaunched && current.state === 'running') {
      showSnackbarRef.current(`${watch.label} is back: ${current.message}`, 'success');
      setWatch(null);
    } else if (Date.now() - watch.startedAt > RESTART_TIMEOUT_MS) {
      showSnackbarRef.current(`${watch.label} has not reported healthy yet. Check the container logs.`, 'warning');
      setWatch(null);
    }
  }, [data, watch]);

  const services = useMemo(() => data?.services ?? [], [data]);
  const supervised = data?.supervised ?? false;

  const handleConfirmRestart = async () => {
    if (!confirming) return;
    const target = confirming;
    setConfirming(null);
    try {
      const result = await restart.mutateAsync(target.name);
      showSnackbar(result.message || `Restart requested for ${target.label}.`, 'info');
      setWatch({ name: target.name, label: target.label, previousPid: target.pid, startedAt: Date.now() });
    } catch (err) {
      const normalized = normalizeApiError(err);
      showSnackbar(`Could not restart ${target.label}: ${normalized.message}`, 'error');
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, py: 2 }} role="status">
        <CircularProgress size={20} aria-label="Loading services" />
        <Typography variant="body2">Checking sidecar services…</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={() => refetch()}>
            Retry
          </Button>
        }
      >
        Could not load the services status: {normalizeApiError(error).message}
      </Alert>
    );
  }

  return (
    <Box>
      {!supervised ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          This app is not running under the container entrypoint, so services are reported as external and cannot be
          restarted from here.
        </Alert>
      ) : null}
      <Grid container spacing={2}>
        {services.map((service) => {
          const meta = STATE_META[service.state];
          const disabledReason = restartDisabledReason(service, supervised);
          const restarting = watch?.name === service.name;
          const uptime = formatUptime(service.uptime_seconds);
          return (
            <Grid item xs={12} md={6} lg={4} key={service.name}>
              <Paper
                variant="outlined"
                role="group"
                aria-label={`Service ${service.label}`}
                sx={{
                  p: 2,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1,
                  borderColor: theme.appTokens.surface.border,
                  backgroundColor: theme.appTokens.surface.raised,
                }}
              >
                <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
                  <Box>
                    <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600 }}>
                      {service.label}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {service.description}
                    </Typography>
                  </Box>
                  <Chip
                    size="small"
                    color={meta.color}
                    icon={meta.icon}
                    label={restarting ? 'Restarting…' : meta.label}
                    data-state={service.state}
                  />
                </Stack>
                <Typography variant="body2" sx={{ mt: 0.5 }}>
                  {service.message}
                </Typography>
                <Stack spacing={0.25} sx={{ color: 'text.secondary', fontSize: theme.typography.caption.fontSize }}>
                  {service.endpoint ? <span>Endpoint: {service.endpoint}</span> : null}
                  {service.version ? <span>Version: {service.version}</span> : null}
                  {uptime ? <span>Up for {uptime}</span> : null}
                </Stack>
                <Box sx={{ mt: 'auto', pt: 1 }}>
                  <Tooltip title={disabledReason ?? ''} disableHoverListener={!disabledReason}>
                    <span>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<RestartAltIcon />}
                        aria-label={`Restart ${service.label}`}
                        disabled={Boolean(disabledReason) || restarting || restart.isPending}
                        onClick={() => setConfirming(service)}
                      >
                        Restart
                      </Button>
                    </span>
                  </Tooltip>
                  {disabledReason ? (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      {disabledReason}
                    </Typography>
                  ) : null}
                </Box>
              </Paper>
            </Grid>
          );
        })}
      </Grid>
      {isFetching && !isLoading ? (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          Refreshing…
        </Typography>
      ) : null}

      <Dialog open={Boolean(confirming)} onClose={() => setConfirming(null)} aria-labelledby="restart-service-title">
        <DialogTitle id="restart-service-title">Restart {confirming?.label}?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            The service stops for a few seconds and the container supervisor starts it again. Anything using it right
            now, such as an open stream, is interrupted.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirming(null)}>Cancel</Button>
          <Button variant="contained" color="warning" onClick={handleConfirmRestart}>
            Restart service
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={closeSnackbar}>
        <Alert onClose={closeSnackbar} severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ServicesPanel;

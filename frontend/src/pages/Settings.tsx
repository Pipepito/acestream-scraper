import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  TextField,
  Button,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
  Snackbar
} from '@mui/material';
import {
  useBaseUrl,
  useUpdateBaseUrl,
  useAceEngineUrl,
  useUpdateAceEngineUrl,
  useRescrapeInterval,
  useUpdateRescrapeInterval,
  useAddPid,
  useUpdateAddPid,
  useAcestreamStatus
} from '../hooks/useConfig';
import { configService } from '../services/configService';

const Settings: React.FC = () => {
  // Form state
  const [baseUrl, setBaseUrl] = useState<string>('');
  const [aceEngineUrl, setAceEngineUrl] = useState<string>('');
  const [rescrapeInterval, setRescrapeInterval] = useState<number>(24);
  const [addPid, setAddPid] = useState<boolean>(false);
  const [appid, setAppid] = useState<boolean>(false);
  const [showSuccess, setShowSuccess] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string>('');

  // Queries
  const baseUrlQuery = useBaseUrl();
  const aceEngineUrlQuery = useAceEngineUrl();
  const rescrapeIntervalQuery = useRescrapeInterval();
  const addPidQuery = useAddPid();
  const acestreamStatusQuery = useAcestreamStatus({ refetchInterval: 30000 }); // Refetch every 30 seconds

  // AppID config (manual, since not in hooks yet)
  const [appidLoading, setAppidLoading] = useState<boolean>(true);
  const [appidSubmitting, setAppidSubmitting] = useState<boolean>(false);
  React.useEffect(() => {
    setAppidLoading(true);
    configService.getAppId().then((val) => {
      setAppid(val);
      setAppidLoading(false);
    });
  }, []);

  // Mutations
  const updateBaseUrlMutation = useUpdateBaseUrl();
  const updateAceEngineUrlMutation = useUpdateAceEngineUrl();
  const updateRescrapeIntervalMutation = useUpdateRescrapeInterval();
  const updateAddPidMutation = useUpdateAddPid();

  // Update local state when queries complete
  React.useEffect(() => {
    if (baseUrlQuery.data) setBaseUrl(baseUrlQuery.data);
  }, [baseUrlQuery.data]);

  React.useEffect(() => {
    if (aceEngineUrlQuery.data) setAceEngineUrl(aceEngineUrlQuery.data);
  }, [aceEngineUrlQuery.data]);

  React.useEffect(() => {
    if (rescrapeIntervalQuery.data !== undefined) setRescrapeInterval(rescrapeIntervalQuery.data);
  }, [rescrapeIntervalQuery.data]);

  React.useEffect(() => {
    if (addPidQuery.data !== undefined) setAddPid(addPidQuery.data);
  }, [addPidQuery.data]);

  // Handle form submissions
  const handleBaseUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateBaseUrlMutation.mutate(baseUrl, {
      onSuccess: () => {
        setSuccessMessage('Base URL updated successfully');
        setShowSuccess(true);
      }
    });
  };

  const handleAceEngineUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateAceEngineUrlMutation.mutate(aceEngineUrl, {
      onSuccess: () => {
        setSuccessMessage('Acestream Engine URL updated successfully');
        setShowSuccess(true);
      }
    });
  };

  const handleRescrapeIntervalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateRescrapeIntervalMutation.mutate(rescrapeInterval, {
      onSuccess: () => {
        setSuccessMessage('Rescrape interval updated successfully');
        setShowSuccess(true);
      }
    });
  };

  const handleAddPidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAddPid(checked);
    updateAddPidMutation.mutate(checked, {
      onSuccess: () => {
        setSuccessMessage('Add PID setting updated successfully');
        setShowSuccess(true);
      }
    });
  };


  const handleAppidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAppid(checked);
    setAppidSubmitting(true);
    configService.updateAppId(checked).then(() => {
      setSuccessMessage('AppID setting updated successfully');
      setShowSuccess(true);
      setAppidSubmitting(false);
    });
  };

  const handleCloseSnackbar = () => {
    setShowSuccess(false);
  };


  const isLoading =
    baseUrlQuery.isLoading ||
    aceEngineUrlQuery.isLoading ||
    rescrapeIntervalQuery.isLoading ||
    addPidQuery.isLoading ||
    appidLoading;


  const isSubmitting =
    updateBaseUrlMutation.isLoading ||
    updateAceEngineUrlMutation.isLoading ||
    updateRescrapeIntervalMutation.isLoading ||
    updateAddPidMutation.isLoading ||
    appidSubmitting;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {/* Acestream Status Card */}
      <Card sx={{ mb: 4 }}>
        <CardHeader title="Acestream Engine Status" />
        <Divider />
        <CardContent>
          {acestreamStatusQuery.isLoading ? (
            <Box display="flex" alignItems="center">
              <CircularProgress size={20} sx={{ mr: 2 }} />
              <Typography>Checking Acestream Engine status...</Typography>
            </Box>
          ) : acestreamStatusQuery.error ? (
            <Alert severity="error">
              Error checking Acestream Engine status: {acestreamStatusQuery.error.toString()}
            </Alert>
          ) : (
            <Alert
              severity={acestreamStatusQuery.data?.status === 'online' ? 'success' : 'warning'}
              icon={false}
            >
              <Box display="flex" alignItems="center">
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: acestreamStatusQuery.data?.status === 'online' ? 'success.main' : 'warning.main',
                    mr: 2
                  }}
                />
                <Typography>
                  {acestreamStatusQuery.data?.message || 'Status unknown'}
                </Typography>
              </Box>
            </Alert>
          )}
          <Box mt={2}>
            <Button
              variant="outlined"
              onClick={() => acestreamStatusQuery.refetch()}
              disabled={acestreamStatusQuery.isLoading}
            >
              Refresh Status
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Grid container spacing={4}>
        {/* Base URL Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Base URL Configuration" />
            <Divider />
            <CardContent>
              <form onSubmit={handleBaseUrlSubmit}>
                <TextField
                  label="Base URL"
                  fullWidth
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  margin="normal"
                  helperText="The base URL for Acestream links (e.g., acestream://)"
                />
                <Box mt={2}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={isSubmitting || baseUrl === baseUrlQuery.data}
                  >
                    {updateBaseUrlMutation.isLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      'Save Changes'
                    )}
                  </Button>
                </Box>
              </form>
            </CardContent>
          </Card>
        </Grid>

        {/* Acestream Engine URL Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Acestream Engine Configuration" />
            <Divider />
            <CardContent>
              <form onSubmit={handleAceEngineUrlSubmit}>
                <TextField
                  label="Acestream Engine URL"
                  fullWidth
                  value={aceEngineUrl}
                  onChange={(e) => setAceEngineUrl(e.target.value)}
                  margin="normal"
                  helperText="The URL of your Acestream Engine (e.g., http://localhost:6878)"
                />
                <Box mt={2}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={isSubmitting || aceEngineUrl === aceEngineUrlQuery.data}
                  >
                    {updateAceEngineUrlMutation.isLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      'Save Changes'
                    )}
                  </Button>
                </Box>
              </form>
            </CardContent>
          </Card>
        </Grid>

        {/* Rescrape Interval Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Rescrape Interval Configuration" />
            <Divider />
            <CardContent>
              <form onSubmit={handleRescrapeIntervalSubmit}>
                <TextField
                  label="Rescrape Interval (hours)"
                  type="number"
                  fullWidth
                  value={rescrapeInterval}
                  onChange={(e) => setRescrapeInterval(parseInt(e.target.value))}
                  margin="normal"
                  InputProps={{ inputProps: { min: 1, max: 168 } }}
                  helperText="Hours between automatic rescrapes (1-168)"
                />
                <Box mt={2}>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={isSubmitting || rescrapeInterval === rescrapeIntervalQuery.data}
                  >
                    {updateRescrapeIntervalMutation.isLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      'Save Changes'
                    )}
                  </Button>
                </Box>
              </form>
            </CardContent>
          </Card>
        </Grid>

        {/* AppID Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Acestream AppID Configuration" />
            <Divider />
            <CardContent>
              <Box sx={{ p: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={appid}
                      onChange={handleAppidChange}
                      disabled={appidSubmitting}
                    />
                  }
                  label="Use AppID in Acestream links"
                />
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  When enabled, the AppID will be used in Acestream links in playlists.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        message={successMessage}
      />
    </Box>
  );
};

export default Settings;

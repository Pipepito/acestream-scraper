import React, { useState } from 'react';
import {
  Box,
  Grid,
  TextField,
  Button,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
  Snackbar,
  Stack,
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
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';

const Settings: React.FC = () => {
  // Form state
  const [baseUrl, setBaseUrl] = useState<string>('');
  const [aceEngineUrl, setAceEngineUrl] = useState<string>('');
  const [rescrapeInterval, setRescrapeInterval] = useState<number>(24);
  const [addPid, setAddPid] = useState<boolean>(false);
  const [appid, setAppid] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });
  const [appIdError, setAppIdError] = useState<string>('');

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
    setAppIdError('');

    configService
      .getAppId()
      .then((val) => {
        setAppid(val);
      })
      .catch(() => {
        setAppIdError('Could not load AppID setting. You can still retry the toggle manually.');
      })
      .finally(() => {
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
        setFeedback({ open: true, message: 'Base URL updated successfully', severity: 'success' });
      }
    });
  };

  const handleAceEngineUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateAceEngineUrlMutation.mutate(aceEngineUrl, {
      onSuccess: () => {
        setFeedback({ open: true, message: 'Acestream Engine URL updated successfully', severity: 'success' });
      }
    });
  };

  const handleRescrapeIntervalSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateRescrapeIntervalMutation.mutate(rescrapeInterval, {
      onSuccess: () => {
        setFeedback({ open: true, message: 'Rescrape interval updated successfully', severity: 'success' });
      }
    });
  };

  const handleAddPidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAddPid(checked);
    updateAddPidMutation.mutate(checked, {
      onSuccess: () => {
        setFeedback({ open: true, message: 'Add PID setting updated successfully', severity: 'success' });
      }
    });
  };


  const handleAppidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAppid(checked);
    setAppidSubmitting(true);

    configService
      .updateAppId(checked)
      .then(() => {
        setAppIdError('');
        setFeedback({ open: true, message: 'AppID setting updated successfully', severity: 'success' });
      })
      .catch(() => {
        setAppid(!checked);
        setFeedback({ open: true, message: 'Failed to update AppID setting', severity: 'error' });
      })
      .finally(() => {
        setAppidSubmitting(false);
      });
  };

  const handleCloseSnackbar = () => {
    setFeedback((current) => ({ ...current, open: false }));
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
    <Box>
      <PageHeader
        title="Settings"
        subtitle="Keep connection details and automation defaults in one predictable place."
      />

      <ContentSection
        title="Engine connection"
        description="Confirm the backend can reach your Acestream engine before changing connection settings."
        actions={
          <Button variant="outlined" onClick={() => acestreamStatusQuery.refetch()} disabled={acestreamStatusQuery.isLoading}>
            Refresh status
          </Button>
        }
      >
        {acestreamStatusQuery.isLoading ? (
          <Box display="flex" alignItems="center">
            <CircularProgress size={20} sx={{ mr: 2 }} />
            <Box component="span">Checking Acestream Engine status...</Box>
          </Box>
        ) : acestreamStatusQuery.error ? (
          <Alert severity="error">
            Error checking Acestream Engine status: {acestreamStatusQuery.error.toString()}
          </Alert>
        ) : (
          <Alert severity={acestreamStatusQuery.data?.status === 'online' ? 'success' : 'warning'}>
            {acestreamStatusQuery.data?.status === 'online' ? 'Online' : 'Needs attention'} · {acestreamStatusQuery.data?.message || 'Status unknown'}
          </Alert>
        )}
      </ContentSection>

      <ContentSection title="Connection settings" description="Update the base URLs only when your environment changes.">
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <form onSubmit={handleBaseUrlSubmit}>
              <Stack spacing={2}>
                <TextField
                  label="Base URL"
                  fullWidth
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  margin="normal"
                  helperText="The base URL for Acestream links (e.g., acestream://)"
                />
                <Button type="submit" variant="contained" color="primary" disabled={isSubmitting || baseUrl === baseUrlQuery.data}>
                  {updateBaseUrlMutation.isLoading ? <CircularProgress size={24} color="inherit" /> : 'Save base URL'}
                </Button>
              </Stack>
            </form>
          </Grid>
          <Grid item xs={12} md={6}>
            <form onSubmit={handleAceEngineUrlSubmit}>
              <Stack spacing={2}>
                <TextField
                  label="Acestream Engine URL"
                  fullWidth
                  value={aceEngineUrl}
                  onChange={(e) => setAceEngineUrl(e.target.value)}
                  margin="normal"
                  helperText="The URL of your Acestream Engine (e.g., http://localhost:6878)"
                />
                <Button type="submit" variant="contained" color="primary" disabled={isSubmitting || aceEngineUrl === aceEngineUrlQuery.data}>
                  {updateAceEngineUrlMutation.isLoading ? <CircularProgress size={24} color="inherit" /> : 'Save engine URL'}
                </Button>
              </Stack>
            </form>
          </Grid>
        </Grid>
      </ContentSection>

      <ContentSection title="Automation settings" description="Adjust scraper timing and playlist link options without mixing them into connection details.">
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <form onSubmit={handleRescrapeIntervalSubmit}>
              <Stack spacing={2}>
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
                <Button type="submit" variant="contained" color="primary" disabled={isSubmitting || rescrapeInterval === rescrapeIntervalQuery.data}>
                  {updateRescrapeIntervalMutation.isLoading ? <CircularProgress size={24} color="inherit" /> : 'Save rescrape interval'}
                </Button>
              </Stack>
            </form>
          </Grid>
          <Grid item xs={12} md={6}>
            <Stack spacing={2} sx={{ pt: 1 }}>
              {appIdError ? <Alert severity="warning">{appIdError}</Alert> : null}
              <Box>
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
                <Box sx={{ typography: 'body2', color: 'text.secondary', mt: 1 }}>
                  When enabled, the AppID will be used in Acestream links in playlists.
                </Box>
              </Box>
              <Box>
                <FormControlLabel
                  control={<Switch checked={addPid} onChange={handleAddPidChange} disabled={isSubmitting} />}
                  label="Append PID to generated Acestream links"
                />
                <Box sx={{ typography: 'body2', color: 'text.secondary', mt: 1 }}>
                  Keep this enabled when your player expects PID values in playlist links.
                </Box>
              </Box>
            </Stack>
          </Grid>
        </Grid>
      </ContentSection>

      <Snackbar
        open={feedback.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={feedback.severity} variant="filled" sx={{ width: '100%' }}>
          {feedback.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;

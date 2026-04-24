import React, { useState } from 'react';
import {
  Box,
  Grid,
  TextField,
  Button,
  FormControl,
  FormControlLabel,
  Switch,
  Radio,
  RadioGroup,
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
  useAllSettings,
  useAcestreamStatus
} from '../hooks/useConfig';
import { configService } from '../services/configService';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';
import { alpha, useTheme } from '@mui/material/styles';

const COMMON_CONNECTION_KEYS = ['base_url', 'ace_engine_url'] as const;
const AUTOMATION_KEYS = ['rescrape_interval', 'addpid', 'appid'] as const;

const INVENTORY_GROUPS = [
  { title: 'Common connection settings', keys: COMMON_CONNECTION_KEYS },
  { title: 'Automation settings', keys: AUTOMATION_KEYS },
  { title: 'Advanced/internal settings', keys: [] as const },
] as const;

const Settings: React.FC = () => {
  const theme = useTheme();
  const { mode, setMode } = useAppThemeMode();
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
  const allSettingsQuery = useAllSettings();
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
        allSettingsQuery.refetch?.();
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
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="60vh" gap={1.5}>
        <CircularProgress aria-label="Loading settings" />
        <Box component="p" sx={{ typography: 'sectionTitle', m: 0 }}>
          Loading settings
        </Box>
        <Box component="p" sx={{ typography: 'body2', color: 'text.secondary', m: 0, textAlign: 'center' }}>
          Preparing connection defaults, automation preferences, and appearance controls.
        </Box>
      </Box>
    );
  }

  const allSettings = allSettingsQuery.data ?? {};
  const mappedKeys = new Set([...COMMON_CONNECTION_KEYS, ...AUTOMATION_KEYS]);
  const advancedKeys = Object.keys(allSettings)
    .filter((key) => !mappedKeys.has(key))
    .sort((left, right) => left.localeCompare(right));
  const inventoryGroups = INVENTORY_GROUPS.map((group) => ({
    title: group.title,
    keys: group.title === 'Advanced/internal settings'
      ? advancedKeys
      : group.keys.filter((key) => Object.prototype.hasOwnProperty.call(allSettings, key)),
  })).filter((group) => group.keys.length > 0);

  return (
    <Box>
      <PageHeader
        title="Settings"
        subtitle="Keep connection details and automation defaults in one predictable place."
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
            <Box sx={{ typography: 'statusMeta', color: theme.appTokens.hero.accent, mb: 1 }}>Control center</Box>
            <Box sx={{ typography: 'h4', letterSpacing: '-0.03em', mb: 1 }}>Settings are ready for connection checks and automation tuning.</Box>
            <Box sx={{ typography: 'body2', color: 'text.secondary' }}>
              Start here when your engine path, playlist behavior, or theme preference needs review. The safest flow is to confirm engine status first and only then change persistent settings.
            </Box>
          </Box>
          <Stack spacing={1} sx={{ minWidth: { xs: '100%', sm: 280 } }}>
            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: alpha(theme.appTokens.shell.accent, 0.08), border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}` }}>
              <Box sx={{ typography: 'statusMeta', color: 'text.secondary', mb: 0.5 }}>Priority check</Box>
              <Box sx={{ typography: 'body2', fontWeight: 600 }}>
                {acestreamStatusQuery.data?.status === 'online' ? 'Engine connection looks healthy.' : 'Engine connection needs attention.'}
              </Box>
            </Box>
            <Box sx={{ p: 1.5, borderRadius: 2, bgcolor: theme.appTokens.surface.panel, border: `1px solid ${theme.appTokens.surface.border}` }}>
              <Box sx={{ typography: 'statusMeta', color: 'text.secondary', mb: 0.5 }}>Next step</Box>
              <Box sx={{ typography: 'body2', fontWeight: 600 }}>
                Confirm the engine is reachable, then update URLs or automation only if your environment changed.
              </Box>
            </Box>
          </Stack>
        </Box>
      </Box>

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

      <ContentSection
        title="Appearance"
        description="Choose the theme mode that keeps the dashboard easiest to read in your environment."
      >
        <FormControl component="fieldset">
          <RadioGroup aria-label="Theme mode" name="theme-mode" value={mode} onChange={(event) => setMode(event.target.value as 'light' | 'dark')}>
            <FormControlLabel value="light" control={<Radio />} label="Light theme" />
            <FormControlLabel value="dark" control={<Radio />} label="Dark theme" />
          </RadioGroup>
        </FormControl>
        <Box sx={{ typography: 'body2', color: 'text.secondary', mt: 1.5 }}>
          The shell toggle changes the theme quickly. This setting is the canonical place to confirm your preference.
        </Box>
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

      <ContentSection
        title="Settings inventory"
        description="Review the saved backend values grouped for quick troubleshooting, including settings that are editable elsewhere on this page."
      >
        <Stack spacing={2}>
          <Box sx={{ typography: 'body2', color: 'text.secondary' }}>
            Saved backend values appear here. Unsaved edits above do not appear here until save succeeds.
          </Box>

          {allSettingsQuery.isLoading ? (
            <Alert severity="info">Loading saved settings inventory.</Alert>
          ) : allSettingsQuery.error ? (
            <Alert severity="warning">Could not load the saved settings inventory. You can still review and update the editable controls above.</Alert>
          ) : Object.keys(allSettings).length === 0 ? (
            <Alert severity="info">No stored settings are available to review right now.</Alert>
          ) : (
            <Stack spacing={2.5}>
              {inventoryGroups.map((group) => (
                <Box key={group.title}>
                  <Box component="h3" sx={{ typography: 'sectionTitle', fontSize: '1rem', mb: 1.25 }}>
                    {group.title}
                  </Box>
                  <Stack
                    spacing={1}
                    sx={{
                      p: 1.5,
                      borderRadius: 2,
                      bgcolor: alpha(theme.palette.text.primary, theme.palette.mode === 'dark' ? 0.06 : 0.025),
                      border: `1px solid ${alpha(theme.palette.text.primary, theme.palette.mode === 'dark' ? 0.12 : 0.08)}`,
                    }}
                  >
                    {group.keys.map((key) => (
                      <Box
                        key={key}
                        sx={{
                          display: 'flex',
                          flexDirection: { xs: 'column', sm: 'row' },
                          gap: 0.5,
                          justifyContent: 'space-between',
                          alignItems: { xs: 'flex-start', sm: 'center' },
                        }}
                      >
                        <Box sx={{ typography: 'body2', fontWeight: 600, wordBreak: 'break-word' }}>{key}</Box>
                        <Box sx={{ typography: 'body2', color: allSettings[key] === '' ? 'text.secondary' : 'text.primary', wordBreak: 'break-word' }}>
                          {allSettings[key] === '' ? 'Not set' : allSettings[key]}
                        </Box>
                      </Box>
                    ))}
                  </Stack>
                </Box>
              ))}
            </Stack>
          )}
        </Stack>
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

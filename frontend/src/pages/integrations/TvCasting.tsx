import React, { useState } from 'react';
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Checkbox, FormControlLabel, List, ListItem, ListItemText, Stack, TextField, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink } from 'react-router-dom';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import ContentSection from '../../components/layout/ContentSection';
import { useAccess } from '../../components/access/AccessContext';
import { castService, type CastSettings } from '../../services/castService';
import { getAccessErrorMessage } from '../../services/accessErrors';

function CastingSettings({ initial, accounts }: { initial: CastSettings; accounts: boolean }) {
  const cache = useQueryClient();
  const [settings, setSettings] = useState(initial);
  const [home, setHome] = useState((initial.home_networks ?? []).join(', '));
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; error: boolean } | null>(null);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setFeedback(null);
    try {
      const saved = await castService.saveSettings({ ...settings, home_networks: home.split(',').map(v => v.trim()).filter(Boolean) });
      cache.setQueryData(['cast-settings'], saved);
      setSettings(saved); setHome((saved.home_networks ?? []).join(', '));
      await cache.invalidateQueries({ queryKey: ['cast-capabilities'] });
      await cache.invalidateQueries({ queryKey: ['access-policy'] });
      setFeedback({ message: 'TV casting settings saved.', error: false });
    } catch (reason) { setFeedback({ message: getAccessErrorMessage(reason), error: true }); }
    finally { setBusy(false); }
  };
  return <ContentSection title="Casting preferences" description="These settings are kept when user management is enabled or disabled.">
    <Stack component="form" onSubmit={submit} spacing={2}>
      <FormControlLabel label="Offer H.264 compatibility conversion" control={<Checkbox checked={settings.compatibility_conversion ?? false} onChange={(_, value) => setSettings({ ...settings, compatibility_conversion: value })} />} />
      <Typography variant="body2">Original video is the default. Conversion uses more CPU, is limited to one 720p/30 fps stream, and yields to recordings.</Typography>
      <Accordion disableGutters>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>Advanced connection settings</AccordionSummary>
        <AccordionDetails><Stack spacing={2}>
          <TextField label="Application address for TVs" value={settings.cast_media_url ?? ''} onChange={e => setSettings({ ...settings, cast_media_url: e.target.value })} helperText="Optional. Leave blank to use the address you opened in your browser. Include any proxy path prefix." />
          <TextField label="Allowed home networks" value={home} onChange={e => setHome(e.target.value)} helperText="Optional override, separated by commas. Leave blank to recognize private-network clients automatically. These are visitor networks, not TV addresses." />
          <FormControlLabel label="Allow accounts with casting permission to control TVs away from home" control={<Checkbox disabled={!accounts} checked={settings.remote_casting ?? false} onChange={(_, value) => setSettings({ ...settings, remote_casting: value })} />} />
          {!accounts ? <Typography variant="body2">Remote control requires an account. Local casting works without user management.</Typography> : null}
        </Stack></AccordionDetails>
      </Accordion>
      {feedback ? <Alert severity={feedback.error ? 'error' : 'success'}>{feedback.message}</Alert> : null}
      <Box><Button variant="contained" type="submit" disabled={busy}>Save casting settings</Button></Box>
    </Stack>
  </ContentSection>;
}

export default function TvCasting() {
  const cache = useQueryClient();
  const access = useAccess();
  const capabilities = useQuery({ queryKey: ['cast-capabilities'], queryFn: castService.capabilities, retry: false });
  const allowed = Boolean(capabilities.data?.server_devices);
  const canConfigure = Boolean(access?.status.user?.administrator || (access?.status.mode === 'open' && capabilities.data?.home_connection));
  const settings = useQuery({ queryKey: ['cast-settings'], queryFn: castService.settings, enabled: canConfigure, retry: false });
  const devices = useQuery({ queryKey: ['cast-devices'], queryFn: castService.devices, enabled: allowed, refetchInterval: allowed ? 3000 : false, retry: false });
  const [busy, setBusy] = useState(false);
  const [trustConfirmed, setTrustConfirmed] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);
  const [settingsVersion, setSettingsVersion] = useState(0);
  const run = async (action: () => Promise<void>) => {
    setBusy(true); setError('');
    try { await action(); } catch (reason) { setError(getAccessErrorMessage(reason)); }
    finally { setBusy(false); }
  };
  const trustHome = async () => {
    const saved = await castService.trustHome();
    cache.setQueryData(['cast-settings'], saved);
    setSettingsVersion(v => v + 1);
    await cache.invalidateQueries({ queryKey: ['cast-capabilities'] });
    await cache.invalidateQueries({ queryKey: ['access-policy'] });
    setTrustConfirmed(false);
  };
  return <IntegrationPage title="TV casting" summary={[
    { label: 'Connection', value: capabilities.data ? capabilities.data.home_connection ? 'Home' : 'Outside or unverified' : 'Checking…' },
    { label: 'TVs', value: allowed ? devices.data?.length ?? 'Looking…' : 'Unavailable' },
  ]}>{() => <>
    <ContentSection title="Home TVs" description="Discover Chromecast and Google Cast-enabled Android TVs. Casting from the scraper works with any browser and does not require user management.">
      <Stack spacing={2}>
        {capabilities.isError ? <Alert severity="error">Could not check casting access.</Alert> : null}
        {capabilities.data && !allowed ? <Alert severity="info">{capabilities.data.message}</Alert> : null}
        {capabilities.data && !capabilities.data.home_connection && access?.status.user?.administrator ? <>
          <Typography variant="body2">Using your public HTTPS address at home? Trust this connection to allow casting from your home internet address. Other visitors remain blocked. Repeat this if your provider changes your address. Shared internet connections also share this trust.</Typography>
          <FormControlLabel label="I am connected to my home network now" control={<Checkbox checked={trustConfirmed} onChange={(_, value) => setTrustConfirmed(value)} />} />
          <Box><Button disabled={busy || !trustConfirmed} onClick={() => void run(trustHome)}>Trust this home connection</Button></Box>
        </> : null}
        {allowed ? <>
          <Box><Button variant="outlined" disabled={busy} onClick={() => void run(async () => {
            cache.setQueryData(['cast-devices'], await castService.discover()); setSearched(true);
          })}>{busy ? 'Searching…' : 'Find TVs'}</Button></Box>
          {devices.isError ? <Alert severity="error">Could not load TVs. Try Find TVs again.</Alert> : null}
          {devices.data?.length ? <List disablePadding>{devices.data.map(tv => <ListItem key={tv.id} disableGutters><ListItemText primary={tv.name} secondary={tv.model} /></ListItem>)}</List> : <Typography variant="body2">{searched ? 'No Google Cast TVs found. Turn on the TV and enable Google Cast. Docker may need host networking for multicast discovery.' : 'Listening for TVs on your home network. Find TVs also checks the local network when multicast is unavailable.'}</Typography>}
          <Typography variant="body2">Choose a channel in Live TV, open Cast, then select your TV under Server devices.</Typography>
          <Box><Button component={RouterLink} to="/live-tv">Open Live TV</Button></Box>
          {capabilities.data?.media_url_configured ? <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>Video address: {capabilities.data.media_url}</Typography> : <Alert severity="info">Open the app using its home-network or HTTPS address so the TV can fetch video.</Alert>}
        </> : null}
        {error ? <Alert severity="error">{error}</Alert> : null}
      </Stack>
    </ContentSection>
    {settings.data ? <CastingSettings key={settingsVersion} initial={settings.data} accounts={access?.status.mode === 'accounts'} /> : settings.isError || (capabilities.data && !canConfigure) ? <Alert severity="info">Casting settings are available to administrators or, without accounts, from a recognized home connection.</Alert> : <Typography role="status">Loading casting settings…</Typography>}
  </>}</IntegrationPage>;
}

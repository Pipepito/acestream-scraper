import { useUnsavedChanges } from '../../components/UnsavedChanges';
import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useRef, useState } from 'react';
import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Checkbox, FormControlLabel, List, ListItem, ListItemText, Stack, TextField, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Link as RouterLink } from 'react-router-dom';
import IntegrationPage from '../../components/integrations/IntegrationPage';
import ContentSection from '../../components/layout/ContentSection';
import { useAccess } from '../../components/access/AccessContext';
import { castService, type CastSettings } from '../../services/castService';
import { getAccessErrorMessage, getCapabilityErrorMessage } from '../../services/accessErrors';

function CastingSettings({ initial, accounts, onEditingChange }: { initial: CastSettings; accounts: boolean; onEditingChange: (value: boolean) => void }) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const [draft, setSettings] = useState<CastSettings | null>(null);
  const settings = draft ?? initial;
  const [homeDraft, setHome] = useState<string | null>(null);
  const home = homeDraft ?? (initial.home_networks ?? []).join(', ');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ error: false } | { error: true; reason: unknown } | null>(null);
  const submitting = useRef(false);
  const dirty = draft !== null || homeDraft !== null;
  useUnsavedChanges(dirty, busy);
  useEffect(() => { onEditingChange(dirty || busy); }, [dirty, busy, onEditingChange]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setFeedback(null);
    try {
      await cache.cancelQueries({ queryKey: ['cast-settings'] });
      const saved = await castService.saveSettings({ ...settings, home_networks: home.split(',').map(v => v.trim()).filter(Boolean) });
      cache.setQueryData(['cast-settings'], saved);
      setSettings(null); setHome(null);
      await cache.invalidateQueries({ queryKey: ['cast-capabilities'] });
      await cache.invalidateQueries({ queryKey: ['access-policy'] });
      setFeedback({ error: false });
    } catch (reason) { setFeedback({ reason, error: true }); }
    finally { submitting.current = false; setBusy(false); }
  };
  return <ContentSection title={tUi("Casting preferences")} description={tUi("These settings are kept when user management is enabled or disabled.")}>
    <Stack component="form" onSubmit={submit} spacing={2}>
      <Box component="fieldset" disabled={busy} sx={{ border: 0, m: 0, p: 0, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 2 }}>
      <FormControlLabel label={tUi("Offer H.264 compatibility conversion")} control={<Checkbox checked={settings.compatibility_conversion ?? false} onChange={(_, value) => setSettings({ ...settings, compatibility_conversion: value })} />} />
      <Typography variant="body2">{tUi("Original video is the default. Conversion uses more CPU, is limited to one 720p/30 fps stream, and yields to recordings.")}</Typography>
      <Accordion disableGutters>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>{tUi("Advanced connection settings")}</AccordionSummary>
        <AccordionDetails><Stack spacing={2}>
          <TextField label={tUi("Application address for TVs")} value={settings.cast_media_url ?? ''} onChange={e => setSettings({ ...settings, cast_media_url: e.target.value })} helperText={tUi("Optional. Leave blank to use the address you opened in your browser. Include any proxy path prefix.")} />
          <TextField label={tUi("Allowed home networks")} value={home} onChange={e => { setSettings(settings); setHome(e.target.value); }} helperText={tUi("Optional override, separated by commas. Leave blank to recognize private-network clients automatically. These are visitor networks, not TV addresses.")} />
          <FormControlLabel label={tUi("Allow accounts with casting permission to control TVs away from home")} control={<Checkbox disabled={!accounts} checked={settings.remote_casting ?? false} onChange={(_, value) => setSettings({ ...settings, remote_casting: value })} />} />
          {!accounts ? <Typography variant="body2">{tUi("Remote control requires an account. Local casting works without user management.")}</Typography> : null}
        </Stack></AccordionDetails>
      </Accordion>
      {feedback ? <Alert severity={feedback.error ? 'error' : 'success'}>{feedback.error ? getAccessErrorMessage(feedback.reason) : tUi("TV casting settings saved.")}</Alert> : null}
      <Box><Button variant="contained" type="submit" disabled={busy}>{tUi("Save casting settings")}</Button></Box>
      </Box>
    </Stack>
  </ContentSection>;
}

export default function TvCasting() {
  const tUi = useUiText();
  const cache = useQueryClient();
  const access = useAccess();
  const capabilities = useQuery({ queryKey: ['cast-capabilities'], queryFn: castService.capabilities, retry: false });
  const allowed = Boolean(capabilities.data?.server_devices);
  const openAccess = capabilities.data?.home_check === 'off';
  const canConfigure = Boolean(access?.status.user?.administrator || (access?.status.mode === 'open' && (openAccess || capabilities.data?.home_connection)));
  const settings = useQuery({ queryKey: ['cast-settings'], queryFn: castService.settings, enabled: canConfigure, retry: false });
  const devices = useQuery({ queryKey: ['cast-devices'], queryFn: castService.devices, enabled: allowed, refetchInterval: allowed ? 3000 : false, retry: false });
  const [busy, setBusy] = useState(false);
  const [trustConfirmed, setTrustConfirmed] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const submitting = useRef(false);
  useUnsavedChanges(trustConfirmed, busy);
  const [searched, setSearched] = useState(false);
  const [settingsEditing, setSettingsEditing] = useState(false);
  const run = async (action: () => Promise<void>) => {
    if (submitting.current) return;
    submitting.current = true; setBusy(true); setError(null);
    try { await action(); } catch (reason) { setError(reason); }
    finally { submitting.current = false; setBusy(false); }
  };
  const trustHome = async () => {
    const saved = await castService.trustHome();
    cache.setQueryData(['cast-settings'], saved);
    await cache.invalidateQueries({ queryKey: ['cast-capabilities'] });
    await cache.invalidateQueries({ queryKey: ['access-policy'] });
    setTrustConfirmed(false);
  };
  return <IntegrationPage title={tUi("TV casting")} summary={[
    { label: uiText("Connection"), value: capabilities.data ? openAccess ? uiText("Open access") : capabilities.data.home_connection ? uiText("Home") : uiText("Outside or unverified") : uiText("Checking…") },
    { label: tUi('TVs'), value: allowed ? devices.data?.length ?? tUi('Looking…') : uiText('Unavailable') },
  ]}>{() => <>
    <ContentSection title={tUi("Home TVs")} description={tUi("Discover Chromecast and Google Cast-enabled Android TVs. Casting from the scraper works with any browser and does not require user management.")}>
      <Stack spacing={2}>
        {capabilities.isError ? <Alert severity="error">{tUi("Could not check casting access.")}</Alert> : null}
        {openAccess ? <Typography variant="body2">{tUi("Anyone who can open this app can list and control TVs. Set CAST_REQUIRE_HOME_NETWORK=true on the container or enable accounts to limit this.")}</Typography> : null}
        {capabilities.data && !allowed ? <Alert severity="info">{getCapabilityErrorMessage(capabilities.data)}</Alert> : null}
        {capabilities.data?.home_check === 'deployment' ? <Typography variant="body2">{tUi("Home-network check enforced by the deployment.")}</Typography> : null}
        {capabilities.data && !openAccess && !capabilities.data.home_connection && access?.status.user?.administrator ? <>
          <Typography variant="body2">{tUi("Using your public HTTPS address at home? Trust this connection to allow casting from your home internet address. Other visitors remain blocked. Repeat this if your provider changes your address. Shared internet connections also share this trust.")}</Typography>
          <FormControlLabel label={tUi("I am connected to my home network now")} control={<Checkbox disabled={busy} checked={trustConfirmed} onChange={(_, value) => setTrustConfirmed(value)} />} />
          {settingsEditing ? <Typography variant="body2">{tUi("Save casting preference changes before trusting this connection.")}</Typography> : null}
          <Box><Button disabled={busy || !trustConfirmed || settingsEditing} onClick={() => void run(trustHome)}>{tUi("Trust this home connection")}</Button></Box>
        </> : null}
        {allowed ? <>
          <Box><Button variant="outlined" disabled={busy} onClick={() => void run(async () => {
            cache.setQueryData(['cast-devices'], await castService.discover()); setSearched(true);
          })}>{busy ? tUi("Searching…") : tUi("Find TVs")}</Button></Box>
          {devices.isError ? <Alert severity="error">{tUi("Could not load TVs. Try Find TVs again.")}</Alert> : null}
          {devices.isFetching && !devices.data?.length ? <Typography role="status">{tUi("Looking for TVs on your home network… This can take up to 20 seconds.")}</Typography> : null}
          {devices.data?.length ? <List disablePadding>{devices.data.map(tv => <ListItem key={tv.id} disableGutters><ListItemText primary={tv.name} secondary={tv.model} /></ListItem>)}</List> : <Typography variant="body2">{searched ? tUi("No Google Cast TVs found. Turn on the TV and enable Google Cast. Docker may need host networking for multicast discovery.") : tUi("Listening for TVs on your home network. Find TVs also checks the local network when multicast is unavailable.")}</Typography>}
          <Typography variant="body2">{tUi("Use Send to player beside a channel in Live TV to cast directly to a TV. Casting options includes playback controls and compatibility settings.")}</Typography>
          <Box><Button component={RouterLink} to="/live-tv">{tUi("Open Live TV")}</Button></Box>
          {capabilities.data?.media_url_configured ? <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{tUi("Video address:")}{' '}{capabilities.data.media_url}</Typography> : <Alert severity="info">{capabilities.data?.home_connection ? tUi("Open the app using its home-network or HTTPS address so the TV can fetch video.") : tUi("From this connection the TV needs a fixed address: set Application address for TVs under Advanced connection settings, or open the app from your home network.")}</Alert>}
        </> : null}
        {error ? <Alert severity="error">{getAccessErrorMessage(error)}</Alert> : null}
      </Stack>
    </ContentSection>
    {access?.status.mode === 'open' || access?.status.user?.administrator ? <Box><Button component={RouterLink} to="/settings?tab=network">{tUi("Network settings")}</Button></Box> : null}
    {settings.data ? <CastingSettings onEditingChange={setSettingsEditing} initial={settings.data} accounts={access?.status.mode === 'accounts'} /> : settings.isError || (capabilities.data && !canConfigure) ? <Alert severity="info">{tUi("Casting settings are available to administrators or, without accounts, from a recognized home connection.")}</Alert> : <Typography role="status">{tUi("Loading casting settings…")}</Typography>}
  </>}</IntegrationPage>;
}

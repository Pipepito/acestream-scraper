import React, { useState } from 'react';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Snackbar, Tab, Tabs } from '@mui/material';
import { useUiText } from '../i18n/useUiText';
import { translateKnown } from '../i18n/text';
import PageHeader from '../components/layout/PageHeader';
import PlaybackSettings from '../components/settings/PlaybackSettings';
import AutomationSettings from '../components/settings/AutomationSettings';
import LinkSettings from '../components/settings/LinkSettings';
import AccessSection from '../components/settings/AccessSection';
import NetworkSettings from '../components/settings/NetworkSettings';
const sections = ['playback', 'automation', 'links', 'access', 'network'] as const;
export default function Settings() {
  const tUi = useUiText();
  const [params, setParams] = useSearchParams();
  const section = sections.find(name => name === params.get('tab')) ?? 'playback';
  const [feedback, setFeedback] = useState<{ message: string | (() => string); severity: 'success' | 'error' } | null>(null);
  const notify = (message: string | (() => string), severity: 'success' | 'error') => setFeedback({ message, severity });
  return <Box>
    <PageHeader title={tUi('Settings')} subtitle={tUi('Playback, scheduled jobs, stream links, accounts and network access.')} actions={<><Button component={RouterLink} to="/setup" variant="outlined">{tUi('Setup wizard')}</Button><Button href="/startup" variant="outlined">{tUi('Startup diagnostics')}</Button></>} />
    <Tabs value={section} onChange={(_event, value: string) => { const next = new URLSearchParams(params); next.set('tab', value); setParams(next); }} variant="scrollable" scrollButtons="auto" allowScrollButtonsMobile aria-label={tUi('Settings sections')} sx={{ mb: 2 }}>
      {sections.map((name, index) => <Tab key={name} value={name} id={`settings-tab-${name}`} aria-controls={`settings-panel-${name}`} label={translateKnown(['Playback', 'Automation', 'Stream links', 'Access', 'Network'][index])} />)}
    </Tabs>
    <Box role="tabpanel" id={`settings-panel-${section}`} aria-labelledby={`settings-tab-${section}`}>
      {section === 'playback' && <PlaybackSettings notify={notify} />}
      {section === 'automation' && <AutomationSettings notify={notify} />}
      {section === 'links' && <LinkSettings notify={notify} />}
      {section === 'access' && <AccessSection notify={notify} />}
      {section === 'network' && <NetworkSettings />}
    </Box>
    <Snackbar open={feedback !== null} autoHideDuration={6000} onClose={() => setFeedback(null)}>
      <Alert onClose={() => setFeedback(null)} severity={feedback?.severity} variant="filled" sx={{ width: '100%' }}>{typeof feedback?.message === 'function' ? feedback.message() : feedback?.message}</Alert>
    </Snackbar>
  </Box>;
}

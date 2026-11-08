import {
Alert,
Box,
Button,
CircularProgress,
FormControlLabel,
FormHelperText,
Stack,
Switch
} from '@mui/material';
import React,{ useEffect,useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
useAddPid,
useUpdateAddPid
} from '../../hooks/useConfig';
import { translateKnown,uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import { configService } from '../../services/configService';
import { getErrorMessage } from '../../utils/errorUtils';
import ContentSection from '../layout/ContentSection';
import StreamLinkFormatsSection from '../StreamLinkFormatsSection';

import { useUnsavedChanges } from '../UnsavedChanges';
type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string, severity: FeedbackSeverity) => void;

export default function LinkSettings({ notify }: { notify: Notify }) {
  const tUi = useUiText();
  const addPidQuery = useAddPid();
  const updateAddPidMutation = useUpdateAddPid();
  const [addPid, setAddPid] = useState(false);
  const [appid, setAppid] = useState(false);
  const [appIdError, setAppIdError] = useState('');
  const [appidLoading, setAppidLoading] = useState(true);
  const [appidSubmitting, setAppidSubmitting] = useState(false);
  useUnsavedChanges(false, appidSubmitting || updateAddPidMutation.isPending);
  useEffect(() => { if (addPidQuery.data !== undefined) setAddPid(addPidQuery.data); }, [addPidQuery.data]);
  useEffect(() => {
    let active = true;
    configService.getAppId().then(value => { if (active) setAppid(value); })
      .catch(() => { if (active) setAppIdError('Could not load the AppID setting. You can still try the switch.'); })
      .finally(() => { if (active) setAppidLoading(false); });
    return () => { active = false; };
  }, []);
  const handleAddPidChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setAddPid(checked);
    updateAddPidMutation.mutate(checked, {
      onSuccess: () => notify(checked ? uiText("PID will be appended to stream links") : uiText("PID will no longer be appended"), 'success'),
      onError: (error) => {
        setAddPid(!checked);
        notify(tUi('Failed to save the PID setting: {{error}}', { error: getErrorMessage(error) }), 'error');
      },
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
        notify(checked ? uiText("AppID will be added to stream links") : uiText("AppID will no longer be added"), 'success');
      })
      .catch(() => {
        setAppid(!checked);
        notify(tUi("Failed to update AppID setting"), 'error');
      })
      .finally(() => setAppidSubmitting(false));
  };


  if (addPidQuery.isLoading || appidLoading) return <CircularProgress aria-label={tUi('Loading settings')} />;
  return <>
      <StreamLinkFormatsSection notify={notify} />
      <ContentSection title={tUi("Player compatibility")} description={tUi("Optional additions for players that require them. Changes affect generated links.")}>
        <Stack spacing={2}>
          <Box>
            <FormControlLabel control={<Switch checked={addPid} onChange={handleAddPidChange} disabled={updateAddPidMutation.isPending} />} label={tUi("Append PID to stream links")} />
            <FormHelperText sx={{ ml: 0 }}>{tUi("Some players need a PID on each acestream:// link to keep streams apart.")}</FormHelperText>
          </Box>
          <Box>
            {appIdError ? (
              <Alert severity="warning" sx={{ mb: 1 }}>
                {translateKnown(appIdError)}
              </Alert>
            ) : null}
            <FormControlLabel control={<Switch checked={appid} onChange={handleAppidChange} disabled={appidSubmitting} />} label={tUi("Use AppID in stream links")} />
            <FormHelperText sx={{ ml: 0 }}>{tUi("Adds the app id to acestream:// links for players that require it (rare).")}</FormHelperText>
          </Box>
        </Stack>
      </ContentSection>
      <Button component={RouterLink} to="/playlist">{tUi("Open playlist builder")}</Button>
      <Button component={RouterLink} to="/integrations/public-address">{tUi("Manage public address")}</Button>
      </>;
}

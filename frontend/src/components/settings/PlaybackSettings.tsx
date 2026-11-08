import {
Alert,
Button,
Chip,
CircularProgress,
Stack,
TextField,
Typography
} from '@mui/material';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
useAceEngineUrl,
useAcestreamStatus,
useUpdateAceEngineUrl
} from '../../hooks/useConfig';
import { useUiText } from '../../i18n/useUiText';
import { getErrorMessage } from '../../utils/errorUtils';
import ContentSection from '../layout/ContentSection';
import PlaybackRoutingFields from '../player/PlaybackRoutingFields';

import { useSettingDraft } from '../../hooks/useSettingDraft';
type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string | (() => string), severity: FeedbackSeverity) => void;

export default function PlaybackSettings({ notify }: { notify: Notify }) {
  const tUi = useUiText();
  const aceEngineUrlQuery = useAceEngineUrl();
  const updateAceEngineUrlMutation = useUpdateAceEngineUrl();
  const acestreamStatusQuery = useAcestreamStatus({ refetchInterval: 30000 });
  const engineDraft = useSettingDraft(aceEngineUrlQuery.data, '', updateAceEngineUrlMutation.isPending);
  const aceEngineUrl = engineDraft.value;
  const setAceEngineUrl = engineDraft.change;
  const engineOnline = acestreamStatusQuery.data?.status === 'online';
  const handleAceEngineUrlSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!engineDraft.dirty || updateAceEngineUrlMutation.isPending || aceEngineUrlQuery.isError) return;
    updateAceEngineUrlMutation.mutate(aceEngineUrl, {
      onSuccess: () => { engineDraft.saved(aceEngineUrl); notify(() => (tUi('Engine URL saved')), 'success'); void acestreamStatusQuery.refetch(); },
      onError: error => notify(() => (tUi('Failed to save the engine URL: {{error}}', { error: getErrorMessage(error) })), 'error'),
    });
  };
  if (aceEngineUrlQuery.isLoading) return <CircularProgress aria-label={tUi('Loading settings')} />;
  if (aceEngineUrlQuery.isError) return <Alert severity="error" action={<Button onClick={() => void aceEngineUrlQuery.refetch()}>{tUi('Retry')}</Button>}>{getErrorMessage(aceEngineUrlQuery.error)}</Alert>;
  return <>

      <ContentSection
        title={tUi("Engine")}
        actions={
          <Button variant="outlined" size="small" onClick={() => acestreamStatusQuery.refetch()} disabled={acestreamStatusQuery.isFetching}>
            {tUi("Refresh status")}</Button>
        }
      >
        <Stack spacing={2}>
          <Stack direction="row" spacing={1.5} alignItems="center" role="status" aria-label={tUi("Engine status")}>
            {acestreamStatusQuery.isLoading ? (
              <CircularProgress size={18} />
            ) : (
              <Chip label={acestreamStatusQuery.error ? tUi("Unknown") : !aceEngineUrlQuery.data ? tUi("Not configured") : engineOnline ? tUi("Online") : tUi("Offline")} color={acestreamStatusQuery.error ? 'default' : !aceEngineUrlQuery.data ? 'default' : engineOnline ? 'success' : 'error'} variant="outlined" sx={{ fontWeight: 600, minWidth: 90 }} />
            )}
            <Typography variant="body2" color="text.secondary">
              {acestreamStatusQuery.error
                ? tUi("Could not check the engine: {{value0}}", { value0: getErrorMessage(acestreamStatusQuery.error) })
                : !aceEngineUrlQuery.data ? tUi("An engine is optional. Without one, playback and stream checks are unavailable unless a dedicated checker is configured.") : engineOnline ? tUi('The engine is reachable.') : tUi("The backend cannot reach the engine. Check its address and make sure the service is running.")}
            </Typography>
          </Stack>
          <form onSubmit={handleAceEngineUrlSubmit}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ sm: 'flex-start' }}>
              <TextField
                label={tUi("Acestream Engine URL")}
                size="small"
                value={aceEngineUrl}
                disabled={updateAceEngineUrlMutation.isPending}
                onChange={(e) => setAceEngineUrl(e.target.value)}
                helperText={tUi("Optional. Leave blank when no playback engine is available.")}
                sx={{ flex: 1, maxWidth: 480 }}
              />
              <Button type="submit" variant="contained" size="small" disabled={updateAceEngineUrlMutation.isPending || !engineDraft.dirty} sx={{ mt: 0.5 }}>
                {updateAceEngineUrlMutation.isPending ? <CircularProgress size={18} color="inherit" /> : tUi("Save engine URL")}
              </Button>
            </Stack>
          </form>
          <PlaybackRoutingFields />
        </Stack>
      </ContentSection>

      <ContentSection title={tUi("Players and network")} description={tUi("Manage the address other devices use, remote players, media servers and tuner limits in Integrations.")}>
        <Stack direction="row" gap={1} flexWrap="wrap">
          <Button component={RouterLink} to="/integrations/public-address" variant="outlined">{tUi("Public address")}</Button>
          <Button component={RouterLink} to="/integrations/remote-players" variant="outlined">{tUi("Remote players")}</Button>
          <Button component={RouterLink} to="/integrations/media-servers" variant="outlined">{tUi("Media servers and tuner")}</Button>
        </Stack>
      </ContentSection>
      </>;
}

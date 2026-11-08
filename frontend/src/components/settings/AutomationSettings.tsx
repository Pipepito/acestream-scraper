import {
Alert,
Button,
CircularProgress,
Stack,
TextField
} from '@mui/material';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
useChannelStatusInterval,
useEpgRefreshInterval,
useRescrapeInterval,
useUpdateChannelStatusInterval,
useUpdateEpgRefreshInterval,
useUpdateRescrapeInterval
} from '../../hooks/useConfig';
import { useUiText } from '../../i18n/useUiText';
import { getErrorMessage } from '../../utils/errorUtils';
import CheckEngineFields from '../CheckEngineFields';
import GuideMatchingFields from '../GuideMatchingFields';
import ContentSection from '../layout/ContentSection';
import ScheduleAnchorFields from '../ScheduleAnchorFields';
import OfflineCleanupFields from '../settings/OfflineCleanupFields';
import StreamCheckScopeField from '../StreamCheckScopeField';

import { useSettingDraft } from '../../hooks/useSettingDraft';
type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string, severity: FeedbackSeverity) => void;
interface IntervalFieldProps {
  max?: number;
  id: string;
  label: string;
  helper: string;
  value: number | '';
  saved: number | undefined;
  pending: boolean;
  onChange: (value: number | '') => void;
  onSave: () => void;
}

const IntervalField: React.FC<IntervalFieldProps> = ({ max = 168, id, label, helper, value, saved, pending, onChange, onSave }) => { const tUi = useUiText(); return (
  <Stack
    component="form"
    aria-label={tUi("{{value0}} form", { value0: label })}
    direction={{ xs: 'column', sm: 'row' }}
    spacing={1}
    alignItems="flex-start"
    onSubmit={(event: React.FormEvent) => {
      event.preventDefault();
      onSave();
    }}
  >
    <TextField
      id={id}
      label={label}
      type="number"
      size="small"
      value={value}
      disabled={pending}
      onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
      InputProps={{ inputProps: { min: 1, max, step: 1 } }}
      helperText={helper}
      sx={{ width: { xs: '100%', sm: 280 } }}
    />
    <Button type="submit" variant="outlined" size="small" disabled={pending || value === '' || !Number.isInteger(value) || value < 1 || value > max || value === saved} sx={{ mt: 0.5 }}>
      {pending ? <CircularProgress size={18} color="inherit" /> : tUi("Save")}
    </Button>
  </Stack>
); };


export default function AutomationSettings({ notify }: { notify: Notify }) {
  const tUi = useUiText();
  const channelStatusIntervalQuery = useChannelStatusInterval();
  const updateChannelStatusIntervalMutation = useUpdateChannelStatusInterval();
  const rescrapeIntervalQuery = useRescrapeInterval();
  const epgRefreshIntervalQuery = useEpgRefreshInterval();
  const updateRescrapeIntervalMutation = useUpdateRescrapeInterval();
  const updateEpgRefreshIntervalMutation = useUpdateEpgRefreshInterval();
  const rescrape = useSettingDraft<number | ''>(rescrapeIntervalQuery.data, 24, updateRescrapeIntervalMutation.isPending);
  const guide = useSettingDraft<number | ''>(epgRefreshIntervalQuery.data, 1, updateEpgRefreshIntervalMutation.isPending);
  const checks = useSettingDraft<number | ''>(channelStatusIntervalQuery.data, 60, updateChannelStatusIntervalMutation.isPending);
  const rescrapeInterval = rescrape.value, epgRefreshInterval = guide.value, channelStatusInterval = checks.value;
  const setRescrapeInterval = rescrape.change, setEpgRefreshInterval = guide.change, setChannelStatusInterval = checks.change;
  const handleRescrapeSave = () => {
    const value = rescrape.value;
    if (!rescrape.dirty || value === '' || !Number.isInteger(value) || value < 1 || value > 168 || rescrapeIntervalQuery.isError || updateRescrapeIntervalMutation.isPending) return;
    updateRescrapeIntervalMutation.mutate(value, {
      onSuccess: () => { rescrape.saved(value); notify(tUi('Sources will be scraped every {{count}} h', { count: value }), 'success'); },
      onError: error => notify(tUi('Failed to save the scrape interval: {{error}}', { error: getErrorMessage(error) }), 'error'),
    });
  };
  const handleEpgRefreshSave = () => {
    const value = guide.value;
    if (!guide.dirty || value === '' || !Number.isInteger(value) || value < 1 || value > 168 || epgRefreshIntervalQuery.isError || updateEpgRefreshIntervalMutation.isPending) return;
    updateEpgRefreshIntervalMutation.mutate(value, {
      onSuccess: () => { guide.saved(value); notify(tUi('EPG will refresh every {{count}} h', { count: value }), 'success'); },
      onError: error => notify(tUi('Failed to save the EPG refresh interval: {{error}}', { error: getErrorMessage(error) }), 'error'),
    });
  };
  const handleChannelStatusSave = () => {
    const value = checks.value;
    if (!checks.dirty || value === '' || !Number.isInteger(value) || value < 1 || value > 10080 || channelStatusIntervalQuery.isError || updateChannelStatusIntervalMutation.isPending) return;
    updateChannelStatusIntervalMutation.mutate(value, {
      onSuccess: () => { checks.saved(value); notify(tUi('Streams will be checked every {{count}} min', { count: value }), 'success'); },
      onError: error => notify(tUi('Failed to save the stream check interval: {{error}}', { error: getErrorMessage(error) }), 'error'),
    });
  };
  if (rescrapeIntervalQuery.isLoading || epgRefreshIntervalQuery.isLoading || channelStatusIntervalQuery.isLoading) return <CircularProgress aria-label={tUi('Loading settings')} />;
  return <>

      {<Button component={RouterLink} to="/recordings?tab=settings">{tUi("Recording settings")}</Button>}
      {<ContentSection title={tUi("Offline stream cleanup")}><OfflineCleanupFields /></ContentSection>}
      {<ContentSection title={tUi("Guide matching")}><GuideMatchingFields /></ContentSection>}
      <ContentSection title={tUi("Stream status checks")}><CheckEngineFields /></ContentSection>

      <ContentSection title={tUi("Automation")} description={tUi("Background jobs run on these schedules. Changes apply right away.")}>
        <Stack spacing={2.5}>
          {rescrapeIntervalQuery.isError || epgRefreshIntervalQuery.isError ? <Alert severity="error">{tUi("Some schedules could not be loaded. Reload before changing them.")}</Alert> : null}
          <IntervalField
            id="rescrape-interval"
            label={tUi("Scrape sources every (hours)")}
            helper={tUi('1 to 168 hours')}
            value={rescrapeInterval}
            saved={rescrape.dirty ? undefined : rescrape.value || undefined}
            pending={updateRescrapeIntervalMutation.isPending || rescrapeIntervalQuery.isError}
            onChange={setRescrapeInterval}
            onSave={handleRescrapeSave}
          />
          <IntervalField
            id="epg-refresh-interval"
            label={tUi("Refresh EPG every (hours)")}
            helper={tUi('1 to 168 hours')}
            value={epgRefreshInterval}
            saved={guide.dirty ? undefined : guide.value || undefined}
            pending={updateEpgRefreshIntervalMutation.isPending || epgRefreshIntervalQuery.isError}
            onChange={setEpgRefreshInterval}
            onSave={handleEpgRefreshSave}
          />
          {channelStatusIntervalQuery.isError ? <Alert severity="error">{tUi("Could not load the stream check interval. Reload to try again.")}</Alert> : null}
          <IntervalField
            id="channel-status-interval"
            label={tUi("Stream check interval (minutes)")}
            helper={tUi('Default: 60 minutes. Channel playback also checks its sources in the background.')}
            max={10080}
            value={channelStatusInterval}
            saved={checks.dirty ? undefined : checks.value || undefined}
            pending={updateChannelStatusIntervalMutation.isPending || channelStatusIntervalQuery.isLoading || channelStatusIntervalQuery.isError}
            onChange={setChannelStatusInterval}
            onSave={handleChannelStatusSave}
          />
          <StreamCheckScopeField />
          <ScheduleAnchorFields />

        </Stack>
      </ContentSection>
      <Button component={RouterLink} to="/connections/notifications">{tUi("Notifications")}</Button>

      </>;
}

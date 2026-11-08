import { getLocale } from '../../i18n/locale';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Button, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { recordingService } from '../../services/recordingService';
const RecordingOverview: React.FC<{ system?: boolean }> = ({ system }) => {
  const tUi = useUiText();
  const upcoming = useQuery({ queryKey: ['recordings', 'upcoming'], queryFn: recordingService.upcoming, refetchInterval: 10000 });
  const capabilities = useQuery({ queryKey: ['recordings', 'capabilities'], queryFn: recordingService.capabilities, enabled: Boolean(system), refetchInterval: 30000 });
  return <ContentSection title={tUi("Recordings")} actions={<Button component={RouterLink} to="/recordings">{tUi("All recordings")}</Button>}>
    {upcoming.isError ? <Alert severity="warning">{tUi("Recording status is unavailable.")}</Alert> : upcoming.isLoading ? <Typography role="status">{tUi("Loading recording status…")}</Typography> : <Stack spacing={1}>
      {!upcoming.data?.items.length ? <Typography color="text.secondary">{tUi("No recordings scheduled.")}</Typography> : upcoming.data.items.slice(0, 5).map((row) => <Typography key={row.id}>{row.snapshot.title} · {row.state} · {new Date(row.start_time).toLocaleString(getLocale())}</Typography>)}
    </Stack>}
    {system && capabilities.data ? <Typography variant="body2" sx={{ mt: 1 }}>{tUi("Capture")}{' '}{capabilities.data.enabled ? tUi("enabled") : tUi("disabled")} {' '}{tUi("· Storage")}{' '}{capabilities.data.storage_ready ? tUi("ready") : tUi("unavailable")} · {capabilities.data.message}</Typography> : null}
  </ContentSection>;
};
export default RecordingOverview;

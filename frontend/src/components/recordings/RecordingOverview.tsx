import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { Alert, Button, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { recordingService } from '../../services/recordingService';
const RecordingOverview: React.FC<{ system?: boolean }> = ({ system }) => {
  const upcoming = useQuery({ queryKey: ['recordings', 'upcoming'], queryFn: recordingService.upcoming, refetchInterval: 10000 });
  const capabilities = useQuery({ queryKey: ['recordings', 'capabilities'], queryFn: recordingService.capabilities, enabled: Boolean(system), refetchInterval: 30000 });
  return <ContentSection title="Recordings" actions={<Button component={RouterLink} to="/recordings">All recordings</Button>}>
    {upcoming.isError ? <Alert severity="warning">Recording status is unavailable.</Alert> : upcoming.isLoading ? <Typography role="status">Loading recording status…</Typography> : <Stack spacing={1}>
      {!upcoming.data?.items.length ? <Typography color="text.secondary">No recordings scheduled.</Typography> : upcoming.data.items.slice(0, 5).map((row) => <Typography key={row.id}>{row.snapshot.title} · {row.state} · {new Date(row.start_time).toLocaleString()}</Typography>)}
    </Stack>}
    {system && capabilities.data ? <Typography variant="body2" sx={{ mt: 1 }}>Capture {capabilities.data.enabled ? 'enabled' : 'disabled'} · Storage {capabilities.data.storage_ready ? 'ready' : 'unavailable'} · {capabilities.data.message}</Typography> : null}
  </ContentSection>;
};
export default RecordingOverview;

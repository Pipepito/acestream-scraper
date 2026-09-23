import { useState } from 'react';
import { Alert, Button, FormControlLabel, LinearProgress, Stack, Switch, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { guideSetupService } from '../services/guideSetupService';

export default function GuideMatchingFields() {
  const client = useQueryClient();
  const config = useQuery({ queryKey: ['guide-matching-config'], queryFn: guideSetupService.config });
  const lastRun = useQuery({ queryKey: ['guide-matching-last-run'], queryFn: guideSetupService.lastRun, refetchInterval: 30_000 });
  const [saved, setSaved] = useState(false);
  const save = useMutation({ mutationFn: guideSetupService.saveConfig, onSuccess: (value) => {
    client.setQueryData(['guide-matching-config'], value); setSaved(true);
  } });
  if (config.isLoading) return <LinearProgress aria-label="Loading automatic guide matching" />;
  if (config.isError || !config.data) return <Alert severity="error" action={<Button onClick={() => void config.refetch()}>Retry</Button>}>Could not load automatic guide matching.</Alert>;
  return <Stack spacing={1.5}>
    <FormControlLabel label="Automatically match guide channels" control={<Switch checked={config.data.enabled ?? false} disabled={save.isPending} onChange={(_, enabled) => { setSaved(false); save.mutate({ enabled }); }} />} />
    <Typography variant="body2" color="text.secondary">Off by default. When enabled, successful source scrapes and EPG refreshes create TV channels or add unassigned streams using unambiguous exact matches. Existing assignments and channel settings are preserved. Similar names, conflicting editions and competing guide sources need review.</Typography>
    {save.isError ? <Alert severity="error">Could not save automatic guide matching. Your previous setting is still shown.</Alert> : saved ? <Alert severity="success">Automatic guide matching {config.data.enabled ? 'enabled for future scrapes and refreshes' : 'disabled'}.</Alert> : null}
    {lastRun.isError ? <Alert severity="warning">The last matching result is unavailable.</Alert> : lastRun.data?.status === 'never' ?
      <Typography variant="body2">Automatic matching has not run yet.</Typography> : lastRun.data ?
        <Alert severity={lastRun.data.status === 'success' ? 'info' : 'warning'}>
          Last run: {lastRun.data.finished_at ? new Date(lastRun.data.finished_at).toLocaleString() : 'Unknown time'}. {lastRun.data.created} channels created, {lastRun.data.assigned} streams assigned.
          {lastRun.data.status === 'error' ? ' Matching failed; try reviewing matches.' : lastRun.data.status === 'partial' ? ' Some matches could not be applied.' : null}
          {(lastRun.data.review_needed ?? 0) > 0 ? ' Some matches need review.' : null}
        </Alert> : null}
    <Button component={RouterLink} to="/epg?tab=matching" sx={{ alignSelf: 'flex-start' }}>Review guide matches</Button>
  </Stack>;
}

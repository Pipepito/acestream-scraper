import { Alert, Button, LinearProgress, Stack, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { guideSetupService } from '../services/guideSetupService';

export default function GuideCoverage() {
  const query = useQuery({ queryKey: ['guide-coverage'], queryFn: guideSetupService.coverage });
  return <Stack spacing={1.5}>
    {query.isLoading ? <LinearProgress aria-label="Loading guide coverage" /> : query.isError || !query.data ?
      <Alert severity="warning" action={<Button onClick={() => void query.refetch()}>Retry</Button>}>Guide coverage could not be loaded.</Alert> : <>
        <Typography variant="body2">{query.data.linked_streams} of {query.data.streams} streams in your catalogue have a linked guide.</Typography>
        <Typography variant="body2" color="text.secondary">{query.data.guide_channels === 0
          ? 'Add and refresh an EPG source, then review matches to connect the guide to your streams.'
          : query.data.linked_streams < query.data.streams
            ? 'Review matches to create TV channels or add streams to existing channels. Unmatched streams remain available without guide data.'
            : 'Your playlist includes the guide address. Programme availability depends on the refreshed EPG source.'}</Typography>
      </>}
    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
      <Button component={RouterLink} to="/epg?tab=matching" variant="outlined">Review guide matches</Button>
      <Button component={RouterLink} to="/epg?tab=sources">Manage EPG sources</Button>
    </Stack>
  </Stack>;
}

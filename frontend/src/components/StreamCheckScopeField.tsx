import { Alert, Button, LinearProgress, Stack, TextField } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { configService } from '../services/configService';

const queryKey = ['stream-check-scope'];

export default function StreamCheckScopeField() {
  const client = useQueryClient();
  const config = useQuery({ queryKey, queryFn: configService.getStreamCheckScope });
  const save = useMutation({
    mutationFn: configService.updateStreamCheckScope,
    onSuccess: value => client.setQueryData(queryKey, value),
  });
  if (config.isLoading) return <LinearProgress aria-label="Loading stream check scope" />;
  if (config.isError || !config.data) return <Alert severity="error" action={<Button onClick={() => void config.refetch()}>Retry</Button>}>Could not load stream check scope.</Alert>;
  return <Stack spacing={0.5}>
    <TextField select SelectProps={{ native: true }} label="Streams to check" id="stream-check-scope"
      size="small" value={config.data.scope} disabled={save.isPending} sx={{ maxWidth: 450 }}
      helperText="Applies to scheduled scans and Run status check now. You can still check any stream individually."
      onChange={event => {
        const scope = event.target.value;
        if (scope === 'all' || scope === 'assigned' || scope === 'favorites') save.mutate({ scope });
      }}>
      <option value="all">All active streams</option>
      <option value="assigned">Assigned to active TV channels</option>
      <option value="favorites">Assigned to active favorite TV channels</option>
    </TextField>
    {save.isError && <Alert severity="error">Could not save stream check scope. Try again.</Alert>}
  </Stack>;
}

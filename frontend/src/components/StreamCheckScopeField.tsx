import { useUiText } from '../i18n/useUiText';
import { Alert, Button, LinearProgress, Stack, TextField } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { configService } from '../services/configService';

const queryKey = ['stream-check-scope'];

export default function StreamCheckScopeField() {
  const tUi = useUiText();
  const client = useQueryClient();
  const config = useQuery({ queryKey, queryFn: configService.getStreamCheckScope });
  const save = useMutation({
    mutationFn: configService.updateStreamCheckScope,
    onSuccess: value => client.setQueryData(queryKey, value),
  });
  if (config.isLoading) return <LinearProgress aria-label={tUi("Loading stream check scope")} />;
  if (config.isError || !config.data) return <Alert severity="error" action={<Button onClick={() => void config.refetch()}>{tUi("Retry")}</Button>}>{tUi("Could not load stream check scope.")}</Alert>;
  return <Stack spacing={0.5}>
    <TextField select SelectProps={{ native: true }} label={tUi("Streams to check")} id="stream-check-scope"
      size="small" value={config.data.scope} disabled={save.isPending} sx={{ maxWidth: 450 }}
      helperText={tUi("Applies to scheduled scans and Run status check now. You can still check any stream individually.")}
      onChange={event => {
        const scope = event.target.value;
        if (scope === 'all' || scope === 'assigned' || scope === 'favorites') save.mutate({ scope });
      }}>
      <option value="all">{tUi("All active streams")}</option>
      <option value="assigned">{tUi("Assigned to active TV channels")}</option>
      <option value="favorites">{tUi("Assigned to active favorite TV channels")}</option>
    </TextField>
    {save.isError && <Alert severity="error">{tUi("Could not save stream check scope. Try again.")}</Alert>}
  </Stack>;
}

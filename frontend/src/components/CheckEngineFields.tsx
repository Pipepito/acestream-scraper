import React, { useState } from 'react';
import { Alert, Button, FormControlLabel, LinearProgress, Stack, Switch, TextField, Typography } from '@mui/material';
import { useCheckEngine, useUpdateCheckEngine } from '../hooks/useConfig';
import type { CheckEngineConfig } from '../services/configService';
import { getErrorMessage } from '../utils/errorUtils';

export default function CheckEngineFields() {
  const query = useCheckEngine();
  const save = useUpdateCheckEngine();
  const [draft, setDraft] = useState<CheckEngineConfig | null>(null);
  const [saved, setSaved] = useState(false);
  const config = draft ?? query.data;
  if (query.isLoading) return <LinearProgress aria-label="Loading checking engine" />;
  if (!config || query.isError) return <Alert severity="error" action={<Button onClick={() => void query.refetch()}>Retry</Button>}>Unable to load checking engine settings.</Alert>;
  const change = (value: Partial<CheckEngineConfig>) => { setDraft({ ...config, ...value }); setSaved(false); save.reset(); };
  return <Stack component="form" aria-label="Checking engine" spacing={1.5} onSubmit={(event: React.FormEvent) => {
    event.preventDefault();
    save.mutate(config, { onSuccess: () => { setDraft(null); setSaved(true); } });
  }}>
    <FormControlLabel label="Use a dedicated checking engine" control={<Switch checked={config.use_dedicated} disabled={config.managed || save.isPending} onChange={(_, checked) => change({ use_dedicated: checked })} />} />
    <Typography variant="body2" color="text.secondary">{config.use_dedicated
      ? 'Stream checks use this engine. If it becomes unavailable, previous results are preserved; checks do not fall back to playback.'
      : 'Stream checks use the playback engine from the Playback tab. With no engine configured, status checks are skipped and previous results are preserved.'}</Typography>
    {config.use_dedicated && <TextField label="Checking engine URL" type="url" required size="small" value={config.url} disabled={config.managed || save.isPending} onChange={event => change({ url: event.target.value })} helperText="HTTP(S) address reachable from the scraper, including the port." sx={{ maxWidth: 480 }} />}
    {config.managed ? <Alert severity="info">The container manages this checking engine. Use Overview to start or stop it; change its configuration when deploying the container.</Alert>
      : <Typography variant="caption" color="text.secondary">This connects to an existing engine; it does not install or start one.</Typography>}
    {save.isError && <Alert severity="error">{getErrorMessage(save.error)}</Alert>}
    {saved && <Alert severity="success">Checking engine settings saved.</Alert>}
    {!config.managed && <Button type="submit" variant="outlined" disabled={!draft || save.isPending || (config.use_dedicated && !(config.url ?? '').trim())} sx={{ alignSelf: 'flex-start' }}>{save.isPending ? 'Saving…' : 'Save checking engine'}</Button>}
  </Stack>;
}

import { useUnsavedChanges } from '../UnsavedChanges';
import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Button, FormControlLabel, LinearProgress, Stack, Switch, TextField, Typography } from '@mui/material';
import { usePlaybackRouting, useUpdatePlaybackRouting } from '../../hooks/useConfig';
import type { PlaybackRouting } from '../../services/configService';
import { getErrorMessage } from '../../utils/errorUtils';

const PlaybackRoutingFields: React.FC = () => {
  const tUi = useUiText();
  const query = usePlaybackRouting();
  const save = useUpdatePlaybackRouting();
  const [draft, setDraft] = useState<PlaybackRouting | null>(null);
  const [saved, setSaved] = useState(false);
  useUnsavedChanges(Boolean(draft), save.isPending);
  const routing = draft ?? query.data;
  if (query.isLoading) return <LinearProgress aria-label={tUi("Loading playback routing")} />;
  if (query.isError || !routing) return <Alert severity="error" action={<Button onClick={() => void query.refetch()}>{tUi("Retry")}</Button>}>{tUi("Unable to load playback routing.")}</Alert>;

  const change = (value: Partial<PlaybackRouting>) => {
    setDraft({ ...routing, ...value });
    setSaved(false);
    save.reset();
  };
  return <Stack component="form" aria-label={tUi("Playback routing")} spacing={1.5} onSubmit={(event: React.FormEvent) => {
    event.preventDefault();
    save.mutate(routing, { onSuccess: () => { setDraft(null); setSaved(true); } });
  }}>
    <FormControlLabel label={tUi("Route playback through Acexy")} control={<Switch checked={routing.use_acexy ?? false}
      disabled={save.isPending} onChange={(_event, checked) => change({ use_acexy: checked })} />} />
    <Typography variant="body2" color="text.secondary">
      {routing.use_acexy
        ? tUi("Web playback, tuners and external players use Acexy through this server. Acexy manages shared streams and player IDs. Saved player link formats are bypassed.")
        : tUi("Web playback and tuner relays connect directly to the engine with a unique player ID. External players use the server relay or their saved link format.")}
    </Typography>
    <TextField label={tUi("Acexy URL")} size="small" value={routing.acexy_url ?? ''} required type="url"
      disabled={save.isPending} onChange={(event) => change({ acexy_url: event.target.value })}
      helperText={tUi("Address reachable from the backend, e.g. http://localhost:8080. Acexy must be running in MPEG-TS mode.")}
      sx={{ maxWidth: 480 }} />
    <Typography variant="caption" color="text.secondary">{tUi("Applies to new sessions. Current sessions keep their route until they close. This setting does not start or stop the Acexy service.")}</Typography>
    {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    {saved ? <Alert severity="success">{tUi("Playback routing saved.")}</Alert> : null}
    <Button type="submit" variant="outlined" disabled={!draft || save.isPending} sx={{ alignSelf: 'flex-start' }}>
      {save.isPending ? tUi("Saving…") : tUi("Save playback routing")}
    </Button>
  </Stack>;
};

export default PlaybackRoutingFields;

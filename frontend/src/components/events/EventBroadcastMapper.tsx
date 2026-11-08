import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useDeferredValue, useState } from 'react';
import { Alert, Autocomplete, Button, Checkbox, FormControlLabel, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import channelService, { type AcestreamChannel } from '../../services/channelService';
import { eventService, type SportingEvent, type EventChannelTarget } from '../../services/eventService';
import { eventErrorMessage as getErrorMessage } from './eventErrors';

interface Props { event: SportingEvent; broadcast: SportingEvent['broadcasts'][number] }
export default function EventBroadcastMapper({ event, broadcast }: Props) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState(broadcast.label);
  const [mode, setMode] = useState('channels');
  const [target, setTarget] = useState<EventChannelTarget | null>(null);
  const [selected, setSelected] = useState<AcestreamChannel | null>(null);
  const [applyToSource, setApplyToSource] = useState(true);
  const deferred = useDeferredValue(search);
  const channels = useQuery({ queryKey: ['event-mapping-channels', deferred],
    queryFn: () => channelService.getAcestreamChannels({ search: deferred, is_active: true, page_size: 30 }), enabled: open && mode === 'stream' });
  const targets = useQuery({ queryKey: ['event-broadcast-targets', deferred], queryFn: () => eventService.broadcastTargets(deferred), enabled: open && mode === 'channels' });
  const saveTarget = useMutation({ mutationFn: () => eventService.mapBroadcastTarget(event.id, event.revision, broadcast.id, target!, applyToSource),
    onSuccess: () => { setOpen(false); void cache.invalidateQueries({ queryKey: ['events'] }); } });
  const save = useMutation({ mutationFn: (channelId: string | null) => eventService.mapBroadcast(event.id, event.revision, broadcast.id, channelId, applyToSource),
    onSuccess: () => { setOpen(false); void cache.invalidateQueries({ queryKey: ['events'] }); } });
  const clearLabel = applyToSource ? `Unlink ${broadcast.label} for all events from this source`
    : broadcast.source_kept ? uiText("Use the shared link again") : uiText("Use source broadcast for this event");
  return <Stack spacing={1}>
    <Button size="small" sx={{ alignSelf: 'flex-start', textAlign: 'left' }} onClick={() => setOpen(!open)} aria-expanded={open}>{open ? tUi("Cancel mapping {{value0}}", { value0: broadcast.label }) : tUi("Link {{value0}}", { value0: broadcast.label })}</Button>
    {open ? <>
      <Typography variant="body2">{applyToSource
        ? tUi("Choose your local channel. It will be used for every event from this source that lists this broadcaster, now and after refreshes.")
        : tUi("Choose your local channel for this event only. It is kept when the schedule refreshes.")}</Typography>
      <FormControlLabel control={<Checkbox checked={applyToSource} onChange={(_, value) => setApplyToSource(value)} />} label={tUi("Apply to all events from this source with this broadcaster")} />
      <TextField select label={tUi("Link to")} value={mode} onChange={(e) => setMode(e.target.value)}><MenuItem value="channels">{tUi("TV or EPG channel")}</MenuItem><MenuItem value="stream">{tUi("Individual stream")}</MenuItem></TextField>
      {mode === 'channels' ? <Autocomplete options={targets.data ?? []} value={target} inputValue={search}
        onInputChange={(_, value) => setSearch(value)} onChange={(_, value) => setTarget(value)}
        filterOptions={(options) => options} loading={targets.isFetching}
        isOptionEqualToValue={(a, b) => a.kind === b.kind && a.id === b.id}
        getOptionLabel={(option) => `${option.name} · ${option.kind === 'tv' ? uiText("TV channel") : `EPG · ${option.source_name}`} ${option.country}`}
        renderInput={(params) => <TextField {...params} label={tUi("Find channel for {{value0}}", { value0: broadcast.label })} />}
        noOptionsText="No channels found. Try the broadcaster name used in your country." /> :
      <Autocomplete options={channels.data?.items ?? []} value={selected} inputValue={search}
        onInputChange={(_, value) => setSearch(value)} onChange={(_, value) => setSelected(value)}
        filterOptions={(options) => options} loading={channels.isFetching}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        getOptionLabel={(option) => `${option.name} · ${option.group || 'No group'} · ${option.id.slice(-8)}`}
        renderInput={(params) => <TextField {...params} label={tUi("Find stream for {{value0}}", { value0: broadcast.label })} />}
        noOptionsText="No active streams found. Try a country, edition or different name." />}
      {channels.isError ? <Alert severity="error" action={<Button onClick={() => void channels.refetch()}>{tUi("Retry search")}</Button>}>{tUi("Could not search streams.")}</Alert> : null}
      {targets.isError ? <Alert severity="error" action={<Button onClick={() => void targets.refetch()}>{tUi("Retry search")}</Button>}>{tUi("Could not search TV and EPG channels.")}</Alert> : null}
      {saveTarget.isError ? <Alert severity="error">{getErrorMessage(saveTarget.error)}</Alert> : null}
      {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
      <Stack direction="row" gap={1} flexWrap="wrap">
        <Button disabled={(mode === 'channels' ? !target : !selected) || save.isPending || saveTarget.isPending} onClick={() => mode === 'channels' ? saveTarget.mutate() : save.mutate(selected!.id)}>{tUi("Save broadcast mapping")}</Button>
        {broadcast.manually_mapped ? <Button disabled={save.isPending} onClick={() => save.mutate(null)}>{clearLabel}</Button> : null}
      </Stack>
    </> : null}
  </Stack>;
}

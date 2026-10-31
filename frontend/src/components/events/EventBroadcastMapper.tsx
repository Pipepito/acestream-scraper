import React, { useDeferredValue, useState } from 'react';
import { Alert, Autocomplete, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import channelService, { type AcestreamChannel } from '../../services/channelService';
import { eventService, type SportingEvent, type EventChannelTarget } from '../../services/eventService';
import { eventErrorMessage as getErrorMessage } from './eventErrors';

interface Props { event: SportingEvent; broadcast: SportingEvent['broadcasts'][number] }
export default function EventBroadcastMapper({ event, broadcast }: Props) {
  const cache = useQueryClient();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState(broadcast.label);
  const [mode, setMode] = useState('channels');
  const [target, setTarget] = useState<EventChannelTarget | null>(null);
  const [selected, setSelected] = useState<AcestreamChannel | null>(null);
  const deferred = useDeferredValue(search);
  const channels = useQuery({ queryKey: ['event-mapping-channels', deferred],
    queryFn: () => channelService.getAcestreamChannels({ search: deferred, is_active: true, page_size: 30 }), enabled: open && mode === 'stream' });
  const targets = useQuery({ queryKey: ['event-broadcast-targets', deferred], queryFn: () => eventService.broadcastTargets(deferred), enabled: open && mode === 'channels' });
  const saveTarget = useMutation({ mutationFn: () => eventService.mapBroadcastTarget(event.id, event.revision, broadcast.id, target!),
    onSuccess: () => { setOpen(false); void cache.invalidateQueries({ queryKey: ['events'] }); } });
  const save = useMutation({ mutationFn: (channelId: string | null) => eventService.mapBroadcast(event.id, event.revision, broadcast.id, channelId),
    onSuccess: () => { setOpen(false); void cache.invalidateQueries({ queryKey: ['events'] }); } });
  return <Stack spacing={1}>
    <Button size="small" sx={{ alignSelf: 'flex-start', textAlign: 'left' }} onClick={() => setOpen(!open)} aria-expanded={open}>{open ? `Cancel mapping ${broadcast.label}` : `Link ${broadcast.label}`}</Button>
    {open ? <>
      <Typography variant="body2">Choose your local channel. This link will be kept when the schedule refreshes.</Typography>
      <TextField select label="Link to" value={mode} onChange={(e) => setMode(e.target.value)}><MenuItem value="channels">TV or EPG channel</MenuItem><MenuItem value="stream">Individual stream</MenuItem></TextField>
      {mode === 'channels' ? <Autocomplete options={targets.data ?? []} value={target} inputValue={search}
        onInputChange={(_, value) => setSearch(value)} onChange={(_, value) => setTarget(value)}
        filterOptions={(options) => options} loading={targets.isFetching}
        isOptionEqualToValue={(a, b) => a.kind === b.kind && a.id === b.id}
        getOptionLabel={(option) => `${option.name} · ${option.kind === 'tv' ? 'TV channel' : `EPG · ${option.source_name}`} ${option.country}`}
        renderInput={(params) => <TextField {...params} label={`Find channel for ${broadcast.label}`} />}
        noOptionsText="No channels found. Try the broadcaster name used in your country." /> :
      <Autocomplete options={channels.data?.items ?? []} value={selected} inputValue={search}
        onInputChange={(_, value) => setSearch(value)} onChange={(_, value) => setSelected(value)}
        filterOptions={(options) => options} loading={channels.isFetching}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        getOptionLabel={(option) => `${option.name} · ${option.group || 'No group'} · ${option.id.slice(-8)}`}
        renderInput={(params) => <TextField {...params} label={`Find stream for ${broadcast.label}`} />}
        noOptionsText="No active streams found. Try a country, edition or different name." />}
      {channels.isError ? <Alert severity="error" action={<Button onClick={() => void channels.refetch()}>Retry search</Button>}>Could not search streams.</Alert> : null}
      {targets.isError ? <Alert severity="error" action={<Button onClick={() => void targets.refetch()}>Retry search</Button>}>Could not search TV and EPG channels.</Alert> : null}
      {saveTarget.isError ? <Alert severity="error">{getErrorMessage(saveTarget.error)}</Alert> : null}
      {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
      <Stack direction="row" gap={1} flexWrap="wrap">
        <Button disabled={(mode === 'channels' ? !target : !selected) || save.isPending || saveTarget.isPending} onClick={() => mode === 'channels' ? saveTarget.mutate() : save.mutate(selected!.id)}>Save broadcast mapping</Button>
        {broadcast.manually_mapped ? <Button disabled={save.isPending} onClick={() => save.mutate(null)}>Use source broadcast</Button> : null}
      </Stack>
    </> : null}
  </Stack>;
}

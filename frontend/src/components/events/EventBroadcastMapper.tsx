import React, { useDeferredValue, useState } from 'react';
import { Alert, Autocomplete, Button, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import channelService, { type AcestreamChannel } from '../../services/channelService';
import { eventService, type SportingEvent } from '../../services/eventService';
import { getErrorMessage } from '../../utils/errorUtils';

interface Props { event: SportingEvent; broadcast: SportingEvent['broadcasts'][number] }
export default function EventBroadcastMapper({ event, broadcast }: Props) {
  const cache = useQueryClient();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState(broadcast.label);
  const [selected, setSelected] = useState<AcestreamChannel | null>(null);
  const deferred = useDeferredValue(search);
  const channels = useQuery({ queryKey: ['event-mapping-channels', deferred],
    queryFn: () => channelService.getAcestreamChannels({ search: deferred, is_active: true, page_size: 30 }), enabled: open });
  const save = useMutation({ mutationFn: (channelId: string | null) => eventService.mapBroadcast(event.id, event.revision, broadcast.id, channelId),
    onSuccess: () => { setOpen(false); void cache.invalidateQueries({ queryKey: ['events'] }); } });
  return <Stack spacing={1}>
    <Button size="small" sx={{ alignSelf: 'flex-start', textAlign: 'left' }} onClick={() => setOpen(!open)} aria-expanded={open}>{open ? `Cancel mapping ${broadcast.label}` : `Map ${broadcast.label} to a stream`}</Button>
    {open ? <>
      <Typography variant="body2">Choose the exact country or edition. This mapping is saved for this broadcast and survives schedule refresh. No channel is created or renamed.</Typography>
      <Autocomplete options={channels.data?.items ?? []} value={selected} inputValue={search}
        onInputChange={(_, value) => setSearch(value)} onChange={(_, value) => setSelected(value)}
        filterOptions={(options) => options} loading={channels.isFetching}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        getOptionLabel={(option) => `${option.name} · ${option.group || 'No group'} · ${option.id.slice(-8)}`}
        renderInput={(params) => <TextField {...params} label={`Find stream for ${broadcast.label}`} />}
        noOptionsText="No active streams found. Try a country, edition or different name." />
      {channels.isError ? <Alert severity="error" action={<Button onClick={() => void channels.refetch()}>Retry search</Button>}>Could not search streams.</Alert> : null}
      {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
      <Stack direction="row" gap={1} flexWrap="wrap">
        <Button disabled={!selected || save.isPending} onClick={() => save.mutate(selected!.id)}>Save broadcast mapping</Button>
        {broadcast.manually_mapped ? <Button disabled={save.isPending} onClick={() => save.mutate(null)}>Use source broadcast</Button> : null}
      </Stack>
    </> : null}
  </Stack>;
}

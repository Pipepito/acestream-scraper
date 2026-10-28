import React, { useState } from 'react';
import { Alert, Box, Button, Checkbox, CircularProgress, FormControlLabel, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useConfirm } from '../ConfirmDialog';
import ContentSection from '../layout/ContentSection';
import { eventService, type EventSource, type EventRetention } from '../../services/eventService';
import { eventErrorMessage as getErrorMessage } from './eventErrors';
import { formatRelativeTime } from '../../utils/format';

function RetentionForm({ policy }: { policy: EventRetention }) {
  const cache = useQueryClient();
  const [ended, setEnded] = useState(String(policy.ended_days ?? 0));
  const [archived, setArchived] = useState(String(policy.archived_days ?? 0));
  const valid = [ended, archived].every((value) => /^\d+$/.test(value) && Number(value) <= 3650);
  const save = useMutation({ mutationFn: () => eventService.saveRetention({ ended_days: Number(ended), archived_days: Number(archived) }),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events', 'retention'] }); } });
  return <Stack spacing={2}>
    <Typography variant="subtitle1">Retention</Typography>
    <Typography variant="body2">Zero keeps events indefinitely. Daily maintenance deletes eligible events and their event-only links; followed events and permanent channels are kept. Archived events use their archive date. Ended events need a known end and a reported finished or cancelled state.</Typography>
    <Stack direction={{ xs: 'column', sm: 'row' }} gap={2}>
      <TextField label="Keep ended events (days)" type="number" value={ended} onChange={(e) => setEnded(e.target.value)} inputProps={{ min: 0, max: 3650 }} />
      <TextField label="Keep archived events (days)" type="number" value={archived} onChange={(e) => setArchived(e.target.value)} inputProps={{ min: 0, max: 3650 }} />
    </Stack>
    {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    {save.isSuccess ? <Alert severity="success">Retention saved. Changes take effect during daily maintenance.</Alert> : null}
    <Box><Button disabled={!valid || save.isPending} onClick={() => save.mutate()}>Save retention</Button></Box>
  </Stack>;
}

export default function EventSourcesPanel({ onReview }: { onReview: (source: EventSource) => void }) {
  const cache = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const remove = useMutation({ mutationFn: (source: EventSource) => eventService.deleteSource(source.id, source.revision),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events', 'sources'] }); } });
  const sources = useQuery({ queryKey: ['events', 'sources'], queryFn: eventService.sources, refetchInterval: 15000 });
  const refresh = useMutation({ mutationFn: eventService.refreshSources });
  const retention = useQuery({ queryKey: ['events', 'retention'], queryFn: eventService.retention });
  const update = useMutation({ mutationFn: ({ source, enabled }: { source: EventSource; enabled: boolean }) => eventService.updateSource(source.id, source.revision, enabled),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events', 'sources'] }); } });
  return <ContentSection title="Sources & retention">
    {dialog}
    <Stack spacing={2}>
      {remove.isError ? <Alert severity="error">{getErrorMessage(remove.error)}</Alert> : null}
      <Typography variant="body2">Saved sources refresh with the scraping schedule in Settings → Automation. Run scraping and event refresh below to queue a pass now. Only reviewed events update automatically; use Review schedule to add new events.</Typography>
      <Box><Button disabled={refresh.isPending || !sources.data?.some((source) => source.enabled)} onClick={() => refresh.mutate()}>Run scraping & event refresh</Button></Box>
      {refresh.isSuccess ? <Alert severity="info">{refresh.data.message}</Alert> : null}
      {refresh.isError ? <Alert severity="error">{getErrorMessage(refresh.error)}</Alert> : null}
      {update.isError ? <Alert severity="error">{getErrorMessage(update.error)}</Alert> : null}
      {sources.isPending ? <CircularProgress aria-label="Loading schedule sources" /> : sources.isError ? <Alert severity="error" action={<Button onClick={() => void sources.refetch()}>Retry sources</Button>}>Could not load schedule sources.</Alert> : sources.data.length === 0 ? <Typography>No saved schedule URLs or providers. Choose Add events → Built-in provider to get started.</Typography> : sources.data.map((source) => <Stack key={source.id} spacing={1} sx={{ borderBottom: 1, borderColor: 'divider', pb: 2, overflowWrap: 'anywhere' }}>
        <Typography fontWeight={600}>{source.name}</Typography>
        <Typography variant="body2">{source.origin} · {source.reviewed} reviewed events · {source.last_success ? `Last success ${formatRelativeTime(source.last_success)}` : 'Not refreshed yet'}</Typography>
        {source.provider_options ? <Typography variant="body2">Next {source.provider_options.window_days} days · Interests: {Object.values(source.provider_options.interests ?? {}).flat().join(", ") || "All events in the selected feeds"}</Typography> : null}
        {source.last_result ? <Alert severity={source.last_result.status === 'error' ? 'warning' : 'info'}>{source.last_result.message}{source.last_result.pending ? ` ${source.last_result.pending} new events available for review.` : ''}</Alert> : null}
        <Stack direction="row" gap={1} flexWrap="wrap">
          <FormControlLabel control={<Checkbox checked={source.enabled} disabled={update.isPending} onChange={(_, enabled) => update.mutate({ source, enabled })} />} label={`Automatic refresh for ${source.name}`} />
          <Button onClick={() => onReview(source)}>Review schedule</Button>
          <Button color="error" disabled={remove.isPending || update.isPending} onClick={async () => {
            if (await confirm({ title: `Delete ${source.name}?`, body: 'Remove this source and stop its automatic refresh. Imported events, manual corrections and channels will be kept.', confirmLabel: 'Delete source', danger: true })) remove.mutate(source);
          }}>Delete source</Button>
        </Stack>
      </Stack>)}
      {retention.isPending ? <CircularProgress aria-label="Loading event retention" /> : retention.isError ? <Alert severity="error" action={<Button onClick={() => void retention.refetch()}>Retry retention</Button>}>Could not load retention.</Alert> : <RetentionForm policy={retention.data} />}
    </Stack>
  </ContentSection>;
}

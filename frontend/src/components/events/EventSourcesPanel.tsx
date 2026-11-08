import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useRef } from 'react';
import { Alert, Box, Button, Checkbox, CircularProgress, FormControlLabel, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useConfirm } from '../ConfirmDialog';
import ContentSection from '../layout/ContentSection';
import { eventService, type EventSource, type EventRetention } from '../../services/eventService';
import { eventErrorMessage as getErrorMessage } from './eventErrors';
import { formatRelativeTime } from '../../utils/format';
import BroadcasterLinks from './BroadcasterLinks';
import { useSettingDraft } from '../../hooks/useSettingDraft';

function RetentionForm({ policy }: { policy: EventRetention }) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const pending = useRef(false);
  const save = useMutation({ mutationFn: (input: EventRetention) => eventService.saveRetention(input),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events', 'retention'] }); } });
  const endedDraft = useSettingDraft(String(policy.ended_days ?? 0), '0', save.isPending);
  const archivedDraft = useSettingDraft(String(policy.archived_days ?? 0), '0', save.isPending);
  const ended = endedDraft.value;
  const archived = archivedDraft.value;
  const valid = [ended, archived].every((value) => /^\d+$/.test(value) && Number(value) <= 3650);
  const submit = async () => {
    if (!valid || pending.current) return;
    pending.current = true;
    try {
      const result = await save.mutateAsync({ ended_days: Number(ended), archived_days: Number(archived) });
      endedDraft.saved(String(result.ended_days)); archivedDraft.saved(String(result.archived_days));
    } catch { /* Keep both drafts and render the mutation error. */ }
    finally { pending.current = false; }
  };
  return <Stack spacing={2}>
    <Typography variant="subtitle1">{tUi("Retention")}</Typography>
    <Typography variant="body2">{tUi("Zero keeps events indefinitely. Daily maintenance deletes eligible events and their event-only links; followed events and permanent channels are kept. Archived events use their archive date. Ended events need a known end and a reported finished or cancelled state.")}</Typography>
    <Stack direction={{ xs: 'column', sm: 'row' }} gap={2}>
      <TextField label={tUi("Keep ended events (days)")} type="number" value={ended} disabled={save.isPending} onChange={(e) => { endedDraft.change(e.target.value); save.reset(); }} inputProps={{ min: 0, max: 3650 }} />
      <TextField label={tUi("Keep archived events (days)")} type="number" value={archived} disabled={save.isPending} onChange={(e) => { archivedDraft.change(e.target.value); save.reset(); }} inputProps={{ min: 0, max: 3650 }} />
    </Stack>
    {save.isError ? <Alert severity="error">{getErrorMessage(save.error)}</Alert> : null}
    {save.isSuccess ? <Alert severity="success">{tUi("Retention saved. Changes take effect during daily maintenance.")}</Alert> : null}
    <Box><Button disabled={!valid || save.isPending} onClick={() => void submit()}>{tUi("Save retention")}</Button>{endedDraft.dirty || archivedDraft.dirty ? <Button disabled={save.isPending} onClick={() => { endedDraft.discard(); archivedDraft.discard(); save.reset(); }}>{tUi("Cancel")}</Button> : null}</Box>
  </Stack>;
}

export default function EventSourcesPanel({ onReview }: { onReview: (source: EventSource) => void }) {
  const tUi = useUiText();
  const cache = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const remove = useMutation({ mutationFn: (source: EventSource) => eventService.deleteSource(source.id, source.revision),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events', 'sources'] }); } });
  const sources = useQuery({ queryKey: ['events', 'sources'], queryFn: eventService.sources, refetchInterval: 15000 });
  const refresh = useMutation({ mutationFn: eventService.refreshSources });
  const retention = useQuery({ queryKey: ['events', 'retention'], queryFn: eventService.retention });
  const update = useMutation({ mutationFn: ({ source, enabled }: { source: EventSource; enabled: boolean }) => eventService.updateSource(source.id, source.revision, enabled),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events', 'sources'] }); } });
  return <ContentSection title={tUi("Sources & retention")}>
    {dialog}
    <Stack spacing={2}>
      {remove.isError ? <Alert severity="error">{getErrorMessage(remove.error)}</Alert> : null}
      <Typography variant="body2">{tUi("Saved sources refresh with the scraping schedule in Settings → Automation. Run scraping and event refresh below to queue a pass now. Only reviewed events update automatically; use Review schedule to add new events.")}</Typography>
      <Box><Button disabled={refresh.isPending || !sources.data?.some((source) => source.enabled)} onClick={() => refresh.mutate()}>{tUi("Run scraping & event refresh")}</Button></Box>
      {refresh.isSuccess ? <Alert severity="info">{refresh.data.status === 'already_running' ? tUi('Scraping and event refresh are already running or waiting. Follow progress in System → Scheduled jobs.') : tUi('Scraping and enabled event sources queued. Follow progress in System → Scheduled jobs.')}</Alert> : null}
      {refresh.isError ? <Alert severity="error">{getErrorMessage(refresh.error)}</Alert> : null}
      {update.isError ? <Alert severity="error">{getErrorMessage(update.error)}</Alert> : null}
      {sources.isPending ? <CircularProgress aria-label={tUi("Loading schedule sources")} /> : sources.isError ? <Alert severity="error" action={<Button onClick={() => void sources.refetch()}>{tUi("Retry sources")}</Button>}>{tUi("Could not load schedule sources.")}</Alert> : sources.data.length === 0 ? <Typography>{tUi("No saved schedule URLs or providers. Choose Add events → Built-in provider to get started.")}</Typography> : sources.data.map((source) => <Stack key={source.id} spacing={1} sx={{ borderBottom: 1, borderColor: 'divider', pb: 2, overflowWrap: 'anywhere' }}>
        <Typography fontWeight={600}>{source.name}</Typography>
        <Typography variant="body2">{source.origin} · {source.timeout_seconds ?? 15}{tUi("s timeout ·")}{' '}{source.reviewed} {' '}{tUi("reviewed events ·")}{' '}{source.last_success ? tUi("Last success {{value0}}", { value0: formatRelativeTime(source.last_success) }) : tUi("Not refreshed yet")}</Typography>
        {source.provider_options ? <Typography variant="body2">{tUi("Next")}{' '}{source.provider_options.window_days} {' '}{tUi("days · Interests:")}{' '}{Object.values(source.provider_options.interests ?? {}).flat().join(", ") || tUi("All events in the selected feeds")}</Typography> : null}
        {source.last_result ? <Alert severity={source.last_result.status === 'error' ? 'warning' : 'info'}>{source.last_result.status === 'updated' ? tUi('Reviewed events refreshed; new events need review.') : source.last_result.status === 'unchanged' ? tUi('No reviewed events were present. Existing events were preserved.') : tUi('Schedule refresh failed or changed during the request. Existing events were preserved.')}{source.last_result.pending ? tUi(" {{value0}} new events available for review.", { value0: source.last_result.pending }) : ''}</Alert> : null}
        <Stack direction="row" gap={1} flexWrap="wrap">
          <FormControlLabel control={<Checkbox checked={source.enabled} disabled={update.isPending} onChange={(_, enabled) => update.mutate({ source, enabled })} />} label={tUi("Automatic refresh for {{value0}}", { value0: source.name })} />
          <Button onClick={() => onReview(source)}>{tUi("Review schedule")}</Button>
          <Button color="error" disabled={remove.isPending || update.isPending} onClick={async () => {
            if (await confirm(() => ({ title: uiText("Delete {{name}}?", { name: source.name }), body: uiText("Remove this source and stop its automatic refresh. Imported events, manual corrections and channels will be kept."), confirmLabel: uiText("Delete source"), danger: true }))) remove.mutate(source);
          }}>{tUi("Delete source")}</Button>
        </Stack>
      </Stack>)}
      <BroadcasterLinks />
      {retention.isPending ? <CircularProgress aria-label={tUi("Loading event retention")} /> : retention.isError ? <Alert severity="error" action={<Button onClick={() => void retention.refetch()}>{tUi("Retry retention")}</Button>}>{tUi("Could not load retention.")}</Alert> : <RetentionForm policy={retention.data} />}
    </Stack>
  </ContentSection>;
}

import React from 'react';
import { Alert, Box, Button, CircularProgress, Stack, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useConfirm } from '../ConfirmDialog';
import { eventService, type BroadcasterLinkView } from '../../services/eventService';
import { eventErrorMessage as getErrorMessage } from './eventErrors';

function describe(link: BroadcasterLinkView): string {
  const target = link.target ? link.target.name : link.content_id ? `Stream ${link.content_id.slice(-8)}` : 'Unavailable channel';
  return `${link.label} → ${target} · ${link.source_name} · ${link.event_count} event${link.event_count === 1 ? '' : 's'}`;
}

/** Source-wide broadcaster links: one choice per broadcaster name, applied to every event of that source. */
export default function BroadcasterLinks() {
  const cache = useQueryClient();
  const { confirm, dialog } = useConfirm();
  const links = useQuery({ queryKey: ['events', 'broadcaster-links'], queryFn: eventService.broadcasterLinks });
  const remove = useMutation({ mutationFn: (link: BroadcasterLinkView) => eventService.deleteBroadcasterLink(link.id),
    onSuccess: () => { void cache.invalidateQueries({ queryKey: ['events'] }); } });
  return <Stack spacing={1.5}>
    {dialog}
    <Typography variant="subtitle1">Broadcaster links</Typography>
    <Typography variant="body2">Linking a broadcaster from an event with Apply to all events checked saves it here and applies it to every event from that source, now and after refreshes.</Typography>
    {remove.isError ? <Alert severity="error">{getErrorMessage(remove.error)}</Alert> : null}
    {links.isPending ? <CircularProgress aria-label="Loading broadcaster links" /> : links.isError ? <Alert severity="error" action={<Button onClick={() => void links.refetch()}>Retry links</Button>}>Could not load broadcaster links.</Alert>
      : links.data.length === 0 ? <Typography variant="body2">No broadcaster links yet. Link a broadcaster from an event with Apply to all events checked.</Typography>
      : links.data.map((link) => <Stack key={link.id} direction="row" spacing={2} alignItems="center" sx={{ overflowWrap: 'anywhere' }}>
        <Box sx={{ flex: 1, minWidth: 0 }}><Typography>{describe(link)}</Typography></Box>
        <Button color="error" aria-label={`Remove link for ${link.label}`} disabled={remove.isPending} onClick={async () => {
          if (await confirm({ title: `Remove link for ${link.label}?`, body: 'Events from this source go back to automatic matching for this broadcaster.', confirmLabel: 'Remove link', danger: true })) remove.mutate(link);
        }}>Remove</Button>
      </Stack>)}
  </Stack>;
}

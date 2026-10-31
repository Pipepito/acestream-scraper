import React, { useState } from 'react';
import { Alert, Button, Checkbox, FormControlLabel, Stack } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from './layout/ContentSection';
import { setupQueryKey, setupService } from '../services/setupService';
import { getErrorMessage } from '../utils/errorUtils';

export default function WarpStartupSection() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get });
  const [draft, setDraft] = useState<Record<string, boolean>>({});
  const [editingRevision, setEditingRevision] = useState<string | null>(null);
  const mutation = useMutation({ mutationFn: setupService.save, onSuccess: data => {
    client.setQueryData(setupQueryKey, data); setDraft({}); setEditingRevision(null);
  } });
  const options = [
    ['ENABLE_WARP', 'Enable WARP service at startup'],
    ['WARP_ENABLE_NAT', 'Connect WARP before engines start'],
    ['WARP_FORCE_IPV4', 'Prefer IPv4 for the WARP connection'],
  ];
  const checked = (name: string) => draft[name] ?? query.data?.runtime[name] === true;
  return <ContentSection title="Startup settings" description="Saved in the app. Restart the container to apply these settings; active playback will be interrupted.">
    <Stack spacing={1}>
      {query.isError ? <Alert severity="error">{getErrorMessage(query.error)} <Button onClick={() => query.refetch()}>Retry loading startup settings</Button></Alert> : null}
      {query.isPending ? <Alert severity="info">Loading startup settings…</Alert> : null}
      {query.data ? <>
        {options.map(([name, label]) => <FormControlLabel key={name} label={label}
          control={<Checkbox checked={checked(name)} disabled={mutation.isPending || (Boolean(query.data?.unavailable[name]) && !checked(name))}
            onChange={(_, value) => { setEditingRevision(previous => previous ?? query.data!.revision); setDraft(previous => ({ ...previous, [name]: value, ...(name === 'ENABLE_WARP' && !value ? { WARP_ENABLE_NAT: false } : {}) })); mutation.reset(); }} />} />)}
        {query.data.unavailable.ENABLE_WARP ? <Alert severity="info">{query.data.unavailable.ENABLE_WARP}</Alert> : null}
        {checked('WARP_ENABLE_NAT') && !checked('ENABLE_WARP') ? <Alert severity="error">Enable the WARP service before enabling automatic connection.</Alert> : null}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <Button variant="outlined" disabled={mutation.isPending || !Object.keys(draft).length || (checked('WARP_ENABLE_NAT') && !checked('ENABLE_WARP'))}
            onClick={() => mutation.mutate({ runtime: draft, expected_revision: editingRevision ?? query.data!.revision, setup_complete: query.data!.setup_complete })}>
            {mutation.isPending ? 'Saving…' : 'Save startup settings'}
          </Button>
          <Button disabled={mutation.isPending} onClick={() => { setDraft({}); setEditingRevision(null); mutation.reset(); query.refetch(); }}>Reload startup settings</Button>
        </Stack>
        {mutation.isSuccess ? <Alert severity="success">Startup settings saved. Restart the container to apply changes.</Alert> : null}
        {query.data.restart_required && !mutation.isSuccess ? <Alert severity="info">Saved runtime changes are waiting for a container restart.</Alert> : null}
        {mutation.isError ? <Alert severity="error">{getErrorMessage(mutation.error)}</Alert> : null}
      </> : null}
    </Stack>
  </ContentSection>;
}

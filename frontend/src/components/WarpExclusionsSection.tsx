import { useUnsavedChanges } from './UnsavedChanges';
import { translateKnown } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Button, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from './layout/ContentSection';
import { getWarpExclusions, saveWarpExclusions } from '../services/warpService';
import { getErrorMessage } from '../utils/errorUtils';

const key = ['warp', 'exclusions'];
const atresmedia = ['api.atresplayer.com', 'atres-live.atresmedia.com'];
const hostsFrom = (text: string) => Array.from(new Set(text.split(/[\s,]+/).filter(Boolean).map(host => host.toLowerCase()))).sort();

export default function WarpExclusionsSection() {
  const tUi = useUiText();
  const client = useQueryClient();
  const query = useQuery({ queryKey: key, queryFn: getWarpExclusions });
  const [draft, setDraft] = useState<string | null>(null);
  const [editingRevision, setEditingRevision] = useState<string | null>(null);
  const mutation = useMutation({
    mutationFn: saveWarpExclusions,
    onSuccess: data => {
      client.setQueryData(key, data);
      client.invalidateQueries({ queryKey: ['warp', 'status'] });
      setDraft(null);
      setEditingRevision(null);
    },
  });
  useUnsavedChanges(draft !== null, mutation.isPending);
  const value = draft ?? query.data?.hosts.join('\n') ?? '';
  const change = (text: string) => {
    setEditingRevision(previous => previous ?? query.data?.revision ?? null);
    setDraft(text);
    mutation.reset();
  };
  const hosts = hostsFrom(value);
  const others = query.data?.applied ? query.data.active_hosts?.filter(host => !query.data?.hosts.includes(host)) ?? [] : [];
  return <ContentSection title={tUi("Excluded hosts")} description={tUi("These hosts connect directly instead of using WARP. Changes may briefly reconnect the tunnel and interrupt playback.")}>
    <Stack spacing={2}>
      {query.isPending ? <Typography role="status">{tUi("Loading exclusions…")}</Typography> : null}
      {query.isError ? <Alert severity="error">{getErrorMessage(query.error)} <Button onClick={() => query.refetch()}>{tUi("Retry loading exclusions")}</Button></Alert> : null}
      {query.data ? <>
        {query.data.applied ? <Alert severity="success">{mutation.isSuccess ? tUi("Exclusions saved and applied.") : tUi("Saved exclusions are applied.")}</Alert>
          : <Alert severity="warning">{tUi("Saved exclusions are not applied.")}{' '}{translateKnown(query.data.error || 'Save and apply to update WARP.')}</Alert>}
        <TextField label={tUi("Hosts to exclude")} multiline minRows={3} fullWidth value={value}
          disabled={mutation.isPending} onChange={event => change(event.target.value)}
          inputProps={{ maxLength: 16384, spellCheck: false, autoCapitalize: 'none' }}
          helperText={tUi("One hostname per line, up to 64. Do not include https://, paths, ports or wildcards. An empty list removes the exclusions managed here.")} />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
          <Button disabled={mutation.isPending} onClick={() => change(Array.from(new Set([...hosts, ...atresmedia])).join('\n'))}>{tUi("Add Atresmedia")}</Button>
          <Button variant="contained" disabled={mutation.isPending || hosts.length > 64}
            onClick={() => mutation.mutate({ hosts, expected_revision: editingRevision ?? query.data!.revision })}>
            {mutation.isPending ? tUi("Applying…") : tUi("Save and apply exclusions")}
          </Button>
          <Button disabled={mutation.isPending} onClick={() => { setDraft(null); setEditingRevision(null); mutation.reset(); query.refetch(); }}>{tUi("Reload saved exclusions")}</Button>
        </Stack>
        {hosts.length > 64 ? <Alert severity="error">{tUi("Use at most 64 hostnames.")}</Alert> : null}
        {others.length ? <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{tUi("Other active WARP exclusions:")}{' '}{others.join(', ')}{tUi(". They are managed outside this form.")}</Typography> : null}
        {mutation.isError ? <Alert severity="error">{getErrorMessage(mutation.error)}</Alert> : null}
      </> : null}
    </Stack>
  </ContentSection>;
}

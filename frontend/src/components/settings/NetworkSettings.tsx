import { useUnsavedChanges } from '../UnsavedChanges';
import { useUiText } from '../../i18n/useUiText';
import React, { useState } from 'react';
import { Alert, Button, Stack, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import NetworkSettingsFields from './NetworkSettingsFields';
import { setupQueryKey, setupService, type SetupState } from '../../services/setupService';
import { ApiError } from '../../services/apiErrors';
import { getErrorMessage } from '../../utils/errorUtils';

interface NetworkDraft {
  initial: SetupState;
  values: SetupState['runtime'];
}

export default function NetworkSettings() {
  const tUi = useUiText();
  const cache = useQueryClient();
  const query = useQuery({ queryKey: setupQueryKey, queryFn: setupService.get });
  const [draft, setDraft] = useState<NetworkDraft | null>(null);
  const save = useMutation({
    mutationFn: async (edit: NetworkDraft) => {
      await cache.cancelQueries({ queryKey: setupQueryKey });
      return setupService.save({ expected_revision: edit.initial.revision, runtime: edit.values, setup_complete: edit.initial.setup_complete });
    },
    onSuccess: state => { cache.setQueryData(setupQueryKey, state); setDraft(null); },
  });
  const initial = draft?.initial ?? query.data;
  const values = { ...initial?.runtime, ...draft?.values };
  const changed = Boolean(draft && Object.entries(draft.values).some(([name, value]) => value !== draft.initial.runtime[name]));
  useUnsavedChanges(changed, save.isPending);
  const reload = async () => {
    const result = await query.refetch();
    if (result.isSuccess) { setDraft(null); save.reset(); }
  };
  return <ContentSection title={tUi("Network access")} description={tUi("Manage trusted reverse proxies, private sources, tuner networks and browser origins here or during setup. Save changes, then restart the container or application to apply them.")}>
    <Stack spacing={2} component="form" aria-label={tUi("Network settings")} onSubmit={event => { event.preventDefault(); if (draft && changed) save.mutate(draft); }}>
      {query.isError ? <Alert severity="error">{tUi("Could not load current network settings.")}{' '}<Button disabled={query.isFetching || save.isPending} onClick={() => void reload()}>{tUi("Reload saved settings")}</Button></Alert> : null}
      {!initial && !query.isError ? <Typography role="status">{tUi("Loading network settings…")}</Typography> : null}
      {initial ? <>
        {(query.data ?? initial).restart_required ? <Alert severity="info">{tUi("Restart required. Saved network changes take effect after restarting the container or application. Restarting interrupts active playback.")}</Alert> : null}
        <NetworkSettingsFields initial={initial} values={values} disabled={save.isPending}
          onChange={update => { save.reset(); setDraft(previous => ({ initial: previous?.initial ?? initial, values: { ...previous?.values, ...update } })); }} />
        {save.isError ? <Alert severity="error">{save.error instanceof ApiError && save.error.status === 409
          ? tUi("Configuration changed in another session. Reload saved settings, then reapply your changes.")
          : tUi("Could not save network settings. {{value0}}", { value0: getErrorMessage(save.error) })} <Button disabled={query.isFetching} onClick={() => void reload()}>{tUi("Reload saved settings")}</Button></Alert> : null}
        {save.isSuccess ? <Alert severity="success">{tUi("Network settings saved.")}</Alert> : null}
        <Stack direction="row" spacing={1}>
          <Button variant="contained" type="submit" disabled={!changed || save.isPending || query.isError}>{save.isPending ? tUi("Saving…") : tUi("Save network settings")}</Button>
          <Button disabled={!draft || save.isPending} onClick={() => { setDraft(null); save.reset(); }}>{tUi("Discard changes")}</Button>
        </Stack>
      </> : null}
    </Stack>
  </ContentSection>;
}

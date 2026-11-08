import React, { useId, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, Dialog, DialogContent, DialogTitle, FormControl, FormControlLabel, FormHelperText, InputLabel, MenuItem, Select, Stack, Switch, TextField } from '@mui/material';
import { useCreateURL, useUpdateURL } from '../../hooks/useScrapers';
import { scraperService, type ScrapedURL } from '../../services/scraperService';
import { useUiText } from '../../i18n/useUiText';
import { getErrorMessage } from '../../utils/errorUtils';
import { useUnsavedChanges } from '../UnsavedChanges';
import { useConfirm } from '../ConfirmDialog';

interface SourceDraft { name: string; url: string; url_type: string; enabled: boolean; scrape_bare_ids: boolean }
const empty: SourceDraft = { name: '', url: '', url_type: 'auto', enabled: true, scrape_bare_ids: false };
interface Props {
  source?: ScrapedURL;
  onSaved: (source: ScrapedURL) => void;
  onClose?: () => void;
  submitLabel?: string;
  disabled?: boolean;
  active?: boolean;
  onSavingChange?: (saving: boolean) => void;
  /** First-run import can reuse an already saved address without creating it again. */
  reuseSources?: ScrapedURL[];
}

/** Canonical source fields, provider selection, validation and save lifecycle. */
export default function SourceEditor({ source, onSaved, onClose, submitLabel, disabled = false, active = true, onSavingChange, reuseSources }: Props) {
  const t = useUiText();
  const id = useId();
  const [initial] = useState<SourceDraft>(() => source ? { name: source.name ?? '', url: source.url, url_type: source.url_type,
    enabled: source.enabled, scrape_bare_ids: source.scrape_bare_ids ?? false } : empty);
  const [value, setValue] = useState(initial);
  const [advanced, setAdvanced] = useState(Boolean(source));
  const [error, setError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);
  const submitting = useRef(false);
  const create = useCreateURL();
  const update = useUpdateURL(source?.id ?? 0);
  const providers = useQuery({ queryKey: ['builtin-providers'], queryFn: scraperService.getProviders, enabled: active && !source });
  const { confirm, dialog } = useConfirm();
  const busy = disabled || saving || create.isPending || update.isPending;
  const dirty = JSON.stringify(value) !== JSON.stringify(initial);
  useUnsavedChanges(dirty, saving || create.isPending || update.isPending);
  const change = (patch: Partial<SourceDraft>) => { setValue(previous => ({ ...previous, ...patch })); setError(null); };
  const close = async () => {
    if (busy) return;
    if (dirty && !await confirm({ title: t('Discard unsaved changes?'), body: t('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: t('Discard changes'), danger: true })) return;
    onClose?.();
  };
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (submitting.current || busy || !value.url.trim()) return;
    submitting.current = true; setSaving(true); onSavingChange?.(true); setError(null);
    try {
      const existing = !source && reuseSources?.find(item => item.url === value.url.trim());
      const payload = { ...value, url: value.url.trim(), name: value.name.trim(), scrape_bare_ids: value.url_type === 'broadcaster' ? false : value.scrape_bare_ids };
      const saved = existing || (source ? await update.mutateAsync(payload) : await create.mutateAsync(payload));
      if (!onClose) setValue(empty);
      onSaved(saved);
    } catch (failure) { setError(failure); }
    finally { submitting.current = false; setSaving(false); onSavingChange?.(false); }
  };
  const content = <Stack component="form" spacing={2} onSubmit={event => void submit(event)} aria-label={source ? t('Edit source') : t('Add source')}>
    <Box component="fieldset" disabled={busy} sx={{ border: 0, p: 0, m: 0, minWidth: 0 }}>
      <Stack spacing={2}>
        <TextField label={t('Channel source link')} value={value.url} fullWidth required disabled={busy}
          onChange={event => change({ url: event.target.value })} inputProps={{ maxLength: 4096 }}
          helperText={t('Use a channel-list link from your provider or a source you have permission to use.')} />
        {!source ? <FormControl fullWidth>
          <InputLabel id={`${id}-provider`}>{t('Built-in provider')}</InputLabel>
          <Select labelId={`${id}-provider`} label={t('Built-in provider')} disabled={busy || providers.isPending}
            value={value.url_type === 'broadcaster' ? providers.data?.find(item => item.url === value.url)?.id ?? '' : ''}
            onChange={event => {
              const provider = providers.data?.find(item => item.id === event.target.value);
              const previous = providers.data?.find(item => item.url === value.url);
              const customName = value.name && value.name !== previous?.name;
              change(provider ? { url: provider.url, url_type: 'broadcaster', name: customName ? value.name : provider.name, scrape_bare_ids: false }
                : { url: '', url_type: 'auto', name: customName ? value.name : '' });
            }}>
            <MenuItem value="">{t('Custom source URL')}</MenuItem>
            {providers.data?.map(provider => <MenuItem key={provider.id} value={provider.id}>{provider.name}</MenuItem>)}
          </Select>
          <FormHelperText>{t('Choosing a broadcaster fills in its address. Availability may depend on your region.')}</FormHelperText>
        </FormControl> : null}
        {providers.isError ? <Alert severity="error" action={<Button onClick={() => void providers.refetch()}>{t('Retry')}</Button>}>{t('Unable to load built-in providers.')}</Alert> : null}
        <TextField label={t('Friendly name (optional)')} value={value.name} fullWidth disabled={busy}
          onChange={event => change({ name: event.target.value })} inputProps={{ maxLength: 255 }} helperText={t('Shown in the source list and channel filters.')} />
        <Button aria-expanded={advanced} aria-controls={`${id}-advanced`} onClick={() => setAdvanced(previous => !previous)} sx={{ alignSelf: 'flex-start' }}>{t('Advanced source options')}</Button>
        <Stack id={`${id}-advanced`} spacing={2} hidden={!advanced} sx={{ display: advanced ? 'flex' : 'none' }}>
          <TextField select label={t('URL Type')} value={value.url_type} disabled={busy} onChange={event => change({ url_type: event.target.value })}>
            <MenuItem value="auto">{t('Auto-detect')}</MenuItem><MenuItem value="regular">{t('Regular HTTP')}</MenuItem>
            <MenuItem value="broadcaster">{t('Built-in broadcaster')}</MenuItem><MenuItem value="zeronet">{t('ZeroNet')}</MenuItem><MenuItem value="ipfs">{t('IPFS')}</MenuItem>
          </TextField>
          <FormControlLabel control={<Switch checked={value.enabled} disabled={busy} onChange={(_, enabled) => change({ enabled })} />} label={t('Enable automatic source updates')} />
          <Box><FormControlLabel control={<Switch checked={value.scrape_bare_ids} disabled={busy || value.url_type === 'broadcaster'} onChange={(_, scrape_bare_ids) => change({ scrape_bare_ids })} />} label={t('Harvest bare content IDs')} />
            <FormHelperText>{t("Also collect raw 40-character acestream hashes from pages that don't use acestream:// links.")}</FormHelperText></Box>
        </Stack>
      </Stack>
    </Box>
    {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
    <Stack direction="row" spacing={1}>
      {onClose ? <Button onClick={() => void close()} disabled={busy}>{t('Cancel')}</Button> : null}
      <Button type="submit" variant="contained" disabled={busy || !value.url.trim() || Boolean(source && !dirty)}>{saving ? t('Saving…') : submitLabel ?? (source ? t('Save source') : t('Add source'))}</Button>
    </Stack>
  </Stack>;
  return <>{onClose ? <Dialog open onClose={() => void close()} fullWidth maxWidth="sm" aria-labelledby={`${id}-title`}>
    <DialogTitle id={`${id}-title`}>{source ? t('Edit source') : t('Add source')}</DialogTitle>
    <DialogContent sx={{ pt: '8px !important' }}>{content}</DialogContent>
  </Dialog> : content}{dialog}</>;
}

import { TextField } from '@mui/material';
import React,{ useRef,useState } from 'react';
import { useSettingDraft } from '../hooks/useSettingDraft';
import { useUiText } from '../i18n/useUiText';
import { TVChannel } from '../types/tvChannelTypes';
import { getErrorMessage } from '../utils/errorUtils';

export default function ChannelNumberField({ channel, onSave, hideLabel = false }: { hideLabel?: boolean; channel: TVChannel; onSave: (channel: TVChannel, value: number | null) => Promise<void> }) {
  const tUi = useUiText();
  const saving = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<{ invalid?: boolean; cause?: unknown } | null>(null);
  const draft = useSettingDraft(String(channel.channel_number ?? ''), '', pending);
  const value = draft.value;
  const setValue = draft.change;
  const save = async () => {
    const number = value.trim() === '' ? null : Number(value);
    if (number !== null && (!Number.isSafeInteger(number) || number < 0)) { setError({ invalid: true }); return; }
    if (saving.current || !draft.dirty) return;
    saving.current = true;
    setPending(true); setError(null);
    try { await onSave(channel, number); draft.saved(number === null ? '' : String(number)); }
    catch (e) { setError({ cause: e }); }
    finally { saving.current = false; setPending(false); }
  };
  return <TextField type="number" size="small" label={hideLabel ? undefined : tUi("Number")} value={value} disabled={pending}
    inputProps={{ min: 0, step: 1, 'aria-label': tUi('Channel number for {{name}}', { name: channel.name }) }}
    error={Boolean(error)} helperText={error ? error.invalid ? tUi("Use a whole number of 0 or more.") : getErrorMessage(error.cause) : undefined}
    onChange={e => { setValue(e.target.value); setError(null); }} onBlur={() => void save()}
    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void save(); } if (e.key === 'Escape') { draft.discard(); setError(null); e.stopPropagation(); } }} />;
}

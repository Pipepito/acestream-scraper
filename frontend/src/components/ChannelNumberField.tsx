import React, { useEffect, useRef, useState } from 'react';
import { TextField } from '@mui/material';
import { TVChannel } from '../types/tvChannelTypes';
import { normalizeApiError } from '../services/apiErrors';

export default function ChannelNumberField({ channel, onSave }: { channel: TVChannel; onSave: (channel: TVChannel, value: number | null) => Promise<void> }) {
  const [value, setValue] = useState(String(channel.channel_number ?? ''));
  const saving = useRef(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { setValue(String(channel.channel_number ?? '')); }, [channel.channel_number]);
  const save = async () => {
    const number = value.trim() === '' ? null : Number(value);
    if (number !== null && (!Number.isSafeInteger(number) || number < 0)) { setError('Use a whole number of 0 or more.'); return; }
    if (saving.current || number === (channel.channel_number ?? null)) return;
    saving.current = true;
    setPending(true); setError('');
    try { await onSave(channel, number); }
    catch (e) { setError(normalizeApiError(e).message); }
    finally { saving.current = false; setPending(false); }
  };
  return <TextField type="number" size="small" label="Number" value={value} disabled={pending}
    inputProps={{ min: 0, step: 1, 'aria-label': `Channel number for ${channel.name}` }}
    error={Boolean(error)} helperText={error || undefined}
    onChange={e => { setValue(e.target.value); setError(''); }} onBlur={() => void save()}
    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void save(); } if (e.key === 'Escape') { setValue(String(channel.channel_number ?? '')); setError(''); e.stopPropagation(); } }} />;
}

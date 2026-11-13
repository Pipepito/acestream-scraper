import { translateKnown } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { renderingLimit } from './renderBudget';
import React, { useMemo } from 'react';
import { Alert, Button, Stack, Typography } from '@mui/material';
import { pathValue } from './engine';
interface Props { sample: string; records: string; pickingRecord: boolean; onPick: (path: string) => void }
export default function JsonPicker({ sample, records, pickingRecord, onPick }: Props) {
  const tUi = useUiText();
  const data = useMemo(() => {
    try {
      const limit = renderingLimit(sample);
      if (limit) return { rows: [], error: 'This JSON sample is too large for the field picker. Enter its paths manually or use a smaller example. Worker extraction tests still accept up to 32 MiB.' };
      const parsed: unknown = JSON.parse(sample);
      const selected = pathValue(parsed, records);
      const root = pickingRecord ? parsed : Array.isArray(selected) ? selected[0] : undefined;
      const rows: { path: string; label: string; records?: number }[] = [];
      const visit = (value: unknown, path: string, depth: number) => {
        if (depth > 8 || rows.length >= 200) return;
        if (Array.isArray(value)) {
          if (pickingRecord) rows.push({ path, label: '', records: value.length });
          else rows.push({ path, label: JSON.stringify(value).slice(0, 100) });
        } else if (value && typeof value === 'object') {
          Object.entries(value).forEach(([key, child]) => visit(child, path ? `${path}.${key}` : key, depth + 1));
        } else if (!pickingRecord && value !== undefined) rows.push({ path, label: String(value).slice(0, 100) });
      };
      visit(root, '', 0);
      return { rows, error: '' };
    } catch { return { rows: [], error: 'Paste a valid JSON response to select its fields.' }; }
  }, [sample, records, pickingRecord]);
  return <Stack spacing={1}>{data.error ? <Alert severity="info">{translateKnown(data.error)}</Alert> : <>
    <Typography variant="body2">{pickingRecord ? tUi("Select the array containing channels.") : tUi("Select a field from the first record. The same path is used for every record.")}</Typography>
    {data.rows.map(row => <Button key={row.path} variant="outlined" sx={{ justifyContent: 'flex-start', textAlign: 'left', overflowWrap: 'anywhere' }} onClick={() => onPick(row.path)}>{row.path || '(root)'} — {row.records === undefined ? row.label : tUi('Array · {{count}} records', { count: row.records })}</Button>)}
    {!data.rows.length && <Alert severity="info">{tUi("Choose a records array first, or enter its path below.")}</Alert>}
  </>}</Stack>;
}

import { translateKnown } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React from 'react';
import { Alert, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';
import { RecipePreview } from './types';
export default function RecipeResults({ result }: { result: RecipePreview }) {
  const tUi = useUiText();
  return <Stack spacing={2} aria-label={tUi("Extraction results")}>
    <Typography role="status">{result.record_count} {' '}{tUi("records ·")}{' '}{result.channels.length} {' '}{tUi("channels ·")}{' '}{result.invalid_count} {' '}{tUi("invalid ·")}{' '}{result.duplicate_count} {' '}{tUi("duplicates")}</Typography>
    {!result.channels.length && <Alert severity="warning">{tUi("No channels matched. Check the record rule and field selections.")}</Alert>}
    {!!result.issues.length && <Alert severity="warning"><ul>{result.issues.slice(0, 20).map((issue, index) => <li key={index}>{tUi("Record")}{' '}{issue.record}: {translateKnown(issue.message)}</li>)}</ul>{result.issues.length > 20 && tUi("{{value0}} more issues. Narrow the sample to inspect them.", { value0: result.issues.length - 20 })}</Alert>}
    <TableContainer sx={{ maxHeight: 400 }}><Table size="small" stickyHeader><TableHead><TableRow><TableCell>{tUi("Name")}</TableCell><TableCell>{tUi("ID")}</TableCell><TableCell>{tUi("Group")}</TableCell></TableRow></TableHead><TableBody>{result.channels.map(channel => <TableRow key={channel.channel_id}><TableCell>{channel.name}</TableCell><TableCell sx={{ overflowWrap: 'anywhere' }}>{channel.channel_id}</TableCell><TableCell>{channel.metadata.group_title ?? '—'}</TableCell></TableRow>)}</TableBody></Table></TableContainer>
  </Stack>;
}

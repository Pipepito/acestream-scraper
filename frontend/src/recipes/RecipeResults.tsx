import React from 'react';
import { Alert, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';
import { RecipePreview } from './types';
export default function RecipeResults({ result }: { result: RecipePreview }) {
  return <Stack spacing={2} aria-label="Extraction results">
    <Typography role="status">{result.record_count} records · {result.channels.length} channels · {result.invalid_count} invalid · {result.duplicate_count} duplicates</Typography>
    {!result.channels.length && <Alert severity="warning">No channels matched. Check the record rule and field selections.</Alert>}
    {!!result.issues.length && <Alert severity="warning"><ul>{result.issues.slice(0, 20).map((issue, index) => <li key={index}>Record {issue.record}: {issue.message}</li>)}</ul>{result.issues.length > 20 && `${result.issues.length - 20} more issues. Narrow the sample to inspect them.`}</Alert>}
    <TableContainer sx={{ maxHeight: 400 }}><Table size="small" stickyHeader><TableHead><TableRow><TableCell>Name</TableCell><TableCell>ID</TableCell><TableCell>Group</TableCell></TableRow></TableHead><TableBody>{result.channels.map(channel => <TableRow key={channel.channel_id}><TableCell>{channel.name}</TableCell><TableCell sx={{ overflowWrap: 'anywhere' }}>{channel.channel_id}</TableCell><TableCell>{channel.metadata.group_title ?? '—'}</TableCell></TableRow>)}</TableBody></Table></TableContainer>
  </Stack>;
}

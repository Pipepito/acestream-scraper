import React, { useState } from 'react';
import { Alert, Box, Snackbar } from '@mui/material';
import PageHeader from '../layout/PageHeader';
import StatusLine, { type StatusItem } from '../StatusLine';
import type { PlayerNotify } from '../player/playerCopy';

type Feedback = { message: string; severity: 'success' | 'warning' | 'error' } | null;
interface IntegrationPageProps {
  title: string;
  summary?: StatusItem[];
  children: (notify: PlayerNotify) => React.ReactNode;
}

/** Each route mounts only its own setup; feedback belongs to that page. */
export default function IntegrationPage({ title, summary, children }: IntegrationPageProps) {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const notify: PlayerNotify = (message, severity) => setFeedback({ message, severity });
  return <Box>
    <PageHeader title={title} />
    {summary ? <StatusLine aria-label={`${title} summary`} items={summary} /> : null}
    {children(notify)}
    <Snackbar open={feedback !== null} autoHideDuration={5000} onClose={() => setFeedback(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
      <Alert onClose={() => setFeedback(null)} severity={feedback?.severity ?? 'success'} variant="filled" sx={{ width: '100%' }}>{feedback?.message}</Alert>
    </Snackbar>
  </Box>;
}

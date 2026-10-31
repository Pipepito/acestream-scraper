import React, { useEffect, useState } from 'react';
import { Box, Typography } from '@mui/material';
import type { BackgroundTaskStatus } from '../../services/dashboardService';
import { formatRelativeTime } from '../../utils/format';

const UPDATES = [
  ['url_scraping', 'Sources'],
  ['epg_refresh', 'TV guide'],
  ['channel_status', 'Stream checks'],
] as const;

function nextUpdate(task: BackgroundTaskStatus | undefined, now: Date): string {
  if (!task) return 'Not scheduled';
  if (task.status === 'running') return 'Running now';
  if (task.status === 'waiting') return 'Waiting to run';
  if (!task.next_run) return 'Not scheduled';
  const remaining = new Date(task.next_run).getTime() - now.getTime();
  if (!Number.isFinite(remaining)) return 'Unavailable';
  if (remaining <= 0) return 'Due';
  if (remaining < 60_000) return 'In less than a minute';
  return formatRelativeTime(task.next_run, now);
}

/** Only the next update belongs on TV; history and results live on System status. */
export default function NextContentUpdates({ tasks }: { tasks: BackgroundTaskStatus[] }) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  return <Box component="dl" sx={{ m: 0, display: 'flex', flexWrap: 'wrap', gap: 3 }}>
    {UPDATES.map(([name, label]) => <Box key={name} sx={{ flex: '1 1 140px' }}>
      <Typography component="dt" variant="body2" color="text.secondary">{label}</Typography>
      <Typography component="dd" variant="body2" sx={{ m: 0, mt: 0.5, fontWeight: 600 }}>
        {nextUpdate(tasks.find(task => task.task_name === name), now)}
      </Typography>
    </Box>)}
  </Box>;
}

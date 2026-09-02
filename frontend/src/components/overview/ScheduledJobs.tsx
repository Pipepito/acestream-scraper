import React from 'react';
import { Chip, Table, TableBody, TableCell, TableHead, TableRow, Tooltip, Typography } from '@mui/material';
import type { BackgroundTaskStatus } from '../../services/dashboardService';
import { formatDateTime } from '../../utils/formatters';
import { formatJobName, formatRelativeTime, summarizeJobResult } from '../../utils/format';

const ORDER = ['url_scraping', 'channel_status', 'epg_refresh', 'epg_program_cleanup', 'channel_cleanup', 'activity_log_cleanup'];

const statusChip = (status: string) => {
  switch (status) {
    case 'running':
      return <Chip size="small" color="info" label="Running" />;
    case 'error':
      return <Chip size="small" color="error" label="Error" />;
    case 'removed':
      return <Chip size="small" label="Finished" />;
    default:
      return <Chip size="small" variant="outlined" label="Idle" />;
  }
};

export interface ScheduledJobsProps {
  tasks: BackgroundTaskStatus[];
}

/** What the scheduler did last and when it runs again, in plain words. */
const ScheduledJobs: React.FC<ScheduledJobsProps> = ({ tasks }) => {
  const sorted = [...tasks].sort((a, b) => {
    const ia = ORDER.indexOf(a.task_name);
    const ib = ORDER.indexOf(b.task_name);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
  if (sorted.length === 0) {
    return <Typography variant="body2">The scheduler is not running.</Typography>;
  }
  return (
    <Table size="small" aria-label="Scheduled jobs">
      <TableHead>
        <TableRow>
          <TableCell>Job</TableCell>
          <TableCell>Last run</TableCell>
          <TableCell>Result</TableCell>
          <TableCell>Next run</TableCell>
          <TableCell>Status</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {sorted.map((task) => {
          const summary = summarizeJobResult(task.task_name, task.last_result);
          const progress = task.progress && typeof task.progress.percent === 'number' ? ` · ${task.progress.percent}%` : '';
          return (
            <TableRow key={task.task_name}>
              <TableCell>{formatJobName(task.task_name)}</TableCell>
              <TableCell>
                <Tooltip title={task.last_run ? formatDateTime(task.last_run) : ''}>
                  <span>{formatRelativeTime(task.last_run)}</span>
                </Tooltip>
              </TableCell>
              <TableCell>
                {task.last_error ? (
                  <Typography variant="body2" color="error.main">
                    {task.last_error}
                  </Typography>
                ) : (
                  <span>{summary ?? '—'}{progress}</span>
                )}
              </TableCell>
              <TableCell>
                <Tooltip title={task.next_run ? formatDateTime(task.next_run) : ''}>
                  <span>{task.next_run ? formatRelativeTime(task.next_run) : '—'}</span>
                </Tooltip>
              </TableCell>
              <TableCell>{statusChip(task.status)}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

export default ScheduledJobs;

import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import { responsiveTableSx } from '../../styles/responsiveTable';
import React from 'react';
import { Box, Chip, Table, TableBody, TableCell, TableHead, TableRow, Tooltip, Typography } from '@mui/material';
import type { BackgroundTaskStatus } from '../../services/dashboardService';
import { formatDateTime } from '../../utils/formatters';
import { formatJobName, formatRelativeTime, summarizeJobResult } from '../../utils/format';

const ORDER = ['url_scraping', 'channel_status', 'epg_refresh', 'epg_program_cleanup', 'channel_cleanup', 'activity_log_cleanup'];

const statusChip = (status: string) => {
  switch (status) {
    case 'waiting':
      return <Chip size="small" color="warning" label={uiText("Waiting")} />;
    case 'running':
      return <Chip size="small" color="info" label={uiText("Running")} />;
    case 'interrupted':
      return <Chip size="small" color="warning" label={uiText("Interrupted")} />;
    case 'error':
      return <Chip size="small" color="error" label={uiText("Error")} />;
    case 'removed':
      return <Chip size="small" label={uiText("Finished")} />;
    default:
      return <Chip size="small" variant="outlined" label={uiText("Idle")} />;
  }
};

export interface ScheduledJobsProps {
  tasks: BackgroundTaskStatus[];
}

/** What the scheduler did last and when it runs again, in plain words. */
const ScheduledJobs: React.FC<ScheduledJobsProps> = ({ tasks }) => {
  const tUi = useUiText();
  const sorted = [...tasks].sort((a, b) => {
    const ia = ORDER.indexOf(a.task_name);
    const ib = ORDER.indexOf(b.task_name);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
  if (sorted.length === 0) {
    return <Typography variant="body2">{tUi("The scheduler is not running.")}</Typography>;
  }
  return (
    <Box sx={responsiveTableSx}><Table size="small" aria-label={tUi("Scheduled jobs")}>
      <TableHead>
        <TableRow>
          <TableCell>{tUi("Job")}</TableCell>
          <TableCell>{tUi("Last started")}</TableCell>
          <TableCell>{tUi("Result")}</TableCell>
          <TableCell>{tUi("Next run")}</TableCell>
          <TableCell>{tUi("Status")}</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {sorted.map((task) => {
          const summary = summarizeJobResult(task.task_name, task.last_result);
          const progress = task.progress && typeof task.progress.percent === 'number' ? ` · ${task.progress.percent}%` : '';
          return (
            <TableRow key={task.task_name}>
              <TableCell data-label={uiText("Job")}>{formatJobName(task.task_name)}</TableCell>
              <TableCell data-label={uiText("Last started")}>
                <Tooltip title={task.last_run ? formatDateTime(task.last_run) : ''}>
                  <span>{formatRelativeTime(task.last_run)}</span>
                </Tooltip>
              </TableCell>
              <TableCell data-label={uiText("Result")}>
                {task.status === 'waiting' ? <span>{tUi("Waiting for another maintenance job")}</span> : task.last_error ? (
                  <Typography variant="body2" color="error.main">
                    {task.last_error}
                  </Typography>
                ) : (
                  <span>{task.status === 'running' ? tUi("In progress") : summary ?? (task.last_run ? tUi("Completed") : tUi("Not run yet"))}{progress}</span>
                )}
              </TableCell>
              <TableCell data-label={uiText("Next run")}>
                <Tooltip title={task.next_run ? formatDateTime(task.next_run) : ''}>
                  <span>{task.next_run ? formatRelativeTime(task.next_run) : '—'}</span>
                </Tooltip>
              </TableCell>
              <TableCell data-label={uiText("Status")}>{statusChip(task.status)}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table></Box>
  );
};

export default ScheduledJobs;

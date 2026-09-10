import React from 'react';
import { render, screen, within } from '@testing-library/react';
import ScheduledJobs from '../components/overview/ScheduledJobs';
import type { BackgroundTaskStatus } from '../services/dashboardService';

const task = (overrides: Partial<BackgroundTaskStatus>): BackgroundTaskStatus => ({
  task_name: 'activity_log_cleanup', last_run: '2026-09-07T12:00:00Z', next_run: null,
  status: 'idle', last_error: null, last_result: null, progress: null, ...overrides,
});

test('shows scalar results, running starts, interruption and never-run jobs', () => {
  render(<ScheduledJobs tasks={[
    task({ last_result: 3 }),
    task({ task_name: 'channel_status', status: 'running' }),
    task({ task_name: 'epg_refresh', status: 'interrupted', last_error: 'Application stopped before this run completed' }),
    task({ task_name: 'url_scraping', last_run: null }),
  ]} />);
  expect(screen.getByRole('columnheader', { name: 'Last started' })).toBeInTheDocument();
  expect(screen.getByText('3 entries removed')).toBeInTheDocument();
  expect(screen.getByText('In progress')).toBeInTheDocument();
  expect(screen.getByText('Interrupted')).toBeInTheDocument();
  expect(screen.getByText('Not run yet')).toBeInTheDocument();
});

test('keeps manual results separate from scheduled next-run time', () => {
  render(<ScheduledJobs tasks={[
    task({ task_name: 'epg_refresh', next_run: '2026-09-08T12:00:00Z', last_result: { sources: 2, successful: 2, failed: 0 } }),
    task({ task_name: 'manual_epg_refresh', last_result: { sources: 1, successful: 1, failed: 0 } }),
  ]} />);
  const manualRow = screen.getByRole('row', { name: /Refresh EPG \(manual\)/ });
  expect(within(manualRow).getByText('1 source refreshed')).toBeInTheDocument();
  expect(within(manualRow).getByText('—')).toBeInTheDocument();
  expect(screen.getByText('2 sources refreshed')).toBeInTheDocument();
});

const statusTask: BackgroundTaskStatus = {
  task_name: 'channel_status', status: 'idle', last_run: '2026-09-10T07:00:00Z',
  next_run: '2026-09-10T08:00:00Z', last_error: null,
  last_result: { checked: 10, online: 7, offline: 3, skipped: 2, failed: 1 },
};

it('shows actual offline results separately from check errors', () => {
  render(<ScheduledJobs tasks={[statusTask]} />);
  expect(screen.getByText('10 checked, 7 online, 3 offline, 2 skipped, 1 error')).toBeInTheDocument();
});

it('shows a queued run as waiting instead of displaying its previous error', () => {
  render(<ScheduledJobs tasks={[{ ...statusTask, status: 'waiting', last_error: 'Previous failure' }]} />);
  expect(screen.getByText('Waiting for another maintenance job')).toBeInTheDocument();
  expect(screen.getByText('Waiting')).toBeInTheDocument();
  expect(screen.queryByText('Previous failure')).not.toBeInTheDocument();
});

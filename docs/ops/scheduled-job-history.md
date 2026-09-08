# Scheduled job history

Overview displays the most recent scheduler run's launch time, result, and next
scheduled time. The latest run per task is stored in `scheduled_task_states`, so
application/container restarts retain history when the database is persisted.

The launch time is recorded before the task starts work. Running tasks show
“In progress”; completion shows the returned summary (including scalar cleanup
counts), and exceptions show the failure. If the application stops before a run
records completion, the next startup labels that run “Interrupted”. Next-run times
come from the current scheduler, not the saved history. A run that has never happened
shows “Not run yet”; old in-memory history from before this change cannot be recovered.

History loading occurs after Alembic upgrades in a worker thread. Storage errors
are logged without turning successful maintenance into a failed task. Only the
latest outcome is retained per scheduler job; this is not an unbounded execution log.

Interactive scrapes, EPG refreshes, and channel checks appear as separate “manual”
rows, with no next-run time. Bulk actions record an aggregate result. If manual
runs overlap within one family, the row describes the latest-started run; an older
completion cannot overwrite it. Scheduled runs and “run now” triggers of the scheduler
retain their own rows and next-run times.

### Run stream checks now

Acestream Channels uses **Run status check now** to request the existing
`channel_status` scheduler job through
`POST /api/v1/background-tasks/channel_status/run`. The job covers all active
streams, independently of the current page, filters or selection. Already-running
jobs are not duplicated; an unavailable scheduler returns 503. Progress and results
remain under the scheduled job in Overview. Individual and playback-time checks
retain their interactive probe priority and safety guards.

The former `/channels/check_status_all` and `/acestream-channels/check_status_all`
manual bulk endpoints are removed. Historical `manual_channel_status` records are
retained in storage but no longer shown in task status responses.

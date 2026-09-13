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

### Start times and overlapping work

Settings → Automation retains the existing repeat intervals and adds optional
start times for scraping, EPG refresh and stream checks, with an IANA timezone
(e.g. `Europe/Madrid`). `GET/PUT /api/v1/config/schedule-anchors` saves all three
anchors and the timezone together in the existing settings table. Blank times
preserve startup-relative intervals; configuring a time applies immediately and
survives restarts. Saving does not launch an immediate catch-up run.

For hour intervals dividing 24, runs follow the local clock: 03:15 every six
hours means 03:15, 09:15, 15:15 and 21:15. Minute intervals dividing 60 repeat
at the selected minute offset each hour. These use calendar triggers; DST can
skip or repeat a local occurrence. Other intervals use elapsed time from the
stable anchor date 2020-01-01 in the selected timezone, so local times can shift
with DST. Overview reports the scheduler's actual next occurrence.

All recurring maintenance jobs, including scheduler “run now” requests, share a
FIFO execution queue. A due job displays **Waiting** until earlier work finishes;
its last-started time changes only when it actually starts. Repeated occurrences
of an already running/waiting job do not accumulate additional runs. Staggering
start times reduces waiting but is not the overlap guarantee. A long stream scan
can delay the other maintenance jobs. Interactive playback probes and separately
tracked manual actions retain their existing behavior and are outside this queue.

Repeat EPG imports defer the initial flush when no new channel IDs are needed,
so parsing and comparing the programme inventory does not hold the writer lock.
Stream status and scrape-status writes retry SQLite lock failures up to three
attempts, rolling back and replaying the database operation. Their blocking writes
and retry delays run off the async event loop. Failed scraper/check sessions are
rolled back before reuse; inventory identifiers are copied before processing so
error logging cannot reload objects through a failed session.

Stream-check results now distinguish **checked, online, offline, skipped and
errors**. Checked is online + offline, not the full catalogue size. Skipped
includes recently checked/in-use streams and unavailable engines, whose previous
status is preserved. Errors count exceptions, not offline streams. Older saved
results lack online/offline totals, so Overview shows their known counts without
inventing an offline count. Progress shows how much of the active inventory has
been processed.

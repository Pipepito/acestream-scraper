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


## Startup catch-up

After history is restored, interval-based guide refresh and URL scraping can run
earlier than their normal first interval when the saved last launch is overdue
or absent. The first eligible job waits five minutes after startup; when both
are due, guide refresh comes first and scraping follows five minutes later.
Cleanup jobs are not brought forward. Explicit start-time anchors remain in
control and are never overridden by catch-up.

Stream checks are reconsidered fifteen minutes after startup. The callback
rechecks the current interval, last launch, configured start time and job
availability before requesting a run. Running or queued work is not duplicated.
A saved last launch, including a failed or interrupted run, still counts toward
the normal interval; this is catch-up of missed launches, not an immediate retry
policy for failures. Run now remains available to request an earlier attempt.

Changing a schedule replaces its pending timing. Restart discards in-memory
callbacks and reconstructs eligibility from persisted history. Individual manual
source operations retain their separate history and do not count as a complete
catalogue-wide scheduled pass.

## Stream checks while watching

Scheduled and run-now catalogue status passes wait between sources while an
application TV relay or starting/ready web-player session is active. A probe
already in progress finishes and cleans up normally. Waiting holds no database
transaction and has a cumulative ten-minute budget per pass; then the pass ends
and releases the maintenance FIFO so guide refresh and scraping can continue.
Shutdown also stops waiting before another probe starts.

Incomplete runs retain their checked/online/offline/skipped/error counts and add
`deferred` plus `stop_reason` (`viewing` or `shutdown`) to the saved result.
Overview and webhook notifications distinguish this from a complete pass. The
existing `channel_status.completed` webhook event remains compatible; its title
and message explicitly say incomplete when work remains.

This guard observes application-owned sessions, including routed remote-player
playback. It cannot discover arbitrary players connected directly to an external
engine. A dedicated checker still waits because playback and checking can share
CPU/network capacity. Its failure never falls back to the playback engine.

## Fair ordering of interrupted stream checks

A status pass considers active streams only. Never-checked streams come first.
Previously checked streams are grouped by complete saved check intervals since
their last observation, oldest group first. Favorites, then streams assigned to
TV channels, take priority within each age group; older observations and stable
IDs break remaining ties. With a one-hour interval, a three-hour-old loose stream
precedes a recently checked favorite. Within the same age group, the favorite
still goes first.

A completed check moves the stream into a newer group, allowing repeated short
passes to reach older lower-priority streams. No separate cursor is stored and
ordering does not modify observations. This uses the configured stream-check
interval, not a hard-coded freshness window.

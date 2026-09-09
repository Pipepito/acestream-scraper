# Startup progress and database recovery

V2 serves its startup screen while database work runs. Open the normal app URL,
or `/startup` directly. After startup, **Settings → Startup diagnostics** opens
this screen again. It shows recent startup milestones and programme import
counts, and downloads a JSON diagnostic report. The latest 300 events are kept
in memory for the current process; restarting clears that history. The download
contains curated events, not raw application logs, database values, credentials,
SQL statements, or full filesystem paths. Container logs remain the detailed
operator source for exception tracebacks.

The normal application becomes available after database provisioning and service
startup succeed. Large V1 programme imports continue in resumable background
batches; a banner links to their progress. Duplicate, orphaned, and expired
programme rows are counted separately. If a background import stops, the app
remains usable. A restart resumes retryable imports from their saved checkpoint.

## If startup stops

The screen stays available and explains the next action. Free disk space or fix
data-folder permissions if needed, then choose **Try startup again**. Startup
never falls back to an empty database automatically.

Database failures also expose two confirmed recovery choices:

- **Recover readable data:** create the current schema through Alembic and copy
  scraper URLs and EPG sources first. Retain source IDs, URLs, enabled state,
  scraper type and bare-ID preference, but reset old errors and timestamps.
  Missing EPG names receive a placeholder rather than losing the source URL.
  Other readable V2 settings, channels, mappings, integrations, and persistent
  configuration are secondary, retaining IDs and checking foreign keys. Channels
  and programme listings can be rebuilt by scraping and refreshing recovered sources.
  Invalid or incompatible rows are skipped and counts appear in diagnostics.
  Programme listings and activity history are omitted; listings can be refreshed
  from configured EPG sources. This is best-effort recovery, not SQLite page
  repair. It does not run the V1 importer again. If no data can be recovered,
  installation stops instead of silently replacing the database with an empty one.
- **Start fresh:** create an empty current-schema database. Channels, sources,
  settings, and integrations must be configured again.

Both choices first copy existing current and legacy database files, SQLite WAL,
SHM/journal files, and migration/recovery checkpoints into a unique private
`<database directory>/backups/recovery-<id>/` folder. `current/` and `legacy/`
retain the original filenames, including sidecars. Files are flushed before
replacement; backup failure stops recovery. The clean database is built and
verified separately, then installed by rename on the same filesystem. Originals
are never automatically pruned. Backups contain private application data and
should not be shared as diagnostic reports.

A `<database stem>.recovery.json` marker prevents old V1 checkpoints from writing
into rebuilt channel IDs. If replacement is interrupted, subsequent startup
stops in recovery mode. Rebuilding again uses the preserved pre-replacement
source for salvage. Keep this marker and the referenced backups. After successful
recovery, the marker intentionally disables the original V1 import, including
its deferred programme work.

For an operator-led rollback, stop the app, preserve the current files, and
restore the entire matching `current/` and `legacy/` sets from the chosen backup,
including checkpoint and SQLite sidecar files. Remove a newly created recovery
marker only when the restored set did not contain one. Do not mix a main database
from one backup with WAL or checkpoint files from another.

## Runtime and security contract

Startup and recovery require one application worker per SQLite database. An
advisory `<database>.startup.lock` is held for the process lifetime; a second
worker fails closed and cannot reset the database. Recovery additionally blocks
other SQLite writers during the backup. Do not operate other instances or SQLite
editing tools on the data folder during recovery. Storage must support SQLite
locking and atomic rename. The supported container runtime uses one worker.

While starting or failed, normal API, playlist, and tuner requests return HTTP
503 with `Retry-After`; `/api/v1/health` remains public and also returns 503.
The SPA/static assets and `/api/v1/startup` remain reachable. Orchestrators should
allow long upgrades and must not repeatedly restart an unhealthy container while
an operator is recovering it. Docker health status alone does not restart it.

`GET /api/v1/startup`, `GET /api/v1/startup/diagnostics`, and
`POST /api/v1/startup/recover` preserve the existing optional `API_TOKEN` policy.
The startup screen accepts a token before the normal Settings page is available.
Recovery needs a JSON POST, explicit confirmation for rebuild/reset, and the
current single-use recovery nonce. It is accepted only after a startup failure;
service-only failures do not enable database replacement. Status and diagnostics
are served with `Cache-Control: no-store`.

Filesystem, database initialization, and recovery work run outside the request
event loop. Shutdown waits for active foreground database work before releasing
the data lock. Database schema upgrades still belong to Alembic; recovery adds
no schema revision and never uses `Base.metadata.create_all()`.

Pre-upgrade SQLite backups abort after 30 seconds of continuous busy/locked
responses instead of retrying indefinitely. Successful copy progress resets this
lock-wait budget, so large healthy backups may take longer. A failed partial copy
is removed and startup remains in recovery; the original database is not upgraded.
Resolve the competing database connection and retry startup to take a fresh backup.

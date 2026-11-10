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

### WARP startup recovery

When WARP is enabled, the entrypoint keeps its daemon supervised and serves the
web startup screen while configuration runs. Configuration retries for up to ten
minutes, including attempts and delays of 5, 10, 20, then at most 30 seconds.
The deadline uses monotonic time, so NTP clock corrections cannot extend it or
expire it early. `WARP_READY_ATTEMPTS` (30) and `WARP_READY_INTERVAL` (1 second)
still control each readiness wait, capped by the remaining recovery window.

Network sidecars, catalogue initialization and application jobs remain blocked
until configuration and saved exclusions succeed. Auto-connect also requires a
final JSON `Connected` status. A successful `connect` command alone is not enough.
Manual-connect and DNS-only mode retain their existing semantics. After ten
minutes, diagnostics remain available and **Try startup again** starts a fresh
window without replacing the container or web process. Missing binaries, TUN or
capabilities require fixing the deployment; a retry cannot grant permissions.

The private coordinator state and retry mailbox live under `SUPERVISOR_RUN_DIR`,
are scoped to one container boot and WARP daemon generation, and never enter
catalogue exports or database recovery. The entrypoint releases sidecars once;
database retries do not start them again. Shutdown terminates configuration
children before stopping supervised daemons.

### WARP kill switch

With automatic full tunneling (`ENABLE_WARP=true`, `WARP_ENABLE_NAT=true`,
not DNS-only), direct internet traffic stays blocked whenever the WARP daemon
is not in charge. `WARP_KILL_SWITCH=false` turns this off.

Two mechanisms cover different periods:

- While `warp-svc` runs connected or reconnecting, Cloudflare's own firewall
  (`inet cloudflare-warp`, output policy drop) rejects direct traffic. It stays
  in place after a crash until the relaunched daemon replaces it.
- A clean daemon exit removes that firewall, and it does not exist before the
  first launch. For those periods `backend/warp_guard.py` installs one private
  table, `inet scraper_warp_guard`. It passes loopback, the `CloudflareWARP`
  interface, WARP's default local exclusions and the daemon itself, and rejects
  everything else.

The daemon is recognized by its group (GID 5743), not by address: until the
tunnel is up, `warp-svc` does not mark its own registration, DNS and tunnel
packets, so a mark or a list of Cloudflare addresses cannot let it connect.

The guard is armed before the daemon first starts, whenever the daemon process
is lost, before an app-initiated WARP restart or Reconnect, and during container
shutdown. The startup coordinator removes it once the current daemon generation
is configured. The WARP supervisor relaunches the daemon after any exit,
including exit 0: before issue #329 a clean exit ended supervision and traffic
continued on the normal connection.

The block expires after 30 seconds unless refreshed, and the entrypoint removes
the table when it stops. A killed container therefore cannot leave a host or
shared network namespace without internet access; an expired table passes all
traffic. Saved exclusions and custom split-tunnel routes are honoured only by
WARP's firewall, so excluded hosts are unreachable while the guard is armed.

After network services have started, a failed relaunch configuration is retried
behind the guard for the same ten-minute window before the container exits.
Without the guard (`WARP_KILL_SWITCH=false`) the first failure still ends the
container, because nothing else stops direct traffic.

Limits, by design: **Disconnect** and non-tunnel modes chosen on the WARP page
are the operator's decision and use the normal connection; an external graceful
stop of `warp-svc` is blocked a few milliseconds after it exits, not before;
and the kill switch does not apply to manual-connect or DNS-only startup.
If the table cannot be installed (no nftables support in the host kernel, or no
`SETGID` capability), startup stops with network services paused and names
`WARP_KILL_SWITCH=false` as the way to run without it.

The startup API includes a freshly generated UTC `server_time` and a nullable
`startup_dependency` (`warp` while blocked). The browser compares server time with
its request midpoint and warns about differences greater than five minutes.
Slow requests (over five seconds), ambiguous timestamps and browser clock jumps
are excluded. The browser may itself be wrong: this is an advisory hint, never
a replacement for TLS or WARP readiness. See the
[host clock guide](../../wiki/Troubleshooting.md#warp-startup-and-system-clock).

### Application and database failures

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

# Runtime diagnostics

From **Overview → Services → Download diagnostics**, save `acestream-diagnostics.zip`
and attach it when reporting a failure. The same download is available at
`GET /api/v1/system/diagnostics`. It uses the normal optional API-token authentication
and remains available during database startup/recovery failures. Downloads are not
cached. One export is built at a time; concurrent requests receive 503 with Retry-After.

Every image flavour and architecture inherits the console collector from the common
image layer. It records application output, supervisor exit/restart messages, and
stdout/stderr from the bundled AceStream, Acexy, IPFS, ZeroNet and WARP processes
when present. Normal Docker console output continues. Process supervision, process
groups, intentional Stop handling and restart policy are unchanged.

Collection starts with the container entrypoint. It cannot recover output from before
the image was upgraded, or read Docker daemon / host kernel logs. External engines
and custom commands that redirect output elsewhere are not captured. Direct source
runs without the entrypoint have no console capture; their exports still work and
mark unavailable logs in the manifest.

The collector writes separate files under `LOG_DIR` (`/app/logs` by default):

- `scraper.log`: the application, including Uvicorn and background jobs.
- `acestream.log`, `acestream-check.log` (when the dedicated checker is enabled), `acexy.log`, `ipfs.log`, `zeronet.log`, `warp.log`, `tor.log`:
  stdout/stderr and supervisor lifecycle messages for each launched service.
- `entrypoint.log`: container setup and overall lifecycle messages.

Only processes launched by this container are captured. Disabled services do not
create new logs; files from earlier runs remain available for troubleshooting.
Each file has two rotated copies (`.log.1` and `.log.2`), each bounded to 2 MiB
(up to 54 MiB for all nine collectors). Rotation is automatic and independent of
logrotate; logrotate handles only the additional native service logs.
Recording failure leaves console output flowing. Files survive application and
engine restarts; retaining them across container replacement requires mounting
the log directory. These local files contain raw operational output: restrict
access to the log volume.

Exports contain the latest 256 KiB from each fixed log filename and its two
rotated copies, omitting missing files and rejecting symlinks and non-regular
files. For upgrade troubleshooting, existing `console.log` and its two rotations
are still exported, along with native `warp-svc.log`, `debug.log` and `error.log`.
New runs no longer write combined `console.log` files. The allowlist is bounded
at 33 files (8.25 MiB of input tails). Rotations provide recent history, not a
guaranteed time window. The manifest records UTC export
time, architecture, file availability/truncation, supervisor PIDs/start times and
intentional Stop state. Linux cgroup v2 memory counters are included when readable,
including OOM counters; these do not replace host kernel diagnostics.

Common labelled credentials, configured environment secrets, HTTP/SOCKS URLs and
IPv4 addresses are masked on export. Review the bundle before sharing: arbitrary
third-party log text can still contain sensitive information, including source names.
No database, environment dump, credentials file or user-selected filesystem path is
included. The download does not restart services, probe channels or change settings.

Player failures log their error category and bounded FFmpeg output before the
session is removed, so closing a player dialog does not discard the diagnostic cause.

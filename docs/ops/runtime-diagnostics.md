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

The collector stores `console.log` plus two rotated copies under the existing
`LOG_DIR` (`/app/logs` by default), each bounded to 2 MiB. Rotation is automatic
and independent of logrotate. Recording failure leaves console output flowing.
Files survive application and engine restarts; retaining them across container
replacement requires mounting the log directory. These local files contain raw
operational output: restrict access to the log volume.

Exports contain the latest 256 KiB from each of six fixed log filenames, omitting
missing files and rejecting symlinks and non-regular files. Rotated console copies
provide recent history, not a guaranteed time window. The manifest records UTC export
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

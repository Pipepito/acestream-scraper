# Account and Cast security contract

Operator instructions: [Accounts and casting](../../wiki/Accounts-and-Casting.md).

`AccessMiddleware` runs after trusted forwarding and before versioned/legacy
routers. Pending/account modes default-deny management APIs, including startup
recovery, diagnostics, docs/OpenAPI, setup, imports, recordings administration,
integration control and unknown routes/methods. `/playlist.m3u` is an explicit
legacy playback alias. ASGI root paths are normalized before policy selection.
Anonymous startup status contains no recovery token, events or raw failure details.
The health endpoint stays available independently of access-storage health.

| Surface | Policy |
| --- | --- |
| `GET /api/v1/auth/status` | Mode, current account, effective permissions, CSRF nonce |
| `POST /api/v1/auth/bootstrap` | First setup/activation, CSRF, rate limit, existing legacy header when configured |
| `POST /api/v1/auth/login` | HTTPS/local loopback, CSRF, bounded Argon2 verification, per-client throttling |
| Other `/auth` operations | Current account or administrator, cookie mutations require CSRF |
| `/api/v1/view/*` | Individual viewing permission and sanitized models |
| `/api/v1/viewers` | Live permission and stored active stream only |
| Viewer status/release | Independent control capability; it cannot read media or another viewer |
| Viewer HLS/segments | Read-only media capability, owner/public-policy revalidation, narrow media-only CORS |
| Playlist/XMLTV/tuner/live routes | Playback credential, Playlists permission, public playback or verified local IPTV |
| Server Cast discovery/start/control | Signed-in Cast-server permission plus verified home CIDR, unless remote control explicitly enabled |
| Browser Cast start | Cast and Live permission; no server-device discovery |
| Recording playback | Recordings permission, per-account preparation subscriptions, descriptor-relative file access |

The reviewed method/path inventory lives in `app/middleware/access.py`. Broad API
prefixes are not viewer exemptions. Query credentials never authorize administration.
Fresh setup intentionally trusts the first visitor; the operator must finish it
before public exposure. Existing deployments retain legacy access until explicit
activation. No Docker bootstrap credentials or new authentication variables exist.

Account data uses a separate mode-0600 SQLite store with Alembic ownership. Passwords
are Argon2id; session/API credentials are stored as hashes. A protection marker is
written before enabling accounts so interrupted activation fails closed. Password
changes/reset, disabling accounts and permission edits revoke sessions/credentials.
Sessions have twelve-hour idle and seven-day absolute limits, at most ten per
account; accounts and credentials are capped at one hundred each. Login cleanup
bounds expired rows. Account request bodies are limited before parsing and
validation errors never echo input secrets.

Cast discovery accepts video-capable mDNS announcements on port 8009 with numeric
RFC1918/ULA destinations. It does not issue DIAL HTTP probes to advertised URLs.
Only server-issued device IDs are accepted. Device and session inventories are
bounded. Each cast owns a viewer lease over the shared player, separate control
and media credentials, and an exact receiver media URL. Cleanup checks ownership
before sending Stop and collects late worker completion before releasing resources.
The receiver URL contains only a media capability; token/cap query values are masked
in application/access logs. Media responses permit receiver CORS without cookies.

Compatibility conversion shares player/source budgets, is limited to one shared
conversion, and yields to DVR capture. Image builds statically link target-architecture
x264 and exercise the resulting encoder on amd64, arm64 and ARMv7. Real receiver
playback and mDNS reachability remain separate from mocked protocol tests.

Production image acceptance explicitly completes the first-run account choice in
its disposable container before reading protected API/schema routes. The private
infrastructure's public-probe pin must include this wizard-aware acceptance probe;
older probes assume anonymous OpenAPI access before setup. This does not change
operator installs or authorize changes to private infrastructure policy.
The private dependency-runner image also needs target-platform x264 development
files when building this revision's GPL-enabled FFmpeg. Updating that runner
definition is a separate infrastructure review; the public application cannot
select or replace its host policy.

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
| `POST /api/v1/auth/login` | HTTPS/verified private HTTP/local loopback, CSRF, bounded Argon2 verification, per-client throttling |
| Other `/auth` operations | Current account or administrator, cookie mutations require CSRF |
| `/api/v1/view/*` | Individual viewing permission and sanitized models |
| `/api/v1/viewers` | Live permission and stored active stream only |
| Viewer status/release | Independent control capability; it cannot read media or another viewer |
| Viewer HLS/segments | Read-only media capability, owner/public-policy revalidation, narrow media-only CORS |
| Playlist/XMLTV/tuner/live routes | Playback credential, Playlists permission, public playback or verified local IPTV |
| Server Cast discovery/start/control | Verified home client; account permission when accounts are enabled. Remote control requires an account and explicit opt-in |
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
validation errors never echo input secrets. The status API reports `account_transport`
so setup/sign-in can explain a blocked connection before sending credentials.
Plaintext account access requires both a numeric RFC1918/ULA destination and a
verified RFC1918/ULA client (or actual loopback with a localhost destination).
Use the same proxy/gateway checks as Cast; configured public Cast home addresses
never widen this exception. Recheck this boundary on authenticated session reads,
not only login. HTTPS cookies remain Secure; local HTTP sessions use HttpOnly,
SameSite=Strict cookies and the existing CSRF guard.

Access and casting forms render refreshed server state until edited, preserve
unsaved drafts during refetch, and replace query data with normalized save responses.
Cancel pending reads before saving so an older response cannot overwrite the save.

Cast discovery accepts video-capable mDNS announcements on port 8009 with numeric
RFC1918/ULA destinations. It does not issue DIAL HTTP probes to advertised URLs.
An explicit Find TVs action can also probe fixed numeric private destinations on
port 8008 for a bounded Cast identity; it never follows redirects or
advertised URLs. Discovery scans at most three inferred /24 networks with 32
concurrent requests, a 20-second deadline and a 30-second cooldown. Unicast entries
expire after five minutes. Older Android TVs are recognized by the legacy
top-level UDN, name and Cast firmware revision when capabilities are absent;
modern responses reporting no display are rejected. Only server-issued device IDs are accepted. Device and session inventories are
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

TV casting has its own `/integrations/tv-casting` page and `/api/v1/cast/settings`
API. Its policy remains in the independent access store and survives account
activation/deactivation. Access form writes merge only submitted fields in an
IMMEDIATE transaction; casting writes update only their own fields. Both forms
update the query cache with the persisted response.

Without accounts, casting settings and receiver operations require a verified
home client, preserve optional API-token enforcement, and require same-origin CSRF
on mutations. A signed CSRF cookie identifies the local browser's session ownership;
it is not an administrative account and is not passed to ViewerService as a user.
Enabling accounts revokes anonymous viewer leases. Remote casting never enables
anonymous remote control, even if accounts are later disabled.

Home defaults are RFC1918/ULA client ranges only when no explicit override exists.
Proxy/gateway ambiguity remains denied. Proxy trust now defaults to loopback in
native settings, runtime metadata and entrypoint; saved values remain explicit.
The administrator-only home-connection action stores a single verified address
(/32 or /128) after UI confirmation. It cannot establish physical location: the
administrator confirms being home, and shared public addresses share this trust.
No server-egress lookup is used (VPNs and tunnels can give misleading addresses).
The automatic receiver media base uses the current trusted request origin and ASGI
root path; an optional override supports different receiver routing.

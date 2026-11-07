# Media integrations: web player, remote players, media servers

Date: 2026-09-03. Branch: `feature/media-integrations` (targets `develop`).

## 1. Goal

Let a non-technical user of the dashboard (a) watch a channel in the browser,
(b) send a channel to a VLC or Kodi player on the same network and control it,
and (c) keep a Jellyfin or Plex server's Live TV channels and guide in sync with
the TV channels curated here, with as little setup as possible.

Also in scope (added 2026-09-03 after the first review): two engine fixes
that the three features depend on in practice — the amd64 engine starts with
`--bind-all` by default (section 4.7), and the ARM images move to the newest
Android engine that passes a real playback test, because the "activate
premium" refusal is reported upstream to affect only stale engine versions
(section 4.7).

Out of scope (documented as follow-ups): Chromecast/DLNA casting, Emby, video
transcoding (MPEG-2/HEVC to H.264), Plex auto-registration, seeking (the
streams are live).

## 2. Research facts the design relies on

Verified on 2026-09-02 against the vendored engines, Acexy 0.2.2, Jellyfin
10.11.x sources, VLC 3.0.x Lua sources, Kodi sources and a running FastAPI app.
The important ones are restated here so the spec stands alone.

- Engine playback: `GET {engine}/ace/getstream?id=<hash>&pid=<uuid>&format=json`
  returns `playback_url`, `stat_url`, `command_url`; `command_url?method=stop`
  ends the session. The progressive `playback_url` is `/ace/r/<infohash>/<token>`
  and answers **302** to `/content/<infohash>/<n>`; the bytes are the untouched
  DVB transport stream. When no peer is available the engine holds the response
  open without data. The engine's own audio transcode (`transcode_audio`) is
  broken on amd64 3.2.11 and premium-gated on the Android engine, so it is
  never used.
- Browsers: hls.js plays H.264 + AAC/MP3 everywhere. Chrome cannot decode AC-3;
  MP2 is unreliable; MPEG-2 video and (mostly) HEVC are not decodable. Most
  European feeds are H.264 + AC-3 or MP2, so server-side audio transcoding is
  the common case, not the exception. Native (Safari/iOS) HLS playback cannot
  send custom headers and, per RFC 3986 §5.2.2, does not inherit the playlist's
  query string when resolving relative segment URIs.
- Acexy has no CORS headers, refuses `pid`, serves only MPEG-TS. A browser page
  cannot use it. The amd64 engine accepts only RFC1918 clients unless started
  with `--bind-all`. Both problems disappear when the backend relays bytes.
- FastAPI/uvicorn relays fine: 6 concurrent 10 Mbit/s relays cost 3-7 % CPU
  and `/api/v1/health` stayed under 25 ms. Client disconnects propagate through
  the correlation-id middleware, but Starlette never closes the body generator,
  so cleanup must be forced with an `aclose()`-guaranteeing response subclass.
  `httpx` clients default to `follow_redirects=False`. uvicorn's graceful
  shutdown waits for open connections forever unless
  `--timeout-graceful-shutdown` is set, so a live relay would block `docker
  stop` until the 10 s SIGKILL and skip the lifespan teardown.
- A purpose-built static FFmpeg 8.1.2 (mpegts/hls/mp4 muxers, h264/hevc/aac/
  ac3/eac3/mp2/mp3/mpeg2video decoders, aac encoder, http/tcp/file/pipe) is
  10.0 MB amd64, 7.4 MB arm64, 5.3 MB armv7, fully static, builds in ~30 s with
  Debian cross toolchains (no QEMU). Debian's ffmpeg costs +300-413 MB.
  ffmpeg's HLS muxer writes bare segment basenames into the playlist; `av_dump_
  format` prints the `Stream #0:…` lines only at `-loglevel info`. The minimal
  binary has no video or AC-3 encoder, so it cannot synthesize its own test
  input.
- VLC desktop: Lua HTTP interface on 8080, HTTP Basic with empty user, must be
  enabled by the user; commands `in_play`, `pl_empty`, `pl_forcepause`,
  `pl_forceresume`, `pl_stop`, `volume`; `status.json` for state. 403 when no
  password is set, 401 when wrong. `volume&val=` takes VLC's raw integer scale
  (256 = 100 %, 512 = 200 %); the `N%` form documented in VLC's README is
  **not** implemented (`luaL_checkint` rejects it) and any Lua error comes back
  as an HTTP 200 HTML "Error loading" page. VLC does not advertise itself.
- Kodi: JSON-RPC over HTTP on 8080 (`POST /jsonrpc`, Basic auth), must be
  enabled by the user (`Allow remote control via HTTP` + `from applications on
  other systems`). `Player.Open`, `Player.PlayPause`, `Player.Stop`,
  `Application.SetVolume`, `Player.GetActivePlayers`, `Player.GetProperties`,
  `Player.GetItem`, `Application.GetProperties`. `Player.Seek {seconds}` is a
  relative seek, unlike VLC's absolute `seek&val=` (one reason seek is out).
- Docker: a bridge container reaches LAN hosts outbound, so control and a TCP
  scan need no host networking. Multicast discovery would, and is not used.
  On Docker Desktop every LAN client appears as `192.168.65.1`; on Linux an
  unaddressed `8000:8000` publish also listens on `[::]` and docker-proxy
  rewrites every IPv6 client (and host-local traffic) to the bridge gateway
  `172.17.0.1`.
- Jellyfin: API key in `Authorization: MediaBrowser Token="…"` (legacy
  `X-Emby-Token` is off by default in 12.0). `POST /LiveTv/TunerHosts`
  (`Type` `hdhomerun` or `m3u`), `POST /LiveTv/ListingProviders` (`xmltv`,
  http `Path`), both upsert by `Id` and queue RefreshGuide. List with
  `GET /System/Configuration/livetv`. Trigger refresh: `GET /ScheduledTasks`,
  find `Key == "RefreshGuide"`, `POST /ScheduledTasks/Running/{Id}`. XMLTV is
  cached 1 h. M3U channel identity is `md5(tunerUrl)+md5(streamLine)`; HDHR
  identity is `hdhr_<GuideNumber>`. Jellyfin 10.11.7+ drops non-http M3U
  entries. HDHR non-legacy channels stream over HTTP from the lineup URL via
  `SharedHttpStream`. Any `ModelNumber` containing `HDTC` is treated as
  transcode-capable and, with `AllowHWTranscoding` on, Jellyfin advertises six
  fake profiles and appends `?transcode=<profile>` to the stream URL.
  `DELETE /LiveTv/TunerHosts` removes the tuner, deletes its channel cache and
  queues RefreshGuide.
- Plex: only HDHomeRun emulation; user adds the tuner in Plex Web by
  `host:port/tuner` (path prefixes work). Needs `discover.json`,
  `lineup.json`, `lineup_status.json`, `device.xml`, MPEG-TS stream URLs.
  XMLTV by URL; `<channel id>` should equal `GuideNumber`, numeric, no dots,
  with `<display-name>` entries "N Name", "N", "Name". Optional owner token:
  `POST /livetv/dvrs/{key}/reloadGuide`. Practical cap 450-480 channels (PMS
  ≥ 1.41.7 saves the channel map in one PUT whose query string carries every
  mapping and rejects it above ~40 KB, observed at 455-466 channels; 480 is
  the xTeVe/Threadfin constant from older servers). Plex Pass required in
  practice. New lineup channels need a rescan in Plex.
- Auth: `require_api_token` gates `/api/v1` (router-wide) and the player
  routes; it accepts `Authorization: Bearer`, `X-Api-Token` and `?token=` on
  every gated route. `PUBLIC_PATHS` is an exact-path set. HTTP 401 from the
  backend is interpreted by the SPA's axios interceptor as "API token
  required" (global notice). Neither Plex nor Jellyfin can send a header token
  to tuner routes. uvicorn's access logger prints the full request line
  (including any `?token=`) at INFO to stdout.
- Public URL: nothing server-side knows the externally reachable origin.
  uvicorn's own `ProxyHeadersMiddleware` (on by default) rewrites `scheme` and
  `client` from `X-Forwarded-Proto`/`X-Forwarded-For` when the peer is in
  `FORWARDED_ALLOW_IPS` (default 127.0.0.1) and discards the raw peer address;
  it never reads `X-Forwarded-Host`. Starlette's `TestClient` bypasses it.
- Repo: `EPGProgram` has no created/updated columns; `EPGSource.last_updated`
  is set on every source refresh (scheduled or manual). `TVChannel.
  acestream_channels` is an unordered relationship; `PlaylistService.
  _score_acestream` (online +10, logo +3, tvg_id +2, tvg_name +1) is private.
  `EPGService.generate_epg_xml` has no channel-subset parameter and inlines
  its lookup and window queries. `scripts/ci/validate_command_builder.sh`
  fails when a name in its tuple is absent from `entrypoint.sh`;
  `docs/builder/runtime-options.json` has no env section and `app.js`
  hard-codes every emitted env line. `scripts/ci/validate_docker_manifest_
  metadata.py` loads exactly three manifests. `Playlist.test.tsx` pins the
  copied playlist URL to `http://localhost/api/v1/playlists/m3u?…`; e2e
  `07-tv-channels.spec.ts` clicks the visible `assign tv channel to …` and
  `go to tv channel …` buttons. **`initialize_database()` runs `alembic
  upgrade head` only when the v2 DB file is missing**; an existing database
  stamped at an older revision boots without ever applying new revisions.
  `TVChannel.channel_number` is nullable, non-unique and unbounded.
  `url_guard.validate_outbound_url` always blocks the cloud-metadata address
  and blocks private targets unless `ALLOW_PRIVATE_SCRAPE_TARGETS`.

## 3. Architecture overview

```
browser ──/api/v1/player/…(HLS)──▶ FastAPI ──ffmpeg──▶ engine /ace/getstream
browser ──/api/v1/remote-players──▶ FastAPI ──HTTP──▶ VLC :8080 / Kodi :8080
                                        │              ▲ plays /tuner/stream/<id>.ts
Jellyfin/Plex ──/tuner/*.json, guide.xml, playlist.m3u──▶ FastAPI
Jellyfin/Plex ──/tuner/stream/<id>.ts──▶ FastAPI ──relay──▶ engine /ace/getstream
FastAPI ──Jellyfin REST / Plex REST──▶ media servers (register, refresh)
```

New backend domains, each following the `system.py` / `base_urls.py`
template (thin endpoint, service, repository, pydantic DTOs, tests):

| Domain | Endpoint module | Service(s) | Storage |
|---|---|---|---|
| Forwarded headers | `app/middleware/forwarded.py` (pure ASGI) | – | env |
| Stream relay | (used by tuner, player) | `engine_client.py`, `stream_relay.py`, `stream_ranking.py` | none |
| Web player | `player.py` (`/api/v1/player`) | `player_service.py` | in-memory sessions |
| Remote players | `remote_players.py` (`/api/v1/remote-players`) | `remote_players/{service,base,vlc,kodi,scan}.py` | table `remote_players` |
| Tuner (HDHR) | `tuner.py`: `hdhr_router` at `/tuner` (no token, allowlist) and `router` at `/api/v1/tuner` (settings/status, token) | `tuner_service.py` | settings keys |
| Media servers | `media_servers.py` (`/api/v1/media-servers`) | `media_servers/{service,jellyfin,plex}.py` | table `media_servers` |
| Public URL | `system.py` (`GET /api/v1/system/public-url`), `config.py` (`PUT /api/v1/config/public_base_url`) | `public_url_service.py` | settings key `public_base_url` |
| LAN target guard | – | `app/utils/url_guard.py::validate_lan_target` | – |

Frontend: one new page `Integrations` (`/integrations`, System nav section),
a `StreamPlayerDialog`, a `PlayOnMenu`, a `ChannelPickerDialog`, and a Play
action wired into the channel surfaces.

## 4. Shared foundation

### 4.1 Engine client (`app/services/engine_client.py`)

`EngineClient(engine_url, client=None)` (sync `httpx.Client`, injectable for
`httpx.MockTransport` tests) with methods `start(content_id, pid) ->
EngineSession(playback_url, stat_url, command_url, is_live)` (calls
`/ace/getstream?id=…&pid=…&format=json`), `stop(session)` (`command_url?
method=stop`, errors swallowed and logged), `stat(session) -> EngineStats(
peers, speed_down, speed_up, status)`. The engine URL is read from the DB
setting `ace_engine_url` at call time (same rule as `ChannelStatusService`;
`http://` prefixed and trailing slash stripped). Errors: `EngineUnavailableError`
(connect/timeout/5xx) and `EngineRefusedError(message)` (engine JSON `error`,
e.g. the ARM premium message). Timeouts: connect 5 s, read 15 s. `pid` is a
fresh `uuid4` hex per session; it is never reused.

### 4.2 Stream relay (`app/services/stream_relay.py`)

- `ClosingStreamingResponse(StreamingResponse)`: wraps `__call__` in
  `try/finally` and awaits `body_iterator.aclose()` inside
  `anyio.CancelScope(shield=True)`. Every streamed route uses it. On shutdown
  uvicorn cancels the relay tasks after `--timeout-graceful-shutdown 3` and
  the shielded `aclose()` path stops the engine session; relays need no
  shutdown event of their own.
- `relay_engine_stream(content_id, client_label) -> AsyncIterator[bytes]`:
  starts an engine session (the sync `EngineClient.start` runs in
  `run_in_threadpool`), then opens `playback_url` with a dedicated
  `httpx.AsyncClient(follow_redirects=True, max_redirects=3,
  timeout=httpx.Timeout(connect=5, read=30, write=30, pool=5))` and streams
  64 KiB chunks. Redirects are the engine's normal behaviour (302 to
  `/content/…`), so following them is a deliberate exception to the
  `follow_redirects=False` rule used for user-supplied targets; the relay
  refuses a final `response.url.host` that differs from the engine host and
  any status other than 200 (stops the engine session, raises
  `EngineRefusedError`, route answers 502 `ENGINE_STREAM_FAILED`). On exit
  (normal, cancel, error) the engine session is stopped. Registers itself in
  `RelayRegistry` (id, content_id, client label, started_at, bytes) so the UI
  can show active relays; a reaper closes relays whose response finished more
  than 30 s ago as belt-and-braces.
- Response headers: `Content-Type: video/mp2t`, `Cache-Control: no-store`,
  `X-Accel-Buffering: no` (nginx hint, harmless elsewhere), chunked. GET and
  HEAD are declared (`methods=["GET", "HEAD"]`); HEAD returns the headers
  only and performs no engine call.

### 4.3 Forwarded headers and public base URL

**Proxy trust is owned by the app, in one place.** `app/middleware/forwarded.py`
`ForwardedHeadersMiddleware` (pure ASGI, added in `main.py` as the outermost
user middleware so it runs before the correlation-id middleware, auth and the
tuner allowlist) always records the raw peer as `scope["state"]["peer"]`
(reachable as `request.state.peer`). When that raw peer is inside
`Settings.FORWARDED_ALLOW_IPS` (comma-separated IPs/CIDRs, parsed once with
`ipaddress`; non-IP tokens such as `testclient` are kept as literals; `*`
trusts everyone) it rewrites the scope once: `scheme` from
`X-Forwarded-Proto` (http/https only), `client` from the right-most untrusted
`X-Forwarded-For` entry (port 0; when every entry is trusted the raw peer is
kept, never the first entry), the `host` header from the first
`X-Forwarded-Host` value, and sets `scope["state"]["forwarded"] = True`.
Untrusted peers get no rewrite. uvicorn's own proxy handling is disabled
(`--no-proxy-headers` in the Dockerfile `CMD`, the entrypoint default command,
`e2e/stack/backend-start.sh`, the `uvicorn.run` call in `main.py` and the dev
command in CLAUDE.md) so the two layers cannot disagree. Everything
downstream (`request.url`, `request.client`) is therefore already corrected;
"client IP" in this spec means the corrected one and "peer" the raw one.
`FORWARDED_ALLOW_IPS` affects only `request.url`, `request.client` and
logging; it never widens `TUNER_ALLOWED_NETWORKS` (4.4).

`public_url_service.resolve_public_base_url(request, settings_repo) ->
ResolvedPublicUrl(url, source, warnings)`:

1. DB setting `public_base_url` when non-empty (`source = "setting"`).
2. Else `request.url` scheme + netloc as rewritten above (`source =
   "forwarded"` when `request.state.forwarded`, else `"request"`).

`warnings` contains `localhost` (loopback host), `docker-internal`
(172.16/12 or 192.168.65/24), `unset` (no setting, so the value depends on
how the browser reached the app) or `proxied` (setting host differs from the
request host, pointing the UI at the reverse-proxy note) so the UI can
explain that Jellyfin/Plex/VLC may not reach that address.
`GET /api/v1/system/public-url` returns `PublicUrlResponse{url, source,
warnings}`.

**Single writer.** `PUT /api/v1/config/public_base_url` (dedicated route plus
both `/config/{key}` if-chain branches in `config.py`) delegates to
`ConfigService.set_public_base_url`, the only validation site: http(s)
scheme, `host[:port]` only (no path/query/fragment/userinfo), trailing slash
stripped, empty string allowed and clears the override. Storage:
`SettingsRepository.PUBLIC_BASE_URL = "public_base_url"`;
`DEFAULT_PUBLIC_BASE_URL` is a `@property` returning
`get_settings().PUBLIC_BASE_URL` so it is read at call time (never
`os.environ` at import; `_get_class_default` and `setup_defaults()` keep
working). Every absolute URL the backend emits (tuner `BaseURL`, lineup
stream URLs, remote-player stream URLs, pasted tuner values, the SPA's
copy/QR playlist link) goes through `resolve_public_base_url`.

### 4.4 Token policy and network gates

- `/tuner/*` routes (`hdhr_router`) are registered on `app` outside
  `api_router` and never require the API token. They are gated by the
  dependency `require_tuner_network`: **both** the raw `request.state.peer`
  and the corrected `request.client.host` must be inside
  `Settings.TUNER_ALLOWED_NETWORKS` (default `127.0.0.0/8,10.0.0.0/8,
  100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10`;
  `*` disables; IPv4-mapped IPv6 addresses are unmapped first). A LAN host
  spoofing `X-Forwarded-For` fails on the raw peer; a trusted proxy
  forwarding a public client fails on the forwarded one. Denied requests get
  403 JSON `{code:"TUNER_NETWORK_DENIED", client_ip, allowed_networks}`; the
  dependency keeps a ring buffer of the last 20 denials and logs one WARNING
  per new denied IP. 100.64.0.0/10 (RFC 6598) is included because Tailscale
  assigns it and the docs steer remote players to VPNs; a host whose own WAN
  sits in an ISP CGNAT pool must not publish 8000 on that interface.
  Rationale: tuner clients cannot send tokens; the allowlist keeps the
  routes off the public internet even when port 8000 is exposed by mistake.
  The gate is only meaningful when the app sees real peers: the reference
  `docker-compose.yml` publishes `0.0.0.0:8000:8000` with a comment (an
  unaddressed publish also listens on `[::]` and docker-proxy rewrites every
  IPv6 client to the bridge gateway, which would pass the allowlist), the
  command builder emits `-p 0.0.0.0:8000:8000`, and `TunerStatus` reports
  `client_source` (`direct|forwarded|docker-gateway|loopback`) with warning
  `TUNER_ALLOWLIST_INEFFECTIVE` when the peer is a Docker gateway or loopback
  without forwarded headers. Narrowing `TUNER_ALLOWED_NETWORKS` below the
  private ranges requires listing any fronting proxy in it. `/api/v1/tuner/
  settings` and `/api/v1/tuner/status` are ordinary token-gated API routes.
- Every `/api/v1/player/...` route (session create/status/delete and the HLS
  files) accepts the token via header or `?token=`. This is existing
  `require_api_token` behaviour, not new code. Because native (Safari/iOS)
  playback cannot send headers and does not inherit the playlist's query
  string, the `index.m3u8` response propagates `?token=` onto every segment
  URI when the request itself authenticated by `?token=` (section 5.1).
- Because `?token=` becomes a routine credential carrier, `setup_logging()`
  installs a `logging.Filter` on the `uvicorn.access` logger that rewrites
  `record.args`/`record.msg` replacing `([?&]token=)[^&\s"]*` with
  `\1[redacted]` (`uvicorn.access` is stdout-only and does not propagate, so
  it is the only sink).
- HTTP 401 is reserved for the API token (`auth.py::require_api_token`; the
  SPA interceptor turns it into the API-token notice). Upstream auth failures
  (VLC/Kodi password, Jellyfin key, Plex token) are 502 with distinct
  `APIError` codes and the UI branches on `error.code`, never on status.
- **LAN target guard.** `url_guard.validate_lan_target(host, *, resolve)`:
  unwraps IPv4-mapped addresses; rejects metadata (`169.254.169.254`),
  link-local, multicast, unspecified and reserved addresses; allows private,
  loopback and global regardless of `ALLOW_PRIVATE_SCRAPE_TARGETS`. With
  `resolve=False` only literal IPs are checked; with `resolve=True` the host
  is resolved through the existing `_resolve_addresses` and every address is
  checked. Applied on create/patch/test of remote players (422
  `REMOTE_PLAYER_HOST_FORBIDDEN`) and media servers (422
  `MEDIA_SERVER_URL_FORBIDDEN`), and by every driver/client immediately
  before each outbound request (`resolve=True`; a `BlockedURLError` maps to
  the domain's `…_UNREACHABLE` code and no request is made). Driver/client
  HTTP clients are `httpx.Client(follow_redirects=False,
  timeout=httpx.Timeout(5.0, connect=2.0))`.
- The Playlist page's copy/QR URL is built from the resolved public URL
  (`usePublicUrl` in `hooks/useSystemServices.ts`; `getAbsolutePlaylistUrl(
  filters, publicBaseUrl?)` falls back to `window.location.origin` while the
  query is pending or failed) and appends the stored `apiToken` as a `token`
  query param via `URLSearchParams` (fixes the existing 401).
  `Playlist.test.tsx` is an existing test this change breaks and must be
  updated; e2e `08-playlist.spec.ts` needs no change (no proxy/token in the
  e2e stack and prefix regexes).

### 4.5 ffmpeg packaging

- Vendoring: `docker/vendor/ffmpeg/ffmpeg-8.1.2.tar.xz`, `SHA256SUMS`,
  `README.md` (bump procedure like `docker/vendor/acestream/README.md`) and
  `docker/manifests/ffmpeg.json` mirroring `acexy.json`: `{"version",
  "vendor_dir": "docker/vendor/ffmpeg", "vendored_file", "sha256",
  "source_url", "mirror_base_url", "mirror_urls"}`.
  `scripts/ci/validate_docker_manifest_metadata.py` is extended to load it,
  `require_keys` the fields, check the sha256 shape and call
  `require_vendored`; `backend/tests/docker/test_ffmpeg_vendor.py` (modelled
  on `test_acexy_vendor.py`) checks digest == manifest, validator passes,
  `build_multiarch_images.sh --print-build-args` emits `FFMPEG_VENDORED_FILE`
  / `FFMPEG_SHA256` / `FFMPEG_SOURCE_URL` / `FFMPEG_MIRROR_URLS` for every
  flavor, and the Dockerfile tries the vendored path first.
  `docs/ops/multiarch-manifest-updates.md` documents the fields.
- Dockerfile stage `ffmpeg-builder` (`FROM --platform=$BUILDPLATFORM
  debian:trixie-slim`, `ARG TARGETARCH TARGETVARIANT FFMPEG_VENDORED_FILE
  FFMPEG_SHA256 FFMPEG_SOURCE_URL FFMPEG_MIRROR_URLS`): installs
  `build-essential`, `nasm`, `xz-utils` and the matching cross toolchain
  (`gcc-x86-64-linux-gnu`, `gcc-aarch64-linux-gnu`, `gcc-arm-linux-gnueabihf`)
  when host != target, then `RUN --mount=type=bind,source=docker/vendor,
  target=/tmp/ffmpeg-vendor,readonly docker/scripts/build-ffmpeg.sh`. The
  script resolves the tarball with the `install-acestream.sh` ladder
  (vendored file → `FFMPEG_SOURCE_URL` → each mirror), verifies
  `FFMPEG_SHA256` (or, when the build-args are empty as in a plain `docker
  build`, the single `ffmpeg-*.tar.xz` under the vendor dir against the
  adjacent `SHA256SUMS`), fails hard on mismatch, configures with the set from
  section 2 (`--enable-cross-compile` when needed), builds, strips, outputs
  `/out/ffmpeg` and `/out/ffprobe`. Placed before the app-source COPY so it
  caches.
- `runtime-base`: `COPY --from=ffmpeg-builder /out/ /opt/ffmpeg/bin/`,
  `ENV FFMPEG_BINARY_PATH=/opt/ffmpeg/bin/ffmpeg`. Every flavor and platform
  gets it (+5-10 MB). No new flavor.
- `entrypoint.sh`: `IMAGE_HAS_FFMPEG` detected from `-x $FFMPEG_BINARY_PATH`
  (IPFS pattern) and exported. Backend resolves the binary as
  `Settings.FFMPEG_BINARY_PATH` (env, default empty), else
  `shutil.which("ffmpeg")`; absent means the player reports `ffmpeg_missing`
  and offers external-player actions only. `GET /api/v1/player/capabilities`
  -> `PlayerCapabilities{ffmpeg_available, ffmpeg_path, max_sessions,
  hls_dir}` (also used by e2e to skip playback tests).
- **Env contract** (one declared home for every knob):
  - `entrypoint.sh` exports, in the existing `${VAR:-default}` form next to
    the `ZERONET_URL`/`IPFS_GATEWAY_URL` block:
    `export PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-}"`,
    `export TUNER_ALLOWED_NETWORKS="${TUNER_ALLOWED_NETWORKS:-127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10}"`,
    `export PLAYER_HLS_DIR="${PLAYER_HLS_DIR:-/tmp/acestream-player}"`,
    `export PLAYER_MAX_SESSIONS="${PLAYER_MAX_SESSIONS:-3}"`,
    `export FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16}"`.
    The default app command becomes `uvicorn main:app --host 0.0.0.0 --port
    "$FLASK_PORT" --no-proxy-headers --timeout-graceful-shutdown 3` (same
    flags in the Dockerfile `CMD`). The TERM trap shuts the app down first,
    then the sidecars, so the lifespan's engine `stop` calls reach a live
    engine. `docker-compose.yml` gains `stop_grace_period: 20s`.
  - `app/config/settings.py` `Settings` fields with byte-identical defaults:
    `PUBLIC_BASE_URL: str = ""`, `TUNER_ALLOWED_NETWORKS: str = "<same list>"`,
    `PLAYER_HLS_DIR: str = "/tmp/acestream-player"`, `PLAYER_MAX_SESSIONS: int
    = 3`, `PLAYER_START_TIMEOUT_SECONDS: int = 45`, `FORWARDED_ALLOW_IPS: str
    = "<same list>"`, `FFMPEG_BINARY_PATH: str = ""`,
    `MEDIA_SERVER_MIN_REFRESH_MINUTES: int = 30`. Services read them via
    `get_settings()`, never `os.environ`, so bare-metal runs match Docker.
    Tests override with `monkeypatch.setenv` + `get_settings.cache_clear()`.
  - Command builder: `docs/builder/runtime-options.json` gains a `player`
    block of facts (`hlsDirDefault`, `hlsDirShmHint`, `maxSessionsDefault`,
    `tunerNetworksDefault`, description) and `notes.publicBaseUrl`
    (rendered with `afterRun` like `notes.externalEngineSettings`);
    `docs/index.html` + `app.js` add three optional inputs in the existing
    Advanced `<details>` (`#public-base-url-input`, `#tuner-networks-input`,
    `#player-max-sessions-input`) with `state` keys, `bind()` calls and
    `envEntries()` lines emitted only when set; the port line becomes
    `-p 0.0.0.0:8000:8000`. `PLAYER_HLS_DIR` is a hint only (needs
    `shm_size`, not worth a toggle). `scripts/ci/validate_command_builder.sh`
    tuple gains exactly `PUBLIC_BASE_URL`, `TUNER_ALLOWED_NETWORKS`,
    `PLAYER_MAX_SESSIONS` and cross-checks `player.maxSessionsDefault` /
    `tunerNetworksDefault` against the entrypoint `${VAR:-default}` captures.
    `FORWARDED_ALLOW_IPS`, `PLAYER_HLS_DIR`, `PLAYER_START_TIMEOUT_SECONDS`
    and `MEDIA_SERVER_MIN_REFRESH_MINUTES` are documented in
    `wiki/Configuration.md` and the README "Canonical Backend Settings" like
    `CHANNEL_CLEANUP_DAYS`.
  - `test_runtime_integration_guards.py` asserts the five entrypoint
    literals, `--no-proxy-headers`, `--timeout-graceful-shutdown 3`, the
    compose `0.0.0.0:8000:8000` publish and `stop_grace_period`; a settings
    test asserts the matching pydantic defaults.
- Docker tests: `backend/tests/docker/test_ffmpeg_build.py` builds the
  `ffmpeg-builder` target for each of the three platforms (cross-compiled on
  the build host, no QEMU), extracts `/out/ffmpeg`, and runs it inside
  `python:3.13-slim` for that platform (QEMU where needed, like
  `test_install_acestream.py`) against a committed fixture
  `backend/tests/docker/fixtures/sample-h264-ac3.m2ts` (2 s 64x64 H.264 +
  AC-3, ~50 KB, `.m2ts` so TypeScript globs never match it; `SHA256SUMS` and
  a README with the full-ffmpeg regeneration one-liner; `.gitattributes`
  marks `backend/tests/docker/fixtures/**` binary): `-c copy -f hls` and
  `-c:v copy -c:a aac -f hls -hls_segment_type fmp4` must succeed and
  `ffprobe` must report h264/ac3. No host or apt ffmpeg is used in CI. Added
  to the Jenkins smoke stage list.

### 4.6 Database upgrade on startup

`initialize_database()` currently runs `alembic upgrade head` only when the
v2 file is missing, so an existing install would never get `remote_players`
/ `media_servers`. Change: after the v1 migration branch, always call
`provision_schema()` (missing → upgrade; unstamped → stamp then upgrade;
stamped → upgrade, a fast no-op at head). Before it, compare the DB's
`alembic_version` with `ScriptDirectory.get_current_head()`; when they
differ, take an on-disk copy with `sqlite3.Connection.backup()` into
`<db dir>/backups/<YYYYmmdd-HHMMSS>-pre-upgrade-<current>-<target>/scraper.db`
(the `scripts/ops/preflight_v2_deploy.sh` convention) and log one line. An
upgrade failure still aborts startup (no `create_all` fallback). Tests in
`test_startup_db_init.py`: a DB stamped one revision behind boots, ends at
head with the new tables and a backup file; a DB at head boots without a
backup. CLAUDE.md ("Existing v2 dbs are left alone") and the release notes
are updated. The idempotent `has_table` guard in the new revision stays for
databases provisioned by `create_all`.

### 4.7 Engine fixes (amd64 `--bind-all`, ARM engine version)

**amd64 `--bind-all` on by default.** The native 3.2.11 engine only admits
loopback and RFC1918 peers unless started with `--bind-all`; users on
Tailscale/CGNAT, IPv6-only LANs, or non-standard Docker networks otherwise
see the relay fail with `engine_refused` while the container itself looks
healthy. `entrypoint.sh` gains `ACESTREAM_BIND_ALL` (default `true`): when
true and `ACESTREAM_START_COMMAND` is the default, `--bind-all` is appended
to the engine command on amd64; an explicit `ACESTREAM_START_COMMAND`
is never rewritten. The knob is declared in `Dockerfile` (`ENV
ACESTREAM_BIND_ALL=true`), `docker-compose.yml`, `docs/builder/runtime-options.json`
and `wiki/Configuration.md`; `scripts/ci/validate_command_builder.sh` keeps
the three in sync. Rationale for the default: the engine port is not
published by default (only the app's 8000 is), so `--bind-all` widens
nothing outside the container network; users who publish 6878 can set the
knob to `false`. On ARM the Android engine has no ACL of this kind and the
knob is ignored. (Implemented by Plan 1 Task 2.)

**ARM engine — superseded by develop (2026-09-03).** The spike
(`engine-spike-results.md`) established that no *official* Android engine lifts
the gate: the engine-only channel is frozen at 3.1.80, 3.2.18 run headless
answers `mod_detected` (attestation keyed on the app identity the bridge
reports) and, with the APK's real identity, the same premium denial;
AceStream's own policy (forum t3928/t3945/t4002) makes live playback outside
their player Premium-only. While that spike ran, `develop` shipped
`166b5cd feat: use non-premium ARM64 AceStream engine`: `linux/arm64` moves off
the official APK to the community distribution `jopsis/acestream:v3.2.17-fix`,
pinned by digest and installed with a new manifest kind `oci-image` (the image's
`/acestream` and `/system` are copied from a build stage; ARMv7 keeps the
official APK). That change is merged into this branch and is the ARM answer;
this work adds no engine task.

Two consequences for this design. First, the user-facing docs Plan 4 writes must
match what was actually verified: `docs/ops/acestream-arm-engine.md` records
"API/startup verified on ARM64", not playback, so the ARM section states that
the web player, remote players and the tuner are expected to work on arm64 with
the 3.2.17 distribution but that live playback has not been confirmed on
hardware, and it keeps the 3.1.80/ARMv7 premium caveat (ARMv7 still runs the
official premium-gated APK). Second, the engine client's refusal mapping must
cover `mod_detected` alongside the premium message so any engine that still
refuses surfaces "The AceStream engine refused to start the stream …" rather
than a timeout. Follow-up (not in scope, needs hardware): a real playback test
of the 3.2.17 arm64 image against a public content id, which would let the ARM
support level and this documentation be tightened.

**Post-spec target update (2026-09-04).** After this design was implemented,
`origin/develop` commit `77c7ad3` moved `linux/arm/v7` from the official 3.1.80
APK to the matching platform variant of the digest-pinned
`jopsis/acestream:v3.2.17-fix` OCI image. That target-branch decision supersedes
only the ARMv7 packaging and premium-gate statements above; the research about
official engines and the prohibition on false app identities still stand.
ARMv7 now builds and installs the community distribution but remains
experimental because it has not been runtime-tested on real 32-bit hardware.

## 5. Web player

### 5.1 Backend (`app/services/player_service.py`, `/api/v1/player`)

- `PlayerSession`: `id` (uuid4 hex), `content_id`, `state`
  (`starting|ready|error|stopped`), `engine_session`, `ffmpeg` process,
  `dir` (`{PLAYER_HLS_DIR}/{id}`), `viewers` (informational count),
  `created_at`, `last_access`, `codecs` (`video`, `audio` parsed from ffmpeg's
  `Stream #0:…` stderr lines), `error` (`engine_unavailable|engine_refused|
  engine_stalled|ffmpeg_missing|ffmpeg_failed`, plus message), `stats`
  (last engine `stat`).
- Sessions are shared per `content_id`: `POST /api/v1/player/sessions
  {content_id}` returns the existing non-stopped session (viewers+1) or
  creates one. `PLAYER_MAX_SESSIONS` caps distinct channels; the next create
  raises `APIError("PLAYER_LIMIT_REACHED", …, 409, context={"limit": N,
  "active": n})`. `content_id` is validated as 40 hex.
- ffmpeg command (per session):
  `ffmpeg -nostdin -hide_banner -loglevel info -nostats -rw_timeout 20000000
  -fflags +genpts+discardcorrupt -i <playback_url> -map 0:v:0 -map 0:a:0?
  -c:v copy -c:a aac -b:a 160k -ac 2 -f hls -hls_time 2 -hls_list_size 6
  -hls_delete_threshold 2 -hls_flags delete_segments+independent_segments+
  omit_endlist+temp_file -hls_segment_type mpegts -hls_segment_filename
  <dir>/seg%05d.ts <dir>/index.m3u8`. `-loglevel info` is required for the
  `Stream #0:` dump; `-nostats` removes `\r` progress spam; `-rw_timeout`
  (µs) makes a starved read fail after 20 s so a peerless engine cannot hang
  ffmpeg forever. ffmpeg follows the engine's 302 itself. Audio is always
  re-encoded to AAC (cheap, one code path). Video is copied; a non-decodable
  video codec is reported through `codecs.video` so the UI can explain before
  hls.js fails.
- Spawn: `await asyncio.create_subprocess_exec(...)` on the event-loop thread
  (the sync endpoint hops via `asyncio.run_coroutine_threadsafe(...).result()`),
  `start_new_session=True`, and on Linux `preexec_fn` setting
  `PR_SET_PDEATHSIG=SIGTERM` through `ctypes` (no-op elsewhere; PDEATHSIG
  binds to the forking thread, hence the loop-thread spawn) so a crashed
  backend cannot leave ffmpeg holding an engine session. `{dir}/ffmpeg.pid`
  is written right after spawn. stderr is drained continuously by a reader
  task (`readline()`, falling back to `read(4096)` on overrun; parses codec
  lines; keeps the last 20 lines in a ring buffer) so the pipe can never
  fill.
- **State transitions.** (a) `starting` on creation once `EngineClient.start`
  succeeded and ffmpeg spawned; an engine failure creates the session directly
  in `error` (`engine_unavailable`/`engine_refused`), `ffmpeg_missing`
  likewise. (b) `starting -> ready` the first time `hls_ready` is observed
  (`index.m3u8` exists with ≥ 2 segment lines); evaluated wherever
  `hls_ready` is computed (status GET and the 5 s service loop); one-way.
  (c) `starting|ready -> error(ffmpeg_failed)` when the stderr reader hits EOF
  and `proc.wait()` returns while the session is not `stopped`; the last
  stderr lines become the message. (d) `-> stopped` only by teardown (reaper
  or shutdown), set before the kill; after `rmtree` the session leaves the
  registry, later GETs answer 404 and the SPA treats a 404 status as "session
  ended". (e) `starting -> error(engine_stalled)` when `now - created_at >
  PLAYER_START_TIMEOUT_SECONDS` and `hls_ready` is still false; message from
  the last engine `stat` (e.g. "no peers (status=prebuf)").
- `GET /sessions/{id}` -> `PlayerSessionStatus` DTO (state, codecs, stats,
  error, viewers, playlist_url, hls_ready). Touches `last_access` (it is the
  heartbeat while a player is paused or still starting).
- `GET /sessions/{id}/index.m3u8`: reads the playlist (atomic thanks to
  `temp_file`) and returns a `Response(media_type="application/vnd.apple.
  mpegurl", headers={"Cache-Control": "no-store"})`. When the request
  authenticated via `?token=`, every non-empty line not starting with `#`
  gets `?` + `urlencode({"token": value})` appended; header-authenticated
  requests get the file verbatim. `GET /sessions/{id}/{segment}` serves
  `FileResponse` (`video/mp2t`, `no-store`) for names matching
  `^seg\d{5}\.ts$` only. Both touch `last_access` and answer 404 until the
  file exists.
- `DELETE /sessions/{id}` -> viewers-1 (never below 0), 204; idempotent.
- `GET /sessions` -> list of `PlayerSessionStatus` (Integrations page);
  `GET /capabilities` (4.5).
- Reaper and service loop: one `asyncio` task started in `lifespan()`
  (`player_service.start()` / `stop()`), every 5 s. Each tick wraps its body
  in `try/except Exception: logger.exception(...)` and continues; per-session
  work is guarded individually; `start()` attaches a done-callback that logs
  and restarts the task on unexpected exit. Per tick: poll `stat_url` for
  `starting` and `ready` sessions (a failed stat logs a warning and leaves
  `stats`/state unchanged); evaluate `hls_ready` and transition (e); tear
  down a session when `now - last_access > 20 s` (regardless of `viewers`,
  so a killed tab cannot leak it), or `viewers == 0` for > 5 s (fast path),
  or `state == error` for > 60 s. Teardown: set `stopped`, SIGTERM the
  process group if still running, SIGKILL after 5 s (`ProcessLookupError`
  suppressed), engine `stop` (errors logged), `shutil.rmtree(dir,
  ignore_errors=True)`. `stop()` (shutdown) SIGKILLs immediately so trap
  latency + 3 s graceful + teardown fits Docker's grace period, then stops
  engine sessions and removes dirs. On `start()`, for each 32-hex session
  dir under `PLAYER_HLS_DIR`: read `ffmpeg.pid`, verify the process is ours
  (`/proc/<pid>/cmdline` on Linux, `ps -o args=` elsewhere, must contain the
  session dir path), SIGKILL it, wait ≤ 1 s, then `rmtree`; never touch the
  directory itself or foreign entries.
- `PLAYER_HLS_DIR` default `/tmp/acestream-player` (documented option:
  `/dev/shm/acestream-player` with `shm_size`).
- Handlers that touch the DB (`POST /sessions` reads `ace_engine_url`) are
  sync `def` endpoints (threadpool); HLS file handlers are async and do no DB
  work.

### 5.2 Frontend

- Dependency `hls.js@1.7.x`, Vite `manualChunks` rule `player-vendor` for
  `/node_modules/hls.js/`; `viteConfig.test.ts` updated.
- `services/playerService.ts`, `hooks/usePlayer.ts` (`useStartPlayerSession`
  mutation; `usePlayerSessionStatus(id)` query with `refetchInterval` 2 s
  while `starting`, 10 s while `ready` (heartbeat), stopped on `error`/404;
  `usePlayerCapabilities`), `components/player/StreamPlayerDialog.tsx`:
  - MUI `Dialog` (full-screen under 900 px) with `<video>` (controls,
    autoplay, muted-autoplay fallback), a status strip (Starting: peers /
    speed, Playing, or an error `Alert`), and actions: "Play on…"
    (`PlayOnMenu`, section 6), "Copy stream link" (the absolute
    `/tuner/stream/<id>.ts` URL from the public base), Close.
  - Uses `Hls.isSupported()` -> hls.js (`enableWorker`, `liveSyncDurationCount
    3`, `xhrSetup` adds `X-Api-Token`), else native `<video src>` with
    `?token=` appended (the backend then propagates it onto segment URIs).
  - Error copy: `ffmpeg_missing` "This server can't prepare streams for the
    browser. Open the channel in VLC instead."; `codecs.video` in
    `{mpeg2video}` (or hls.js `BUFFER_INCOMPATIBLE_CODECS_ERROR`) "Your browser
    can't play this channel's video format (MPEG-2). Send it to VLC or Kodi.";
    `engine_refused` shows the engine's message; `engine_stalled` "No one is
    sharing this channel right now. Try again later or pick another stream."
    with Retry; `ffmpeg_failed` "The stream stopped unexpectedly" with Retry;
    the create mutation rejecting with `ApiError.code === 'PLAYER_LIMIT_
    REACHED'` -> "Too many channels are playing at once (limit N)" with N
    from `error.context.limit`.
  - Release: leaving the dialog and `pagehide` both call
    `fetch(`${apiBase}/player/sessions/${id}${token ? `?token=…` : ''}`,
    { method: 'DELETE', keepalive: true })` behind an idempotent guard
    (`navigator.sendBeacon` is POST-only and cannot carry the token, so it is
    not used). A missed release is harmless: the idle rule reaps the session.
- Entry points, all opening the dialog with a `content_id`:
  - Acestream Channels rows: `ChannelRowActions` visible icons become Play
    (`PlayArrowRounded`, `aria-label="play channel ${name}"`) and Check
    status; "Open/Link TV channel" moves into the row menu as items labelled
    `Link to a TV channel` (unlinked) / `Open TV channel: ${linkedName}`
    (linked), next to a "Play on…" submenu. `ChannelActionHandlers` gains
    `onPlay` and `onPlayOn`. Existing Jest assertions on the visible
    `go to tv channel …` / `assign tv channel to …` buttons
    (`ChannelTable.test.tsx`, `ChannelCardList.test.tsx`) become `menuitem`
    assertions inside the opened `More actions for …` menu.
  - TV Channel detail: Play per stream (secondary action group) and "Play
    best stream" in the header (first entry of `acestream_channels`).
  - TV Channels table/cards: Play (best stream) next to Open.
  - Search results: Play by result id.
- **Stream ranking.** `PlaylistService._score_acestream` moves to
  `app/services/stream_ranking.py` (`score_acestream(stream)`, duck-typed;
  `sort_streams_curated(streams)` = `sorted(streams, key=lambda s:
  (-score_acestream(s), s.id))`); `_score_acestream` stays as a thin alias.
  `TVChannelResponse.acestream_channels` gets a `@field_validator(mode=
  "after")` returning `sort_streams_curated(value)` (covers list, detail,
  favorite/create/update responses) and `GET /{id}/acestreams` returns the
  sorted copy, so "best stream" is `acestream_channels[0]` everywhere
  (frontend, tuner lineup, playlist).

## 6. Remote players (VLC, Kodi)

### 6.1 Data and API

Table `remote_players` (Alembic revision after `20260824_1200`): `id`,
`name` (unique), `kind` (`vlc|kodi`), `host`, `port` (default 8080),
`username` (Kodi, default `kodi`; empty for VLC), `password`, `base_url_id`
(nullable FK to `base_urls`; null = backend relay URL), `created_at`,
`updated_at`. Passwords are stored as-is (SQLite, single-user app; documented
in the wiki), never logged, and never returned by the API (`has_password:
bool` instead). `host` is validated as a hostname or IP without scheme,
userinfo or path and must pass `validate_lan_target(host, resolve=False)`
(private/loopback allowed regardless of `ALLOW_PRIVATE_SCRAPE_TARGETS`;
metadata/link-local/multicast/unspecified/reserved rejected with 422
`REMOTE_PLAYER_HOST_FORBIDDEN`).

`/api/v1/remote-players` (sync `def` handlers; drivers use `httpx.Client`):

- `GET ""` list, `POST ""` 201 (409 duplicate name), `PATCH /{id}`,
  `DELETE /{id}` 204 — the `base_urls.py` CRUD template.
- `POST /test` body `RemotePlayerTestRequest` (the `RemotePlayerCreate`
  fields with `password` optional, plus optional `id`) -> `RemotePlayerProbe
  {reachable, authenticated, version, message, hint, tuner_access:
  {addresses, allowed}}`; performs no writes. Secret rule: use the body
  password when non-empty; else, when `id` is given, the stored password of
  that row (host/port/kind still from the body); else probe without
  credentials. `tuner_access` resolves the host with `getaddrinfo` and checks
  every address against `TUNER_ALLOWED_NETWORKS` (a heuristic for multi-homed
  hosts) so the UI can warn "This player at <ip> is outside
  TUNER_ALLOWED_NETWORKS and will get 403 from the stream URL: add <cidr> or
  choose the Acexy/engine stream link format". `POST /{id}/test` is the
  shortcut using stored values. Probe outcomes: unreachable / VLC 403 "web
  interface has no password" / 401 "wrong password" / Kodi 401 / ok
  (+version).
- `GET /{id}/status` -> `RemotePlayerStatus {state: playing|paused|stopped|
  unreachable|auth_error, title, position_s, length_s, volume_pct, message}`.
- `POST /{id}/play {content_id}` -> resolves the stream URL (6.3), clears the
  playlist, `in_play` (VLC) / `Player.Open` (Kodi); 202 with the URL used.
- `POST /{id}/command {command: pause|resume|stop|volume, value?}`
  (`volume` 0-200 percent). Seek is intentionally absent (live streams;
  VLC and Kodi disagree on semantics).
- `POST /scan {cidr, ports?: [8080], timeout_ms?: 400}` (async handler):
  `cidr` is parsed with `ipaddress.ip_network(strict=False)`, must be a
  subnet of `PRIVATE_SCAN_NETWORKS = (10.0.0.0/8, 100.64.0.0/10,
  172.16.0.0/12, 192.168.0.0/16, fc00::/7)` and have `num_addresses <= 1024`
  (422 `SCAN_CIDR_NOT_PRIVATE` / `SCAN_TOO_LARGE`); `ports` 1-65535, at most
  8. Asyncio TCP connect-scan (≤ 128 concurrent, 30 s budget) followed by an
  HTTP probe per open port classifying `vlc` (`/requests/status.json` ->
  401/403/200 with VLC's JSON/HTML), `kodi` (`/jsonrpc` -> 401 or JSON-RPC
  body) or `unknown`. Returns `ScanResult {hosts: [{host, port, kind, hint}],
  scanned, duration_ms}`. `GET /scan/default` derives `<client>/24` from the
  corrected client IP when it is RFC1918 and not a Docker gateway
  (172.16/12 `.1` gateways, 192.168.65/24), else returns an empty CIDR with a
  hint to type the network.


**Amendment (2026-09-04, from the Plan 3 review).** `POST /{id}/play` returns
`{url, warnings}`: the same public-address and tuner-allowlist warnings the probe
computes are attached to the play response, because a player that cannot fetch
the link would otherwise get a silent 202. The UI shows them next to the
"Sent X to Y" confirmation.
### 6.2 Drivers (`app/services/remote_players/`)

`PlayerDriver` protocol: `probe()`, `status()`, `play(url, title)`,
`pause()`, `resume()`, `stop()`, `set_volume(pct)`. Both drivers take an
injectable `httpx.Client` (tests use `httpx.MockTransport`) constructed as
in 4.4, call `validate_lan_target(host, resolve=True)` before every request,
and build queries with httpx `params=` so `input=` and literal `%` are
encoded correctly.

- `VlcDriver`: Basic auth `("", password)`; `GET /requests/status.json` with
  `command=…`; `play` = `pl_empty` then `in_play&input=<url>`; pause =
  `pl_forcepause`, resume = `pl_forceresume`, stop = `pl_stop`; volume =
  `volume&val=<int>` on VLC's raw scale, `val = clamp(round(pct * 256 / 100),
  0, 512)`. Status from `status.json`: `state`, `time`, `length`,
  `volume_pct = round(volume * 100 / 256)` (may exceed 100), title from
  `information.category.meta.title` or `filename`. A `text/html` or non-JSON
  body is VLC's "Error loading" page and is raised as
  `PlayerCommandError(<pre> text)`, never treated as success.
- `KodiDriver`: `POST /jsonrpc` JSON-RPC 2.0 with Basic auth; `play` =
  `Player.Open {item:{file:url}}`; pause/resume = `Player.PlayPause
  {playerid, play: false|true}`; stop = `Player.Stop`; volume =
  `Application.SetVolume` (0-100, values above 100 clamped); status =
  `Player.GetActivePlayers` + `Player.GetProperties (time,totaltime,speed)`
  + `Player.GetItem (title,file)` + `Application.GetProperties (volume)`.
- Errors and HTTP mapping (rule: 401 stays reserved for the API token):
  `PlayerUnreachable` (incl. `BlockedURLError`) -> 502
  `REMOTE_PLAYER_UNREACHABLE`; `PlayerAuthError(kind)` -> 502
  `REMOTE_PLAYER_AUTH` with `context={"kind": "no_password"|"wrong_password"}`;
  `PlayerCommandError(message)` -> 400 `REMOTE_PLAYER_COMMAND_FAILED`.
  The UI shows the guided password message when `error.code ===
  'REMOTE_PLAYER_AUTH'` and never triggers the API-token notice.

### 6.3 Stream URL handed to a player

`resolve_player_stream_url(content_id, player, request)`:
`base_url_id` set -> `PlaylistService._stream_link(pattern, content_id,
pid=None)` (addpid off); else `{public_base_url}/tuner/stream/{content_id}.ts`.
The relay URL is the default because it works for every flavor and needs only
port 8000, at the cost of the backend carrying the bytes. The tuner allowlist
applies to the player's address (see `tuner_access` in 6.1).

### 6.4 UI (Integrations page, "Remote players" section)

- Card list of players: name, kind chip, host:port, live status line (polled
  every 5 s while the page is open), two visible actions (play/pause toggle,
  stop) plus a volume slider; "Send channel…", Edit, Test, Delete
  (`danger`) in a `RowActionsMenu` ("More actions for <name>"); `useConfirm`
  on delete.
- "Add player" / "Edit player" dialog: name, kind (VLC/Kodi), host, port,
  password (+ username for Kodi), stream link format select (default "Server
  relay (recommended)"), inline "Test connection" calling `POST /test` (with
  `id` when editing and the password field left empty) showing:
  - VLC 403: "VLC's web interface has no password. In VLC: Tools >
    Preferences > All > Interface > Main interfaces > Web, then Lua > Lua HTTP
    > Password."
  - VLC/Kodi 401: "Check the password (VLC: Lua HTTP password; Kodi: Settings >
    Services > Control)."
  - `tuner_access.allowed === false`: the allowlist warning from 6.1.
- "Find players" dialog: CIDR field prefilled from `scan/default`, progress,
  results with one-click "Add" (opens the Add dialog prefilled).
- `components/player/ChannelPickerDialog.tsx` (`{open, player, onClose}`):
  `ToggleButtonGroup` "TV channels | Streams" over a MUI `Autocomplete` with
  300 ms debounced server search. TV channels mode uses
  `useTVChannelCatalog({search})`, options filtered to active channels with
  streams, secondary text "Best stream: <acestream_channels[0].name> ·
  Online/Offline", `content_id = acestream_channels[0].id`. Streams mode uses
  `channelService.getChannels({search, is_active: true, page_size: 50})`,
  `content_id = id`. Confirm "Send to <player>" calls `POST /{id}/play`.
- `PlayOnMenu` component (used by the player dialog and the row menu "Play
  on…"): lists players, sends `POST /{id}/play`, snackbar feedback; empty
  state links to the Integrations page.

## 7. Tuner (HDHomeRun emulation) and Jellyfin/Plex

### 7.1 Tuner routes (`/tuner`, token-free, allowlist-gated)

`app/api/endpoints/tuner.py` exports two routers. `hdhr_router =
APIRouter(prefix="/tuner", dependencies=[Depends(require_tuner_network)])`
carries the tuner-client-facing routes below plus a catch-all
`/tuner/{path:path}` JSON 404, and is registered on `app` in `main.py`
without `require_api_token`; the SPA fallback skips `/tuner`. `router =
APIRouter()` carries `GET/PUT /settings` and `GET /status` only and is
included in `api.py` as `api_router.include_router(tuner.router,
prefix="/tuner", tags=["tuner"])`. DB-touching handlers are sync `def`.

- `GET /tuner/discover.json`: `FriendlyName` (setting, default "AceStream
  Scraper"), `Manufacturer: Silicondust`, `ModelNumber: HDTC-2US`,
  `FirmwareName: hdhomeruntc_atsc`, `FirmwareVersion: 20240101`,
  `DeviceID` (setting `tuner_device_id`, generated once: 8 uppercase hex with
  a valid libhdhomerun checksum), `DeviceAuth: ""`, `BaseURL:
  {public}/tuner`, `LineupURL: {public}/tuner/lineup.json`, `TunerCount`
  (setting, default 4).
- `GET /tuner/lineup.json`: `[{GuideNumber, GuideName, URL}]` from
  `TunerService.build_lineup()`; `GET /tuner/lineup_status.json`:
  `{ScanInProgress:0, ScanPossible:0, Source:"Cable", SourceList:["Cable"]}`;
  `POST /tuner/lineup.post` -> 200 empty; `GET /tuner/device.xml`: UPnP root
  description (`urn:schemas-upnp-org:device:MediaServer:1`, UDN
  `uuid:<DeviceID>`, `URLBase`).
- `GET|HEAD /tuner/stream/{content_id}.ts` -> `relay_engine_stream`; unknown
  query params (`transcode`, `duration`) ignored; `content_id` validated as
  40 hex; concurrent relays capped at `TunerCount` (503 `TUNER_BUSY` beyond).
- `GET /tuner/guide.xml`: numeric-id XMLTV for the lineup channels
  (`<channel id="{GuideNumber}">` with three `<display-name>`s and `<icon>`,
  programmes keyed by `GuideNumber`). `EPGService` is extended with default
  behaviour unchanged: `generate_epg_xml(..., tv_channel_ids=None)` (when
  given, ANDs `TVChannel.id.in_(ids)` with the existing filters) and three
  public helpers it calls itself and `TunerService.build_guide_xml` reuses:
  `epg_channel_lookup(tv_channels) -> dict[(epg_source_id, epg_id),
  EPGChannel]`, `programs_in_window(epg_channel_ids, days_back=1,
  days_forward=7) -> dict[epg_channel_id, list[EPGProgram]]`,
  `programme_xml_lines(program, channel_id) -> list[str]`. The existing
  `/api/v1/epg/xml` endpoint is not widened and its output stays
  byte-for-byte identical (pinned by existing tests). Served uncompressed.
- `GET /tuner/playlist.m3u`: curated M3U for the lineup channels with
  `tvg-id="{epg_id}"`, `tvg-chno="{GuideNumber}"`, `tvg-name`, `tvg-logo`,
  `group-title`, stream URL `{public}/tuner/stream/{content_id}.ts` (no pid,
  no query string). `GET /tuner/epg.xml` -> `generate_epg_xml(tv_channel_ids=
  [lineup ids])`. These two back the Jellyfin M3U mode.

### 7.2 Lineup rules (`TunerService`)

- Source: `TVChannel.is_active` with ≥1 `AcestreamChannel`, ordered like the
  curated playlist. Best stream = `sort_streams_curated(...)[0]`. Channels
  whose every stream is known offline are still listed (tune failures are
  clearer than vanishing channels) unless `tuner_only_online` (default off).
- `GuideNumber` allocation, deterministic and collision-free in one pass over
  curated order: `explicit = {channel_number of lineup channels where set}`;
  `fallback_base = max(1000, max(explicit, default=0) + 1)`; `GuideNumber =
  channel_number` when set and not already claimed by an earlier channel,
  else `fallback_base + tv_channel.id` (ids are unique and the base exceeds
  every explicit number, so no residual duplicates). Channels that lost their
  explicit number are reported as `renumbered: [{tv_channel_id, name,
  requested_number, assigned_number}]`. Caveat recorded in the wiki: a new
  explicit number ≥ the current base shifts every fallback number; the
  lineup fingerprint changes and the sync job pushes a refresh (Jellyfin
  re-identifies `hdhr_<n>`, Plex needs its usual rescan).
- Cap `tuner_max_channels` (default 450, validated 1..1000); overflow is
  dropped in order and reported; the UI warns "Plex stops saving channel
  maps at roughly 450-480 channels (it depends on channel number and name
  length). N channels were left out; disable channels or lower the count."
- `lineup_fingerprint()` = sha256 over `(GuideNumber, GuideName, content_id)`
  tuples. `guide_fingerprint()` = sha256 over sorted `(EPGSource.id,
  EPGSource.last_updated.isoformat() or "")` for enabled sources whose
  `last_error IS NULL` (changes on every scheduled or manual refresh and on
  source add/remove/enable; the in-memory scheduler `last_run` is deliberately
  not used). Both feed the sync job.
- Settings keys (`SettingsRepository`): `tuner_device_id`,
  `tuner_friendly_name`, `tuner_count`, `tuner_max_channels`,
  `tuner_only_online`. `GET/PUT /api/v1/tuner/settings` (`TunerSettings` DTO,
  no `public_base_url` field) expose them; `GET /api/v1/tuner/status`
  (`TunerStatus`) returns channel count, `renumbered`, overflow, the resolved
  URLs to paste (read-only), `ffmpeg_available`, `allowed_networks`,
  `client_ip`, `peer`, `client_allowed`, `client_source`, `warnings`
  (`TUNER_ALLOWLIST_INEFFECTIVE`), and `recent_denials: [{client_ip, path,
  at}]`.

### 7.3 Media servers (`/api/v1/media-servers`)

Table `media_servers`: `id`, `kind` (`jellyfin|plex`), `name`, `base_url`,
`api_key` (Jellyfin API key or Plex owner token; write-only, `has_api_key` in
responses, never logged), `tuner_mode` (`hdhomerun|m3u`, Jellyfin only),
`enabled`, `auto_refresh` (default true), `tuner_host_id`,
`listing_provider_id`, `dvr_key` (Plex), `last_lineup_fingerprint` (String
64), `last_guide_fingerprint` (String 64), `last_sync_at`,
`last_sync_status` (`ok|error|never|manual`), `last_error`,
`server_version`, timestamps. `base_url` is validated as http(s) with host,
optional port/path, no userinfo, and its host must pass
`validate_lan_target(resolve=False)` (422 `MEDIA_SERVER_URL_FORBIDDEN`).

Endpoints (sync `def` handlers, `httpx.Client` clients as in 4.4): CRUD
(`GET ""`, `POST ""`, `PATCH /{id}`, `DELETE /{id}` — for a connected
Jellyfin server `DELETE` first runs `disconnect()` best-effort, errors
logged), `POST /test` (body `MediaServerTestRequest`, same secret rule as
remote players, response includes `tuner_access`), `POST /{id}/test`,
`POST /{id}/connect`, `POST /{id}/refresh` -> `MediaServerRefreshResponse
{status: ok|error|manual, message, last_sync_at}`, `POST /{id}/disconnect`,
`GET /{id}/status`. Error mapping: `MEDIA_SERVER_UNREACHABLE`,
`MEDIA_SERVER_AUTH`, `MEDIA_SERVER_ERROR` -> 502 with the upstream status in
`context`; `MEDIA_SERVER_NOT_CONNECTED` -> 409.

Jellyfin client (`media_servers/jellyfin.py`, injectable httpx client):

- Header `Authorization: MediaBrowser Token="<key>", Client="acestream-scraper",
  Device="acestream-scraper", DeviceId="<tuner_device_id>", Version="<app>"`.
- `test()`: `GET /System/Info/Public` (version) then `GET /System/
  Configuration/livetv` (proves the key is an admin key).
- `connect()`: read `GET /System/Configuration/livetv`; in `hdhomerun` mode
  upsert a `TunerHostInfo {Type:"hdhomerun", Url:"{public}/tuner",
  FriendlyName, TunerCount:0, AllowHWTranscoding:false, AllowStreamSharing:
  true, ImportFavoritesOnly:false}` (`AllowHWTranscoding:false` because
  Jellyfin treats `HDTC` models as transcode-capable and would otherwise
  advertise six fake profiles and append `?transcode=`; a tuner the user
  added by hand is corrected on the next connect since the upsert resends the
  whole object) — reuse the stored `Id`, else match by `Url`, else create —
  and a `ListingsProviderInfo {Type:"xmltv", Path:"{public}/tuner/guide.xml",
  EnableAllTuners:false, EnabledTuners:[tunerId]}`; in `m3u` mode the tuner
  `Url` is `{public}/tuner/playlist.m3u` and the provider path
  `{public}/tuner/epg.xml`. PascalCase bodies. Persist both ids. Jellyfin
  validates the tuner by fetching it, so a wrong public URL surfaces here with
  the hint "Jellyfin could not download {url}; check the public address".
- `refresh()`: `GET /ScheduledTasks`, `Key == "RefreshGuide"`; `ok` when
  triggered (`POST /ScheduledTasks/Running/{Id}`) or already running, `error`
  otherwise; retries once after 2 s on 503.
- `disconnect()`: `DELETE /LiveTv/ListingProviders?id=`, `DELETE /LiveTv/
  TunerHosts?id=`, clear stored ids.
- `status()`: tuner/provider presence, RefreshGuide `State` and
  `LastExecutionResult`, `GET /LiveTv/Channels?addCurrentProgram=false&
  enableImages=false&limit=1` for `TotalRecordCount`.
- Version gate: warn below 10.9; note below 10.11.7 for the M3U mode.

Plex client (`media_servers/plex.py`):

- `connect()` is instructions-only: the status DTO carries the exact steps and
  values (tuner address `{public host}:{port}/tuner`, guide URL
  `{public}/tuner/guide.xml`, the Plex Pass note, the "rescan after channel
  changes" note). With a token: `GET /livetv/dvrs` (header `X-Plex-Token`,
  `Accept: application/json`) finds the DVR whose device `uri` matches our
  `BaseURL` and stores `dvr_key`.
- `refresh()`: `POST /livetv/dvrs/{dvr_key}/reloadGuide` -> `ok`; without a
  token or `dvr_key` -> `manual` ("the lineup/guide changed but Plex must
  rescan the guide in its UI").
- `disconnect()`: forget `dvr_key` only (never deletes in Plex).

Sync job: `media_server_sync` interval task (10 min, registered in
`lifespan()`, body in `app/tasks/media_server_sync_task.py`, runs in the
scheduler thread with sync clients): for each enabled server with
`auto_refresh`, compare the current lineup/guide fingerprints with the stored
ones; when either changed and `last_sync_at` is older than
`Settings.MEDIA_SERVER_MIN_REFRESH_MINUTES` (30; `0` disables the debounce),
call `refresh()`; store fingerprints and the result. A `manual` result stores
the fingerprints and `last_sync_status='manual'` but leaves `last_sync_at`
untouched (real refreshes only), so the job does not repeat the no-op and the
card can flag "channels changed since your last Plex scan". Errors are
recorded per server, never raised. Manual `POST /{id}/refresh` bypasses the
debounce.

### 7.4 UI (Integrations page, "Media servers" section)

- Cards per server: kind chip, name, base URL, connection chip (Connected /
  Not connected / Error with message), sync chip (`ok` "Guide up to date",
  `error` "Refresh failed" + `last_error`, `never` "Not synced yet",
  `manual` "Rescan the guide in Plex", warning styling), last sync relative
  time, channel count (Jellyfin); two visible actions, "Refresh now" and
  "Connect"/"Disconnect" (Plex "Refresh now" disabled with a tooltip when no
  token or `dvr_key`); Edit, "Test connection" and Delete (`danger`) in a
  `RowActionsMenu` ("More actions for <name>"). `useConfirm()` on Delete and
  on Jellyfin Disconnect (title "Disconnect <name>?", body "This removes the
  AceStream tuner and its guide provider from Jellyfin. Jellyfin will re-run
  Refresh Guide and drop those channels."); Delete's body says the same when
  the server is connected. Plex Disconnect does not confirm.
- "Add media server" / "Edit" dialog: kind, name, base URL, API key/token,
  and for Jellyfin a tuner mode radio (HDHomeRun recommended; M3U with the
  identity caveat text), inline "Test connection" via `POST /test` (shows the
  `tuner_access` warning without the link-format alternative).
- Plex card body shows the paste-ready values with copy buttons and the
  numbered steps. Sync errors that mention the public address link to the
  Public address section (`#public-address`).

## 8. Cross-cutting UI

- Nav: `{ text: 'Integrations', path: '/integrations', icon:
  <HubRounded />, section: 'System' }` above Settings. `routes.test.tsx` and
  e2e `NavLabel`/`NAV_ROUTES` updated.
- Page skeleton per checklist: `PageHeader` ("Integrations", subtitle
  "Play channels in the browser, on players in your network, and in Jellyfin
  or Plex."), `StatusLine` (Public address with tone `warning` when any
  warning is present, Players, Media servers, Active streams), then
  `ContentSection`s:
  - **Public address** (`id="public-address"`): resolved URL with its source
    (Setting / Proxy headers / Request), a warning `Alert` for `localhost`,
    `docker-internal`, `unset` or `proxied` explaining that Jellyfin/Plex/VLC
    may not reach that address (the `proxied` text points at the reverse-proxy
    note about `/tuner/` and proxy auth), a `<form>` TextField + Save
    (disabled while unchanged) writing `PUT /api/v1/config/public_base_url`
    through `configService.setPublicBaseUrl`; Save invalidates the public-url
    and tuner-status queries so pasted values refresh. When
    `TunerStatus.warnings` contains `TUNER_ALLOWLIST_INEFFECTIVE`, an Alert:
    "This host hides real client addresses (Docker Desktop, rootless Docker,
    or IPv6 through docker-proxy); the private-network allowlist cannot tell
    your LAN from the internet. Publish the port IPv4-only, put a reverse
    proxy with allow/deny in front, or keep port 8000 off the internet." When
    `recent_denials` is non-empty: "Requests from <ip> were denied <n> min
    ago; add <cidr> to TUNER_ALLOWED_NETWORKS".
  - **Web player**: ffmpeg availability, active sessions and relays (from
    `GET /api/v1/player/sessions` and the relay registry), limit.
  - **Remote players** (6.4) and **Media servers** (7.4).
- All copy plain-language; status uses chips with icons, not colour only;
  dark theme via `appTokens`.
- e2e:
  - `e2e/src/pages/channels.ts`: `openAssignTv` uses `rowMenuAction(row,
    name, 'Link to a TV channel')`; new `playChannel(name)` clicking
    `getByRole('button', { name: \`play channel ${name}\` })` and
    `expectLinkedTv(name, tvName)` (opens `More actions for ${name}`, asserts
    the `Open TV channel: ${tvName}` menuitem, presses Escape).
    `07-tv-channels.spec.ts` uses `expectLinkedTv` instead of the visible
    button assertion; `05-channels.spec.ts` is unaffected.
  - `e2e/tests/10-integrations.spec.ts` with page object
    `e2e/src/pages/integrations.ts` (`playerCard(name)`/`serverCard(name)`,
    menus through `rowMenuAction`, `confirmDialog`): page loads; add a fake
    VLC player pointing at a mock HTTP server started by the spec and
    test-connection reports the guided message; tuner endpoints answer JSON
    and the SPA fallback does not; **deterministic playback** against a stub
    engine started by the spec (Node `http` server implementing
    `/ace/getstream?format=json`, a `playback_url` serving the vendored
    `sample-h264-ac3.m2ts` looped at real time, `stat_url`, `command_url`
    stop) reached via `api.setSetting('ace_engine_url', stubUrl)` with the
    original restored in `finally`, asserting `ready`, `hls_ready` and a
    playing `<video>`, skipped with an annotation when `GET /api/v1/player/
    capabilities` reports no ffmpeg (`e2e/stack/backend-start.sh` exports
    `FFMPEG_BINARY_PATH` when a host ffmpeg exists); and a tolerant
    real-stack-engine test that accepts `ready` or `engine_refused` with the
    message rendered, annotating the outcome (the default e2e stack is the
    ARM engine, which is premium-gated; strict `ready` only when
    `E2E_PLATFORM=linux/amd64` on the `test:docker` target).

## 9. Backend wiring summary

- `main.py`: add `ForwardedHeadersMiddleware` (outermost); include
  `tuner.hdhr_router` on `app` without the token dependency; SPA fallback
  skips `/tuner`; `lifespan()` runs the startup DB upgrade (4.6), starts/stops
  `player_service` and the relay reaper, registers `media_server_sync`;
  `uvicorn.run(..., proxy_headers=False, timeout_graceful_shutdown=3)`.
- `api.py`: include `player`, `remote_players`, `media_servers`, and
  `tuner.router` (prefix `/tuner`, settings/status only).
- `app/utils/logging.py`: the access-log token filter (4.4).
- `app/utils/url_guard.py`: `validate_lan_target` (4.4).
- `app/config/database.py` / `main.initialize_database`: unconditional
  `provision_schema()` with pre-upgrade backup (4.6).
- Models in `models/models.py`: `RemotePlayer`, `MediaServer`. One Alembic
  revision `20260903_1200_add_media_integrations` (idempotent `has_table`);
  parity covered by `test_schema_parity.py`; noted in CLAUDE.md.
- Settings (`SettingsRepository` + `ConfigService` + `config.py` branches):
  `public_base_url` (validated, property default), `tuner_*` keys (validated
  through the tuner settings DTO only). `app/config/settings.py`: the fields
  listed in 4.5.
- `services/epg_service.py`: `tv_channel_ids` parameter and the three
  helpers (7.1); `services/stream_ranking.py`, the `TVChannelResponse`
  validator and the sorted `/acestreams` route (5.2).
- Schemas: `schemas/player.py`, `schemas/remote_players.py`,
  `schemas/tuner.py`, `schemas/media_servers.py`, `schemas/system.py`
  (`PublicUrlResponse`). Unique DTO names.
- OpenAPI dump + `npm run codegen` committed.

## 10. Testing

Backend (`backend/tests/`):

- `test_forwarded_middleware.py` / `test_public_url.py`: with
  `FORWARDED_ALLOW_IPS=testclient` forwarded headers rewrite scheme/host/
  client, `request.state.peer` keeps the raw peer, all-trusted XFF keeps the
  raw peer as client, resolved URL has `source=forwarded`; with `10.0.0.0/8`
  the headers are ignored and the `Host` header wins; setting precedence;
  warnings incl. `proxied`; `*`; allow-list parser (IP, CIDR, `*`, literal,
  malformed). Env-seed cases use `monkeypatch.setenv` +
  `get_settings.cache_clear()` on a fresh `alembic_db_session`.
- `test_config.py`: `public_base_url` valid, path rejected 422, trailing
  slash stripped, empty clears.
- `test_startup_db_init.py`: existing stamped DB upgrades to head with a
  backup; DB at head boots without a backup; failure still aborts.
- `test_engine_client.py` (MockTransport: start/stop/stat, refused, timeout).
- `test_stream_relay.py`: fake engine answering the JSON start, a 302 to
  `/content/…`, N bytes; relayed body equals N bytes; `stop` called exactly
  once after the consumer closes and exactly once when the response task is
  cancelled; 302 to another host or a 500 yields no bytes and one `stop`;
  HEAD performs zero upstream requests; `X-Accel-Buffering` header.
- `test_player_service.py` (fake ffmpeg script writing a playlist and
  segments; transitions ready/ffmpeg_failed before and after ready/stopped;
  `engine_stalled` after the deadline with `PLAYER_START_TIMEOUT_SECONDS=1`,
  then reaped; a fake that floods stderr with `\r` progress keeps the session
  `ready`; argv contains `-nostats` and `-rw_timeout`; reaper reaps
  viewers=1 with stale `last_access`; status poll refreshes `last_access`;
  a failing teardown does not block other sessions and the loop keeps
  ticking; stat poll with the engine unreachable keeps `ready`; startup sweep
  kills a fake ffmpeg whose pidfile+cmdline match and leaves others alone;
  shutdown teardown finishes well under 3 s; limit 409 envelope with
  `context.limit`; codec parsing).
- `test_player_endpoints.py` incl. `test_api_token_auth.py` extensions: with
  `API_TOKEN` set, `index.m3u8?token=T` returns 200 with every URI line
  `segNNNNN.ts?token=T` and `#EXT` lines untouched; each rewritten URI
  fetches 200; the same segment without a token 401; header-authenticated
  playlist is byte-identical to disk; reserved characters URL-encoded;
  `DELETE …?token=` 204; a `uvicorn.access` record with `?token=T` formats
  as `token=[redacted]`.
- `test_stream_ranking.py` (weights) and `test_tv_channels.py::
  test_acestream_channels_returned_in_curated_order` on `/`, `/{id}` and
  `/{id}/acestreams` (online stream first regardless of insertion order).
- `test_url_guard.py`: `validate_lan_target` allows private/loopback with
  `ALLOW_PRIVATE_SCRAPE_TARGETS=false`; rejects metadata (also IPv4-mapped),
  link-local, multicast, unspecified; hostname passes with `resolve=False`
  and fails with `resolve=True` when the fake resolver maps it to metadata.
- `test_remote_players.py` (drivers via MockTransport incl. VLC HTML error
  page and raw volume scale; CRUD; `/test` with/without stored secret and no
  row created; `tuner_access`; 502 `REMOTE_PLAYER_AUTH` for wrong password;
  metadata host 422 and resolved-to-metadata host 502 with zero requests;
  scan classification against a local asyncio server; scan CIDR validation
  (public 422, link-local 422, too large 422, private 200); `scan/default`).
- `test_tuner.py` (discover/lineup/status/device.xml shapes, DeviceID
  checksum, GuideNumber allocation: explicit 1005 + unnumbered id 5 distinct,
  two explicit 7s renumbered, `len(set) == len(lineup)` in every case; cap;
  guide.xml ids and display-names; playlist.m3u attributes; epg.xml
  restricted while `generate_epg_xml()` without ids is byte-identical;
  allowlist 403 incl. IPv4-mapped and 100.64.0.1 allowed by default; spoofed
  XFF from an allowed peer with a `/32` allowlist still 403; denials appear
  in `recent_denials`; `client_source` docker-gateway warning; unknown path
  JSON 404; SPA fallback exclusion; `/tuner/settings` and `/tuner/status`
  not served by `hdhr_router` and 401 on `/api/v1/tuner/*` without token
  while `/tuner/discover.json` is 200; `TUNER_BUSY`).
- `test_media_servers.py` (Jellyfin upsert with `AllowHWTranscoding` false,
  refresh/status/disconnect and test with a recorded fake server; DELETE on
  a connected server disconnects; Plex reloadGuide and the `manual` path with
  `last_sync_at` unchanged; sync job debounce; `/test` secret rule;
  forbidden base_url 422).
- Contract tests `tests/contracts/test_integrations_contracts.py` (request
  DTO validation, exact response key sets and the new error codes for every
  new endpoint) added to the quick profile in `run_v2_test_suite.sh`.

Frontend (`src/__tests__/`): `Integrations.test.tsx` (sections, per-card
menus, Delete and Jellyfin Disconnect open `ConfirmDialog`, Plex Disconnect
does not, public address save, allowlist alerts), `StreamPlayerDialog.test.
tsx` (hls.js mocked; pagehide/close call `fetch` with `method: 'DELETE',
keepalive: true` and the `?token=` suffix; error copy per code incl.
`engine_stalled`), `PlayOnMenu.test.tsx`, `ChannelPickerDialog.test.tsx`,
`ChannelRowActions.test.tsx` (new) plus `ChannelTable` / `ChannelCardList` /
`AcestreamChannelsPage` updated for `onPlay`/`onPlayOn` and the TV link in
the menu, `TVChannelDetail.test.tsx` (Play per stream and "Play best stream"
with `acestream_channels[0].id`), `TVChannelsTable.test.tsx` (desktop and
card mode), `TVChannelsPageResponsive.test.tsx` (mock gains `onPlay`),
`Search.test.tsx` (Play on a result), `Playlist.test.tsx` (mock
`usePublicUrl`; public origin; `token=` only when `apiToken` is stored;
fallback while pending), `playlistService.test.ts` (base override + token),
`playerService.test.ts`, `remotePlayerService.test.ts`,
`mediaServerService.test.ts`, `publicUrlService.test.ts`, a test that a 502
`REMOTE_PLAYER_AUTH` response does not dispatch `API_TOKEN_REQUIRED_EVENT`,
`routes.test.tsx`, `viteConfig.test.ts`.

Docker/CI: `test_ffmpeg_build.py`, `test_ffmpeg_vendor.py`,
`validate_command_builder.sh` tuple and default cross-checks,
`validate_docker_manifest_metadata.py` ffmpeg block,
`test_runtime_integration_guards.py` literals (entrypoint defaults, uvicorn
flags, compose publish and grace period), `docker/vendor/ffmpeg/README.md`,
`docs/ops/multiarch-manifest-updates.md`.

## 11. Documentation

`wiki/Web-Player.md`, `wiki/Remote-Players.md` (VLC and Kodi setup as step
lists; Tailscale/CGNAT note), `wiki/Media-Servers.md` (Jellyfin incl.
HDHomeRun vs M3U, Plex incl. Plex Pass and rescan notes, GuideNumber
renumbering caveat, port/allowlist guidance incl. the docker-proxy/IPv6
caveat), updates to `wiki/Configuration.md` and the README "Canonical
Backend Settings" (`PUBLIC_BASE_URL`, `TUNER_ALLOWED_NETWORKS`,
`PLAYER_HLS_DIR`, `PLAYER_MAX_SESSIONS`, `PLAYER_START_TIMEOUT_SECONDS`,
`FORWARDED_ALLOW_IPS`, `MEDIA_SERVER_MIN_REFRESH_MINUTES`,
`FFMPEG_BINARY_PATH`, `stop_grace_period`; the `ALLOW_PRIVATE_SCRAPE_TARGETS`
row notes it does not affect remote players, media servers or discovery
while the metadata/link-local block still applies), `docs/ops/reverse-proxy.md`
(Jellyfin/Plex fetch `/tuner/*` without credentials so `/tuner/` cannot sit
behind proxy basic auth; nginx `location ^~ /tuner/ { auth_basic off;
proxy_buffering off; … }`, Caddy `handle /tuner/*` before the authed handle,
Traefik `scraper-tuner` router; forwarded headers honoured only from
`FORWARDED_ALLOW_IPS` peers and the proxy must be listed in
`TUNER_ALLOWED_NETWORKS` when that list is narrowed; `--no-proxy-headers`
and `--timeout-graceful-shutdown` must stay in `command:` overrides;
`PUBLIC_BASE_URL` for Host-rewriting or sub-path proxies; HTTPS front with
HTTP relay; a `curl …/tuner/discover.json` verification), `docs/builder/
runtime-options.json`, and CLAUDE.md (new domains, tuner mount, player
lifecycle, forwarded middleware, startup DB upgrade, migration). Known
limitations recorded: ARM engine gate (only if the bump does not clear it; `ACESTREAM_BIND_ALL` default true is documented as a knob, not a limitation), Plex
channel cap and rescan, secrets stored in plain text in the SQLite database,
no seek.

## 12. Decisions and rationale

- ffmpeg always, audio to AAC: one path, works on every flavor/platform,
  fixes AC-3/MP2 which is the common case; cost is a cheap audio encode.
- Backend relay as the default stream URL for players and tuners: only port
  8000 must be reachable, no engine ACL/CORS issues, sessions are owned and
  stopped by the backend. Users can still pick a stream link format (Acexy or
  engine) per remote player.
- HDHomeRun for both Jellyfin and Plex, M3U as an opt-in Jellyfin mode: stable
  identities by default; the M3U path is kept for users who want tvg-id
  linkage and understand the re-keying caveat.
- Token-free tuner routes with a private-network allowlist checked on both
  the raw peer and the forwarded client: tuner clients cannot send tokens;
  the allowlist keeps the routes off the public internet even when port 8000
  is exposed by mistake, and cannot be spoofed from the LAN.
- App-owned proxy trust: one decision on the raw peer address, testable with
  `TestClient`, and `X-Forwarded-Host` support that uvicorn lacks.
- Static minimal ffmpeg in `runtime-base`: +5-10 MB versus hundreds of MB,
  no QEMU apt, no fifth flavor.
- Startup schema upgrade for existing databases: without it no existing
  install would ever see the new tables; a pre-upgrade backup keeps it safe.
- Player button placement: Play and Check status visible; TV link in the
  menu (user decision). Remote player scope: VLC and Kodi (user decision).

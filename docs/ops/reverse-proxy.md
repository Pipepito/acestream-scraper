# Reverse Proxy / HTTPS Deployment

## Scope

This guide covers putting the v2 app (uvicorn on port `8000`) behind a
TLS-terminating reverse proxy for access from outside a trusted network:

- nginx, Caddy, and Traefik configurations
- proxy-level authentication, and the app's optional `API_TOKEN`
- the `/tuner/*` carve-out media servers (Jellyfin, Plex) need
- how the `base_url` setting interacts with a proxied deployment
- which container ports must never be exposed publicly
- WARP interaction with remote access

## Why a proxy is required for remote access

Acestream Scraper's deployment model is a **trusted network**: by default
the app is **open** — anyone who can reach port `8000` can read and change
settings, trigger scrapes, and manage channels through the SPA and
`/api/v1/*`.

Setting the `API_TOKEN` environment variable turns on built-in token
authentication for `/api/v1/*` and the playlist/EPG URLs (sent as
`Authorization: Bearer <token>`, `X-Api-Token: <token>`, or `?token=` for
IPTV players; `/api/v1/health` stays public for health probes). That
protects the data surface, but the token travels in cleartext without TLS —
so exposing the app beyond your LAN still means:

1. Terminate TLS at a reverse proxy.
2. Enforce authentication at the proxy (basic auth below, or an SSO
   gateway such as Authelia/authentik if you already run one).
3. Publish only the app port (`8000`) through the proxy. Keep the engine
   and Acexy ports off the public internet (see the exposure table).

## What the proxy fronts

Everything is served by the one uvicorn process on `:8000`:

- SPA: `/` plus static assets under `/assets` / `/static`
- API: `/api/v1/*`
- Player-facing URLs: `/playlist.m3u`, `/playlists/m3u`,
  `/api/playlists/m3u`, `/api/playlists/epg.xml`,
  `/api/v1/playlists/tv-channels/m3u`, `/api/v1/playlists/all-streams/m3u`
- Tuner routes for Jellyfin/Plex: `/tuner/*` (no API token, gated by client
  address — see the carve-out rule below)

Proxying notes that apply to all three configs:

- **No websockets.** The app is plain request/response HTTP; no `Upgrade`
  header handling is needed.
- **Forwarded headers are trusted by address.** The app reads
  `X-Forwarded-Proto`, `X-Forwarded-Host` and `X-Forwarded-For` itself, but
  only when the connecting peer (the proxy) is inside `FORWARDED_ALLOW_IPS`
  — by default loopback and the private ranges
  (`127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`). Because the app owns
  that trust, uvicorn's own handling stays off: keep `--no-proxy-headers` and
  `--timeout-graceful-shutdown 3` in any compose `command:` override, which is
  what `entrypoint.sh` passes by default.
- **Set `PUBLIC_BASE_URL`** when the proxy rewrites `Host` or mounts the app
  under a sub-path. Without it the app derives its public origin per request,
  and links handed to players and media servers point at the wrong name.
- **`/tuner/` cannot sit behind proxy authentication.** Jellyfin fetches
  `/tuner/discover.json`, `/tuner/lineup.json`, `/tuner/guide.xml` and the
  stream URLs with a bare `HttpClient` that has no credential store, and Plex's
  tuner setup has no credential field at all. A basic-auth challenge on those
  paths shows up as "tuner not found" or an empty channel list, never as a login
  prompt. The routes carry no `API_TOKEN` either — they are gated by client
  address (`TUNER_ALLOWED_NETWORKS`) instead. Every example below therefore
  carves `/tuner/` out of the authenticated location, with buffering off so a
  live stream is not held in the proxy.
- **The proxy must be inside `FORWARDED_ALLOW_IPS`**, or the app ignores its
  `X-Forwarded-*` headers and every tuner request looks like it came from the
  proxy itself. And when `TUNER_ALLOWED_NETWORKS` is narrowed below the private
  defaults, the proxy's own address has to be inside *that* list too: the gate
  checks the raw peer (the proxy) **and** the forwarded client, and refuses
  unless both are allowed.
- **Enable gzip at the proxy.** The app does not compress responses, and
  M3U (`text/plain`) and XMLTV EPG (`application/xml`) payloads compress
  very well.

## nginx

```nginx
server {
    listen 443 ssl;
    server_name scraper.example.com;

    ssl_certificate     /etc/letsencrypt/live/scraper.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scraper.example.com/privkey.pem;

    # The app does not gzip; playlists and EPG XML compress well.
    gzip on;
    gzip_types text/plain application/xml application/json;

    # Proxy-level auth (see "Authentication at the proxy").
    auth_basic "acestream-scraper";
    auth_basic_user_file /etc/nginx/htpasswd-scraper;

    # Jellyfin/Plex reach the tuner without credentials, and streams must not
    # be buffered. ^~ wins over the regex locations, so it must come first.
    location ^~ /tuner/ {
        auth_basic off;
        proxy_buffering off;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

`auth_basic off;` has to be repeated inside the `/tuner/` location: `auth_basic`
is inherited from the `server` block, and only an explicit `off` clears it.

Create the credentials file:

```bash
htpasswd -c /etc/nginx/htpasswd-scraper youruser
```

## Caddy

Caddy provisions TLS certificates automatically and sets the
`X-Forwarded-*` headers on `reverse_proxy` by default:

```caddyfile
scraper.example.com {
    encode gzip

    # Media servers first: this handle matches before the authenticated one.
    handle /tuner/* {
        reverse_proxy 127.0.0.1:8000
    }

    handle {
        basic_auth {
            # Generate the hash with: caddy hash-password
            youruser $2a$14$REPLACE_WITH_CADDY_HASH
        }
        reverse_proxy 127.0.0.1:8000
    }
}
```

(`basic_auth` is the Caddy 2.8+ directive name; older Caddy 2 releases
spell it `basicauth`.)

## Traefik (compose labels)

Add labels to the `app` service in `docker-compose.yml`. With Traefik on
the same Docker network, drop the `ports: "0.0.0.0:8000:8000"` mapping entirely —
Traefik reaches the container directly and nothing listens on the host:

```yaml
services:
  app:
    image: pipepito/acestream-scraper:latest
    volumes:
      - ./config:/app/config
    labels:
      - traefik.enable=true
      - traefik.http.routers.scraper.rule=Host(`scraper.example.com`)
      - traefik.http.routers.scraper.entrypoints=websecure
      - traefik.http.routers.scraper.tls.certresolver=letsencrypt
      - traefik.http.services.scraper.loadbalancer.server.port=8000
      # Basic auth: generate with `htpasswd -nB youruser`,
      # then escape every $ as $$ for compose interpolation.
      - traefik.http.middlewares.scraper-auth.basicauth.users=youruser:$$2y$$05$$REPLACE_WITH_HASH
      - traefik.http.middlewares.scraper-gzip.compress=true
      - traefik.http.routers.scraper.middlewares=scraper-auth,scraper-gzip
      # Tuner routes: no basic auth, higher priority so they win over the
      # Host-only rule above.
      - traefik.http.routers.scraper-tuner.rule=Host(`scraper.example.com`) && PathPrefix(`/tuner/`)
      - traefik.http.routers.scraper-tuner.priority=100
      - traefik.http.routers.scraper-tuner.entrypoints=websecure
      - traefik.http.routers.scraper-tuner.tls.certresolver=letsencrypt
      - traefik.http.routers.scraper-tuner.service=scraper
      - traefik.http.routers.scraper-tuner.middlewares=scraper-gzip
```

Assumes an existing Traefik instance with a `websecure` entrypoint and a
`letsencrypt` certificate resolver.

## Authentication at the proxy

The snippets above each include basic auth. Two operational notes:

**IPTV players and basic auth.** Most players (TiviMate, VLC, Kodi PVR
clients, xmltv grabbers) have no separate credential fields, but they
accept credentials embedded in the URL:

```text
https://youruser:yourpass@scraper.example.com/playlist.m3u
https://youruser:yourpass@scraper.example.com/api/playlists/epg.xml
```

Caveats:

- URL-encode special characters in the password (`@` → `%40`, `:` →
  `%3A`, etc.).
- The credentials are stored in plain text in the player's configuration.
  Use a dedicated user for players, separate from the one you use for the
  admin UI, so it can be rotated independently.
- A few clients ignore userinfo in URLs — test with your player before
  rolling out.

**Combining with the built-in `API_TOKEN`.** Proxy auth and the app's
token are independent layers and stack cleanly. With `API_TOKEN` set,
players that can't do basic auth can instead fetch
`https://scraper.example.com/playlist.m3u?token=<token>` through a
TLS-only proxy vhost with no basic auth on the playlist paths.

**Scope of protection.** Proxy auth protects only what goes through the
proxy. It does nothing for ports published directly on the host — which
is why the engine/Acexy ports must not be published publicly at all.

## The `base_url` interplay

Generated playlists **embed stream URLs**. Each entry is the `base_url`
setting concatenated with the stream id (Settings → `base_url`, default
`acestream://`). The proxy does not rewrite playlist bodies, so two
different addresses are in play:

1. **Playlist/EPG URLs the player fetches** — these go through the proxy:
   `https://scraper.example.com/playlist.m3u`.
2. **Stream URLs inside the playlist** — these point wherever `base_url`
   says, and the player connects to them directly.

`base_url` is not `PUBLIC_BASE_URL`: `base_url` is the stream address
embedded in every playlist entry, while `PUBLIC_BASE_URL` is this app's own
origin — the one used for the playlist and tuner links handed to players and
media servers.

Set `base_url` to an engine/Acexy address that is reachable *from the
player's network position*:

- `acestream://` (default) — the player device runs its own AceStream
  engine and opens the id locally. Works anywhere; no server stream port
  needed.
- `http://192.168.1.10:8080/ace/getstream?id=` — LAN players streaming
  from the server's Acexy.
- `http://192.168.1.10:6878/ace/getstream?id=` — LAN players streaming
  from the server's engine directly (no Acexy PID management).

For remote players, prefer a VPN (WireGuard/Tailscale) and set `base_url`
to the server's VPN address rather than exposing the stream port
publicly. Any playlist route also accepts a per-request override
(`?base_url=...`) if different consumers need different stream addresses
from the same server.

## Per-flavor port exposure

| Port | What listens | Present when | Exposure guidance |
|---|---|---|---|
| `8000` | App: SPA + API + playlists/EPG (`FLASK_PORT`) | all flavors | Via reverse proxy with TLS + auth only. Don't publish the raw port on an untrusted network. |
| `6878` | AceStream engine HTTP API (`ACESTREAM_HTTP_PORT`) | `scraper-acestream*` flavors with `ENABLE_ACESTREAM_ENGINE=true` | **Never publicly.** Unauthenticated: anyone can start streams and burn your bandwidth. LAN/VPN only. |
| `8080` | Acexy: `/ace/getstream` + `/ace/status` (`ACEXY_LISTEN_ADDR`; the healthcheck and the Overview probe follow it, falling back to `ACEXY_STATUS_PORT`) | `*-acexy` flavors with `ENABLE_ACEXY=true` | **Never publicly.** Same unauthenticated stream/status surface. LAN/VPN only. |
| `43110` | ZeroNet UI: bundled node (`ZERONET_UI_PORT`) or optional sidecar | `ENABLE_ZERONET=true` / `--profile zeronet` | **Never publicly.** The ZeroNet UI has no authentication and full node control; the app reaches it internally via `ZERONET_URL`. LAN/VPN only, and only with `ZERONET_UI_HOST` set. |
| `26552` | Bundled ZeroNet node: fileserver/peer port (`ZERONET_FILESERVER_PORT`) | `ENABLE_ZERONET=true` | Safe to publish; improves peer connectivity. Not needed for scraping to work. |
| `4001` | Embedded IPFS daemon: swarm/P2P (tcp+udp, `IPFS_SWARM_PORT`) | `ENABLE_IPFS=true` | Safe to publish; improves peer connectivity. Not needed for scraping to work. |
| `8081` | Embedded IPFS daemon: HTTP gateway (`IPFS_GATEWAY_PORT`) | `ENABLE_IPFS=true` | Internal by default; only publish on trusted networks if you want to browse IPFS through the node. |
| `5001` | Embedded IPFS daemon: RPC API / WebUI (`IPFS_API_PORT`) | `ENABLE_IPFS=true` | **Never publicly.** Unauthenticated full node control; loopback-bound in-container by default. |

Least-exposure rule: the only thing an untrusted network should ever see
is the reverse proxy's `443`. In compose terms, remove or firewall the
direct `ports:` mappings and let the proxy reach the app over the Docker
network; only bind `6878`/`8080` to the host when LAN/VPN players
actually stream from this server, e.g. `- "192.168.1.10:8080:8080"` to
pin the bind to a LAN interface.

## WARP and remote access

- `ENABLE_WARP=true` requires the `NET_ADMIN` and `SYS_ADMIN` container
  capabilities (`cap_add` in compose) and `/dev/net/tun`. It is available on
  amd64 and arm64, but not arm/v7. Set `WARP_ENABLE_NAT=true` to connect at startup.
- WARP's full-tunnel mode routes the container's traffic through
  Cloudflare and **can interfere with remote access** to the container —
  streams and proxied requests may stall or become unreachable while the
  tunnel is up (see issue #93).
- Recommendation: enable WARP only when you need it for **scraping
  egress** (reaching sources that block your ISP/geo). Keep it off on
  installations whose main job is serving remote players; if you need
  both, prefer running the scraper instance with WARP separately from the
  streaming path.

## Quick verification

After wiring up the proxy:

```bash
# Auth is enforced
curl -s -o /dev/null -w '%{http_code}\n' https://scraper.example.com/api/v1/health/          # 401
curl -su youruser:yourpass -o /dev/null -w '%{http_code}\n' https://scraper.example.com/api/v1/health/  # 200

# Playlist comes through, gzip works
curl -su youruser:yourpass -H 'Accept-Encoding: gzip' -I https://scraper.example.com/playlist.m3u

# Stream ports are NOT reachable from outside
curl -s --max-time 5 http://scraper.example.com:6878/webui/api/service || echo "6878 closed (good)"
curl -s --max-time 5 http://scraper.example.com:8080/ace/status || echo "8080 closed (good)"

# The tuner is reachable without credentials, and only from the allowed networks
curl -s -o /dev/null -w '%{http_code}\n' https://scraper.example.com/tuner/discover.json
# 403 from outside TUNER_ALLOWED_NETWORKS (the carve-out works, the gate holds)
# 200 from the LAN / from the media server's host
# 401 means basic auth is still in front of /tuner/ — the carve-out is not applied
```

Then open a playlist entry in a player from the network position it will
really be used from, to confirm the `base_url` target is reachable.

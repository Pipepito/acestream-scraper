# Reverse Proxy / HTTPS Deployment

## Scope

This guide covers putting the v2 app (uvicorn on port `8000`) behind a
TLS-terminating reverse proxy for access from outside a trusted network:

- nginx, Caddy, and Traefik configurations
- proxy-level authentication, and the app's optional `API_TOKEN`
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

Proxying notes that apply to all three configs:

- **No websockets.** The app is plain request/response HTTP; no `Upgrade`
  header handling is needed.
- **Standard forwarded headers** (`Host`, `X-Forwarded-For`,
  `X-Forwarded-Proto`) are enough.
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

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

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
    basic_auth {
        # Generate the hash with: caddy hash-password
        youruser $2a$14$REPLACE_WITH_CADDY_HASH
    }
    reverse_proxy 127.0.0.1:8000
}
```

(`basic_auth` is the Caddy 2.8+ directive name; older Caddy 2 releases
spell it `basicauth`.)

## Traefik (compose labels)

Add labels to the `app` service in `docker-compose.yml`. With Traefik on
the same Docker network, drop the `ports: "8000:8000"` mapping entirely —
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
| `8080` | Acexy: `/ace/getstream` + `/ace/status` (`ACEXY_LISTEN_ADDR`, healthchecked via `ACEXY_STATUS_PORT`) | `*-acexy` flavors with `ENABLE_ACEXY=true` | **Never publicly.** Same unauthenticated stream/status surface. LAN/VPN only. |
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
  capabilities (`cap_add` in compose). It is amd64-only.
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
```

Then open a playlist entry in a player from the network position it will
really be used from, to confirm the `base_url` target is reachable.

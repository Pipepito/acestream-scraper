# Requirements

Use the [Docker command builder](https://pipepito.github.io/acestream-scraper/) to select the image, architecture, enabled services, ports and storage together. An image containing a service does not start it automatically.

## Host and capacity

Run Linux containers on a supported Docker Engine/Compose installation or Docker Desktop. Examples use the `docker compose` command. For manual installation, use a Linux-compatible environment and the dependencies in `backend/requirements.txt`; the container pins application Python 3.13. The frontend is built separately with Node/npm. See [Installation](Installation.md#manual-installation).

Capacity depends on enabled services, guide size and concurrent playback. Do not size a full deployment from a scraper-only memory estimate:

- Scraping, XMLTV imports and SQLite backups need working memory and free disk space.
- Each bundled engine adds its own RAM, cache and peer bandwidth; a separate checker adds another engine.
- Browser sessions share FFmpeg for the same stream/audio choice. Different choices consume additional sessions, up to `PLAYER_MAX_SESSIONS` (default 3).
- Default tuner relays preserve source bytes. Experimental transcoding recovery encodes video for each viewer and needs substantially more CPU.
- IPFS/ZeroNet data and engine caches can grow. A host mount changes where data is stored, not its size limit.

Keep enough free space for database upgrades/recovery backups as well as live data. Backups are not automatically pruned. See [storage planning](Docker.md#recommended-cache-and-temporary-storage).

## Architecture and optional services

| Feature | amd64 | arm64 | arm/v7 |
|---|---|---|---|
| Scraper, UI and bundled FFmpeg | Yes | Yes | Yes |
| Bundled AceStream in engine flavors | Native Linux 3.2.11 | Community Android 3.2.17 | Community Android 3.2.17; experimental |
| WARP and bundled IPFS | Available, opt-in | Available, opt-in | No upstream packages; external IPFS gateway usable |
| Bundled ZeroNet | Available, opt-in | Use external node | Use external node |

ARM engines require a 4 KB kernel page size. On Raspberry Pi 5 this may require selecting `kernel8.img`. A successful cross-platform image build does not prove playback on real hardware; ARMv7 runtime validation remains outstanding. See [Docker platform notes](Docker.md#playing-streams-on-arm).

Only WARP requires `NET_ADMIN`, `SYS_ADMIN` and `/dev/net/tun`. Ordinary engine operation does not require privileged mode. Tor is optional with bundled ZeroNet or configured on an external node.

## Network access

The backend must reach its configured engines, gateways and sources. Each client must reach both its playlist URL and the stream addresses inside it. HTTP relay clients need the scraper web endpoint; clients using direct engine/Acexy formats also need those respective endpoints.

| Default port | Purpose | Publish on the host? |
|---|---|---|
| 8000/TCP | Web UI, API, browser player and tuner relay | Yes; builder uses `0.0.0.0:8000:8000` |
| 6878/TCP | Playback engine HTTP API | Only for direct external clients; trusted networks only |
| 8080/TCP | Acexy | Only for clients connecting directly; trusted networks only |
| 8621/TCP+UDP | Playback engine P2P | Useful for peer connectivity |
| 6880, 6881, 62063, 8622 | Dedicated checker internal ports | Keep internal and separate from playback overrides |
| 4001/TCP+UDP | IPFS swarm | Useful for peer connectivity when bundled IPFS is enabled |
| 8081/TCP | IPFS gateway | Only if used outside the container |
| 5001/TCP | IPFS RPC/WebUI | Unauthenticated; expose only on host loopback if needed |
| 43110/TCP | ZeroNet UI | Only for external browsing; trusted networks only |
| 26552/TCP | ZeroNet peer/fileserver | Useful when bundled ZeroNet is enabled |

See [port configuration](Configuration.md#port-mapping), [reverse proxies](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/reverse-proxy.md) and [media-server access](Media-Servers.md#before-you-start).

## Browsers and players

Use a current Chrome/Chromium, Firefox, Edge or Safari browser. Browser playback needs a source video codec supported by the device; the server converts audio to AAC and passes video through. Safari/iOS use native HLS; other supported browsers use the bundled HLS client. Codec support varies by browser and OS; use VLC/Kodi when a format is unsupported.

For `acestream://` playlist links, the viewing client needs native AceStream support or an appropriate integration. For HTTP relay/Acexy links, it needs M3U/HTTP streaming support and network access to the selected server. See [Web Player](Web-Player.md) and [Remote Players](Remote-Players.md).

## Persistent storage

Always persist `/app/config`. Add service state/cache and player mounts for the enabled features; optionally retain `/app/logs` across container replacements. SQLite storage must support file locking and atomic renames, and only one application worker may own a database. Keep database backups private.

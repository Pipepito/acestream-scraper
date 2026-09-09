# Troubleshooting

Start with **Overview → Services** and **Scheduled jobs**. Service state, the last job result and a stream's last verified signal answer different questions. An engine that is running does not guarantee that a particular broadcast is available.

## Find the right check

| Problem | Check first | More help |
|---|---|---|
| New install has no channels | Add an enabled source in Scraper, run Scrape and inspect its result | [Source workflow](Usage.md#step-3-add-and-scrape-a-source) |
| Stream inventory has entries but Live TV is empty | Assign streams to active TV channels; check catalogue filters | [Channel management](tasks/channel-management.md) |
| Scraper-only install has no engine | This is supported. Set a playback URL only if you need engine search or playback, or a checker for signal checks | [Configuration](Configuration.md#application-settings) |
| Checks are skipped or results stay unchanged | Settings → Automation: checker selection; Overview: checker state. Dedicated checker failure never falls back | [Signal checks](Configuration.md#channel-status-checking) |
| A new import is not online | Imports leave IDs unchecked. Run a signal check; catalogue availability alone does not verify media | [Signal checks](Configuration.md#channel-status-checking) |
| Channel is online but will not play | The result is a snapshot. Try another stream and inspect player feedback | [Playback](#playback-will-not-start-or-stops) |
| Playlist is empty or has duplicate stations | Review online/favorite/group filters, assignments and selected link format | [Playlist](#playlist-or-remote-player-cannot-reach-the-stream) |
| Current programme is missing or wrong | Source refresh result, linked EPG ID, device timezone and clock | [Programme guide](#programme-guide-is-empty-or-wrong) |
| API asks for a token | Save the server's API_TOKEN in Settings → API access; on startup use that screen's token field | [Access](Configuration.md#security-considerations) |
| App remains on startup screen | Free space, permissions, upgrade milestones and recovery options | [Startup recovery](#startup-or-upgrade-does-not-finish) |

## Playback will not start or stops

1. Check **Settings → Playback**. Its engine URL must be reachable **from the backend container**. `localhost` refers to that container, not another machine. For a host engine on Linux, configure `host.docker.internal:host-gateway` when using that name.
2. If **Route playback through Acexy** is on, check that Acexy is running, its URL is reachable from the backend and it serves MPEG-TS. Starting Acexy in Docker does not enable this routing setting. New sessions use saved routing; existing ones retain their original route.
3. In Live TV, try another **Stream**, then Retry if offered. Peers, an engine ID lookup and a past online result do not guarantee a usable broadcast now.
4. If the browser reports an unsupported video codec, open the stream in VLC/Kodi. The browser player copies video and converts audio; it does not convert unsupported video codecs. Choose **Audio track** if the source exposes several tracks.
5. At the session limit, close another viewer or wait for cleanup before retrying. Different channels/audio choices use separate FFmpeg sessions. Multiple viewers of the same choice share one.
6. If checks interrupt players connected straight to an engine, use a dedicated checker. A PID alone cannot isolate stopping the same source on native engine 3.2.11. The app can coordinate its own web/relay sessions; direct external players are outside that registry.

For stable TV relay URLs, default recovery ends a failed response and relies on the player reconnecting to the **same URL**. Recently failed sources are tried later. A raw content-ID URL has no channel fallback. **Experimental transcoding recovery** in Integrations → Tuner settings attempts recovery within the same connection, costs substantial CPU and is not a guarantee of uninterrupted playback. See [relay behavior](Media-Servers.md#channels-with-several-streams).

## Playlist or remote player cannot reach the stream

The playlist URL and each stream URL must both be reachable from the viewing device.

- Set **Integrations → Public address** to the scraper's reachable HTTP(S) origin and published web port. Avoid `localhost` for a different device.
- **TV channel relay (automatic failover)** uses `/tuner/channel/{tv_channel_id}.ts`, one entry per station. Assign streams and verify their signal first. The relay uses eligible online sources.
- **Server relay** uses `/tuner/stream/{channel_id}.ts`, one specific AceStream ID. Appending unassigned streams to a TV relay playlist also uses this individual route.
- **AceStream direct** and **Acexy** formats need their respective published ports reachable from the player. `{channel_id}` is a stream hash; `{tv_channel_id}` is a station ID. They are not interchangeable.
- A saved default format changes all links that use that default. The inline Playlist editor and Settings → Stream links edit the same formats.
- With API protection, the generated M3U URL may contain `?token=...`. Keep URLs and QR codes private. `/tuner/*` uses `TUNER_ALLOWED_NETWORKS` instead; adding an API token will not fix a tuner 403.
- Behind a proxy, configure trusted proxy addresses and keep tuner routing compatible with your media server. See [reverse proxy deployment](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/reverse-proxy.md).

For Plex/Jellyfin, refresh the guide/lineup after changing channels or formats. Plex also needs channel rescan/mapping in its own interface. See [Media Servers](Media-Servers.md) and [Remote Players](Remote-Players.md).

## Programme guide is empty or wrong

In **EPG → Sources**, check the last refresh and error. In **Channels**, confirm the guide contains the station, then verify the TV channel's EPG mapping. Matching names alone do not guarantee the right regional edition. Refreshing XMLTV cannot fix an incorrect station assignment.

Refreshes replace older listings that overlap valid programmes supplied by the same source, including title or timing corrections. Gaps, channels absent from the feed and listings from other sources are preserved; empty feeds do not clear the guide. If programmes still overlap after a successful refresh, check whether the provider includes those overlapping entries in its XMLTV feed.

Guide times use the viewing device's timezone; XMLTV timestamps are normalized by the backend. Check the device clock. Today hides programmes that have ended; future tabs retain their full schedule. No current programme does not mean no broadcast.

Large legacy guide imports continue in resumable batches. Use the import banner or **Settings → Startup diagnostics** for progress. Do not delete migration checkpoints or the archived v1 database while an import is unfinished.

## Scraper or optional service fails

Use the source row's result and diagnostic logs. JavaScript rendered pages are not executed by the scraper; a direct M3U, JSON or text feed is often more suitable. **Harvest bare content IDs** enables unstructured hashes; structured name/ID text lists are recognized automatically. See [supported source formats](Contributing-Scraper-Data.md).

- **IPFS/IPNS:** enable bundled IPFS on amd64/arm64, or set a reachable `IPFS_GATEWAY_URL`. `inbrowser.link` Auto/IPFS sources are routed through that HTTP gateway; they cannot depend on a browser service worker. Cold content may take time to find providers.
- **ZeroNet:** bundled on amd64 only, opt-in with `ENABLE_ZERONET=true`; on ARM use `ZERONET_URL` for an external node. The node and the requested site must both be reachable.
- **WARP:** inspect System → WARP. Running and Connected are separate states. It requires amd64/arm64, `ENABLE_WARP=true`, `NET_ADMIN`, `SYS_ADMIN` and `/dev/net/tun`. `WARP_ENABLE_NAT=true` connects at startup; otherwise use Connect. WARP does not guarantee access to an unavailable source.
- **Engine crashes:** the supervisor retries exits indefinitely. An intentional Overview Stop pauses recovery until Start/Restart or container restart. A separate checker has independent controls and logs; its outage does not make the entire container unhealthy.

## Startup or upgrade does not finish

Open the normal app address or `/startup`. The screen remains available during database work and after a failed upgrade; normal APIs and health return 503 until startup succeeds. A large background programme import can continue after the rest of the app becomes usable.

1. Read the latest startup milestone; download startup diagnostics and runtime logs.
2. Check disk space and data-folder permissions. Do not run two application instances against the same SQLite database.
3. Fix the cause, then choose **Try startup again**. Avoid repeatedly recreating the container while inspecting a failed startup.
4. For a database failure, **Recover readable data** attempts a backup-first rebuild of readable sources/settings/channels; listings can be refreshed later. It is not full SQLite repair and may skip damaged rows.
5. **Start fresh** replaces the active database with an empty one after backup and explicit confirmation. Use it only when you intend to rebuild your configuration.

Recovery retains originals, sidecar files and checkpoints in a private backup folder. Do not share databases as diagnostic attachments or mix files from different backups. For rollback/recovery details use the [operator recovery guide](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/startup-recovery.md) and [upgrade guide](Installation.md#updating-to-a-newer-image).

## Collect evidence for a bug report

Choose **Overview → Services → Download diagnostics**. The ZIP includes bounded recent scraper, entrypoint and per-service logs, including a dedicated checker when enabled. Capture starts with the updated container; it cannot recover old output or external-engine logs. Logs survive container replacement only if you persist the log directory.

The export masks common credentials and addresses, but review it before sharing. Include image tag/digest, architecture, steps, expected/actual behavior and the time of the failure. See [Bug Reporting](Bug-Reporting.md).

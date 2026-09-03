# Web Player

Play a channel straight in your browser — no VLC, no Acestream engine plugin, nothing to install on the viewing device.

## What it does

Every image ships a small, statically-linked ffmpeg (built during the image build, one static binary per platform/flavor — no extra install step). When you press **Play**, the backend asks the AceStream engine for that channel and starts one ffmpeg process for it: the video track is copied through untouched, the audio track is re-encoded to AAC (AceStream channels are often MPEG-2 audio or AC-3, which browsers cannot play), and the result is repackaged as an HLS stream (2-second segments, a 6-segment sliding window) that `hls.js` (or the browser's native HLS support on Safari/iOS) plays back.

That segmenting and buffering means the player runs roughly 6–10 seconds behind live — expected for HLS, not a fault.

One ffmpeg process is shared per channel, not per viewer: if two browser tabs (or two people) play the same channel at once, they join the same session instead of doubling the transcode cost. A session is torn down automatically a few seconds after its last viewer leaves, or after it sits idle, so it does not keep using engine and CPU resources in the background.

Because the video track is passed through as-is, a browser that cannot decode it natively (MPEG-2, MPEG-1, VC-1, MPEG-4 v3) still cannot play the channel — the player tells you so and points you at VLC or Kodi instead of pretending it will work.

## Requirements

- **ffmpeg is bundled.** Every flavor and platform (`scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`; amd64, arm64, arm/v7) includes it — nothing to enable, nothing to configure to get started.
- **To use your own ffmpeg build instead**, set `FFMPEG_BINARY_PATH` to its path. Leaving it empty (the default) uses the bundled binary; if that is somehow missing, the app falls back to whatever `ffmpeg` it finds on `PATH`.
- **ARM engine caveat:** on `linux/arm64`, playback runs through a community-maintained AceStream engine build ([`jopsis/acestream`](https://github.com/jopsis/docker-acestream-aceserve)) that is not premium-gated — the web player is expected to work there but is not yet confirmed against real hardware playback. On `linux/arm/v7`, the official engine AceStream ships is Premium-only for live playback outside their own app, so the web player (and any other playback path) will not work on 32-bit ARM until that changes. See [Docker Guide](Docker.md) for the full ARM engine notes.

## Playing a channel

Wherever a channel appears in the app — Acestream Channels, TV Channels (including the channel detail page) and Search — its row actions carry a **Play** button (alongside **Check status**; anything else lives under "More actions" on crowded rows). Press it to open the player dialog: it starts a session, waits for the first HLS segments, and then plays automatically.

While a channel is starting, the dialog shows the engine's peer count and download speed as they become available. Once segments are ready it switches to **Playing**. Closing the dialog (or navigating away) releases the session; if you are the only viewer, the backend stops ffmpeg and the engine stream a few seconds later.

## Status and error messages

The player explains problems in plain language instead of raw codes:

| What you see | What it means | What to do |
|---|---|---|
| "This server can't prepare streams for the browser. Open the channel in VLC instead." | No ffmpeg is available on the server | Use VLC/Kodi with the stream link, or fix `FFMPEG_BINARY_PATH` |
| "No one is sharing this channel right now. Try again later or pick another stream." | The engine never produced a usable stream before the start timeout | Try another channel, or retry later |
| "The stream stopped unexpectedly. Try again." | ffmpeg exited mid-stream | Press **Retry** |
| "The AceStream engine could not start this channel: …" | The engine refused or was unreachable | Check the engine URL under Settings, or that the engine is running |
| "Your browser can't play this channel's video format (…). Send it to VLC or Kodi instead." | The source video codec (MPEG-2, MPEG-1, VC-1, MPEG-4 v3) is not one browsers decode | Open the stream link in VLC or Kodi |
| "Too many channels are playing at once…" | `PLAYER_MAX_SESSIONS` distinct channels are already active | Close another player tab, or raise the limit |

Errors that are not a dead end (everything except "ffmpeg is missing") offer a **Retry** button in the dialog.

## VLC, Kodi and other players

The dialog's **Copy stream link** button copies a direct MPEG-TS link to the channel (the same route Jellyfin and Plex tuners use) that plays in VLC, Kodi, or any player that opens network streams — no browser, no transcoding, and no `?token=` needed on that particular link: it works from the address it can reach precisely because it is gated by network address (`TUNER_ALLOWED_NETWORKS`), not by the API token, since tuner-style clients cannot send one.

## The knobs

The web player has three settings, all environment variables (see [Configuration Reference](Configuration.md#media-integrations) for the full table):

- **`PLAYER_MAX_SESSIONS`** (default `3`) — how many *distinct* channels the player prepares at once. Each one costs one engine stream and one ffmpeg process; raise it if you regularly want more channels playing side by side.
- **`PLAYER_HLS_DIR`** (default `/tmp/acestream-player`) — where segments are written. Point it at `/dev/shm/acestream-player` (with a larger `--shm-size`/`shm_size`) to keep them in RAM instead of on disk.
- **`PLAYER_START_TIMEOUT_SECONDS`** (default `45`) — how long a session may sit in "starting" before it is reported as stalled. Raise it on slow links where a channel takes longer to buffer its first segments.

The [Docker command builder](https://pipepito.github.io/acestream-scraper/) can set `PLAYER_MAX_SESSIONS` for you under Container options; the other two are best set directly as environment variables.

## API token

If you have set an `API_TOKEN`, links elsewhere in the app that need it (the M3U playlist link, in particular) carry it automatically as `?token=` when you copy them. The web player's own stream link does not carry a token — it does not need one, because the tuner route it uses is gated by network address instead (see above). The HLS video stream itself carries the token too, with nothing for you to do: browsers that play it through `hls.js` (Chrome, Firefox, Edge) send it as a request header, while Safari and iOS — which play HLS themselves and cannot add headers — get it as `?token=` on the stream address instead.

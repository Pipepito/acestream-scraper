# Web Player

Play a channel straight in your browser — no VLC, no Acestream engine plugin, nothing to install on the viewing device.

## What it does

Every image ships a small, statically-linked ffmpeg (built during the image build, one static binary per platform/flavor — no extra install step). When you press **Play**, the backend asks the AceStream engine for that channel and starts one ffmpeg process for it: the video track is copied through untouched, the audio track is re-encoded to AAC (AceStream channels are often MPEG-2 audio or AC-3, which browsers cannot play), and the result is repackaged as an HLS stream (2-second segments, a 6-segment sliding window) that `hls.js` (or the browser's native HLS support on Safari/iOS) plays back.

Playback can connect directly to the engine (with a unique PID per session) or
through Acexy. Choose **Route playback through Acexy** under **Settings › Engine**;
see [Playback routing](Remote-Players.md#playback-routing).

That segmenting and buffering means the player runs roughly 6–10 seconds behind live — expected for HLS, not a fault.

One ffmpeg process is shared per channel and selected audio track: if two browser tabs (or two people) play the same channel with the same audio selection, they join the same session instead of doubling the transcode cost. A session is torn down automatically a few seconds after its last viewer leaves, or after it sits idle, so it does not keep using engine and CPU resources in the background.

Because the video track is passed through as-is, a browser that cannot decode it natively (MPEG-2, MPEG-1, VC-1, MPEG-4 v3) still cannot play the channel — the player tells you so and points you at VLC or Kodi instead of pretending it will work.

## Requirements

- **ffmpeg is bundled.** Every flavor and platform (`scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`; amd64, arm64, arm/v7) includes it — nothing to enable, nothing to configure to get started.
- **To use your own ffmpeg build instead**, set `FFMPEG_BINARY_PATH` to its path. Leaving it empty (the default) uses the bundled binary; if that is somehow missing, the app falls back to whatever `ffmpeg` it finds on `PATH`.
- **ARM engine caveat:** on `linux/arm64`, playback runs through a community-maintained AceStream engine build ([`jopsis/acestream`](https://github.com/jopsis/docker-acestream-aceserve)) that is not premium-gated — the web player is expected to work there but is not yet confirmed against real hardware playback. On `linux/arm/v7`, the official engine AceStream ships is Premium-only for live playback outside their own app, so the web player (and any other playback path) will not work on 32-bit ARM until that changes. See [Docker Guide](Docker.md) for the full ARM engine notes.

## Playing a channel

Wherever a channel appears in the app — Acestream Channels, TV Channels (including the channel detail page) and Search — its row actions carry a **Play** button (alongside **Check status**; anything else lives under "More actions" on crowded rows). Press it to open the player dialog: it starts a session, waits for the first HLS segments, and then plays automatically.

While a channel is starting, the dialog shows the engine's peer count and download speed as they become available. Once segments are ready it switches to **Playing**. Closing the dialog (or navigating away) releases the session; if you are the only viewer, the backend stops ffmpeg and the engine stream a few seconds later.

## Live TV and choosing a stream

Live TV uses the available page width. While watching, TV channels and unassigned
streams share a scrollable catalogue; each section grows with its content.
**Playback options › Larger player** gives the video more space on desktop, and
**Standard player** restores the split. The top-bar navigation button collapses
or restores the sidebar. These layout controls do not restart playback.

The watched channel's **Schedule** opens below the player controls by default in
its own scrollable section. Today shows programmes still on air and upcoming
programmes, hiding entries once their end time passes. Future day tabs retain
their full schedule. Guide times remain in the browser's timezone.

**Send to player** beside Watch sends a channel directly to a saved external
player without starting browser playback. Add players and access their playback
controls under **Integrations › Remote players**.

Open **Live TV** from navigation to browse active TV channels, search by name,
category or channel number, and filter favorites. Each channel shows its current
and next programme when its EPG source and ID are mapped. Only channels with attached
streams appear here; TV Channels remains the full management inventory. The list
loads guides for at most twelve visible channels at a time.

**Online streams without a channel** lists streams whose last check was online and
which have no TV channel assignment. It has its own search and pagination and
refreshes every 30 seconds. Watch opens the same player, without an invented TV
schedule. Online is a saved check result, not a guarantee that playback will start.

Press **Watch** to open the player and schedule. The **Stream** selector lists every
attached stream, its last known online status and a short ID. Switching releases
the previous viewer and starts the selected stream. Copy stream link and Play on
both follow the selected stream. A channel can be opened directly at
`/live-tv?channel=123` (replace 123 with its TV channel ID).

The initial stream uses the server's existing ranking: online status (+10), logo
(+3), EPG ID (+2), and EPG name (+1), then stream ID to break ties. This ranking does
not measure resolution or buffering. Choose another stream if the default fails.

Players opened from TV Channels retain that channel's schedule and alternatives.
Players opened from an AceStream ID look up its assigned TV channel; an unassigned
ID has no channel schedule or alternatives.

Guide times are shown in the viewing device's timezone, named beside the guide.
XMLTV offsets are normalized to UTC by the backend and converted once for display.
The on-air marker updates every 30 seconds and guides refresh every minute while
open. No current programme means the guide has no matching entry; it does not mean
the channel is offline. Correct your device clock and EPG mapping/source if the
schedule is wrong. HLS playback can still trail the broadcast by several seconds.

On phones, the player fills the screen and its schedule scrolls independently of
the bottom actions. Scraper sources, EPG sources and scheduled jobs show stacked,
labelled fields so their controls remain reachable without sideways scrolling.

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
| "Playback stopped in your browser. Try again." | The browser's player hit an error it could not recover from (it retries network and buffer errors a few times first) | Press **Retry** |
| "The stream ended." | The session was released after nobody watched it for a while | Press **Retry** |

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


## Open-stream counts

The Overview service details refresh every 30 seconds and show:

- **AceStream engine — Open streams through this app:** distinct content IDs in
  this app process's web-player and relay registries. Multiple viewers of the same
  ID count once. Starting sessions and sessions waiting to close count; failed
  web-player sessions and closed relays do not. Direct external players and Acexy
  are outside this count, so zero does not establish that the entire engine is idle.
- **Acexy — Open streams through Acexy:** the proxy's `streams` value from
  `/ace/status`, including any streams retained until its cleanup timeout. This is
  not a viewer count. Missing or invalid telemetry is **Unavailable**, not zero.

The counts can overlap and must not be added. Neither count proves that a player
is currently receiving video. The documented [engine status API](https://docs.acestream.net/developers/api-reference/#get_status)
does not provide an engine-wide playback total.


## Choosing audio

The player discovers input audio tracks as ffmpeg opens the stream. **Audio track**
shows the track number, language, codec and channel layout when the source provides
them. Choose a track to restart your browser playback with that audio; other
viewers keep their own selection. The first audio track is the default. A source
without detectable audio metadata has no selector.

Different audio selections use separate HLS/ffmpeg sessions and count against the
player session limit. The previous session closes after its normal grace period;
at capacity, close another player or wait for that cleanup before retrying.
Selected audio is converted to stereo AAC. Copied raw stream links and remote
player actions carry the original source with all its audio tracks, rather than
forcing the browser's selection on that player.

The channel stream picker also displays saved bitrate and audio-track counts when
available from status checks. The tuner alone uses bitrate order; the web player's
existing manual stream selection remains available.

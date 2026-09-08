# Media Servers (Jellyfin and Plex)

Watch your channels in Jellyfin or Plex, with a full TV guide, using the apps you already use on the TV, phone and tablet.

The app pretends to be an **HDHomeRun tuner** — a network TV tuner both Jellyfin and Plex support out of the box. They ask it for a channel list, ask it for a guide, and pull the video from it. Nothing is installed in Jellyfin or Plex, and no plugin is involved.

## Before you start

**Three things have to be true**, and the app checks all three for you under **Integrations**.

1. **The media server can reach this app.** Jellyfin and Plex fetch the channel list, the guide and the video themselves, from wherever they run. The address they use is the **Public address** at the top of the Integrations page. If that shows something only your browser can reach (`localhost`, a Docker-internal name), type the address the media server would use — usually this machine's LAN address, e.g. `http://192.168.1.10:8000` — and press **Save**.

2. **The media server is on an allowed network.** The tuner routes (`/tuner/*`) carry no API token, because no media server can send one — Jellyfin and Plex fetch them with a plain HTTP client, and Plex has no credential field at all. They are gated by **address** instead: only clients inside `TUNER_ALLOWED_NETWORKS` are answered, everything else gets `403`. The default list is every private range plus loopback and Tailscale's `100.64.0.0/10`, so a media server on your LAN is already allowed. See [Configuration](Configuration.md#media-integrations).

3. **The app sees real client addresses.** Publish the web port as `-p 0.0.0.0:8000:8000`, never the bare `-p 8000:8000`. An unaddressed mapping also listens on IPv6, and Docker then rewrites every IPv6 client to the bridge gateway (`172.17.0.1`) before the app sees it — which is inside the allowed list, so the address gate stops meaning anything. The **Public address** block on the Integrations page warns you when it sees this ("This host hides real client addresses…").

Behind a reverse proxy there is one more rule: `/tuner/` must be excluded from proxy authentication, because these clients cannot answer a login prompt. The nginx, Caddy and Traefik snippets are in [Reverse Proxy / HTTPS](https://github.com/Pipepito/acestream-scraper/blob/main/docs/ops/reverse-proxy.md).

## Jellyfin

### 1. Create an API key in Jellyfin

**Dashboard › API Keys › +**, name it (for example `AceStream Scraper`) and copy the key. It must be an administrator's key: the app has to write Live TV configuration, which a normal user key cannot do.

### 2. Add the server here

**Integrations › Media servers › Add media server**. Pick **Jellyfin**, give it a name, type its address (`http://192.168.1.10:8096`) and paste the API key.

Press **Test connection** first. It reports what it found:

| What you see | What it means |
|---|---|
| "Jellyfin is reachable (version 10.11.11)." | The address and key are good. |
| "Jellyfin rejected the API key (it must be an administrator API key from Dashboard > API Keys)" | Jellyfin answered, but the key is wrong, was revoked, or is not an administrator's. |
| "Jellyfin at … did not answer: …" | Wrong address or port, or Jellyfin cannot be reached from this app. |
| "… Jellyfin at 203.0.113.9 is outside TUNER_ALLOWED_NETWORKS and will get 403 from the tuner routes; add its network." | Jellyfin is fine, but it would be refused when it fetches the channel list. See the address rule above. |

### 3. Connect

Press **Connect** on the server's card. The app then, in Jellyfin:

- adds (or updates) a **tuner** pointing at `http://<public address>/tuner`, and
- adds an **XMLTV guide provider** pointing at `http://<public address>/tuner/guide.xml`, bound to that tuner only.

Jellyfin validates the tuner by fetching it right away, so a wrong public address fails here with a clear message ("Jellyfin could not download …; check the public address") rather than silently later. The channels appear under **Live TV** once Jellyfin has run its **Refresh Guide** task; press **Refresh now** on the card to ask for it straight away.

**Disconnect** removes both again. It asks first, because Jellyfin drops those channels when it does.

### HDHomeRun or M3U

The dialog offers two modes. **HDHomeRun is the recommended one** and the default.

| | HDHomeRun (recommended) | M3U |
|---|---|---|
| What Jellyfin sees | A tuner device with a channel list | A playlist file |
| Channel identity | Stable. A channel keeps its identity in Jellyfin across guide and lineup changes | Re-keyed whenever a channel's number changes: Jellyfin identifies M3U channels by their `tvg-id`/number, so favourites, recordings and images can detach |
| Guide linking | By channel number, automatic | By `tvg-id`, which some people prefer because it matches their existing XMLTV setup |

Pick M3U only if you specifically want `tvg-id` linkage and accept the re-keying caveat. Switching modes later means Jellyfin re-identifies everything once.

### How refreshing works

Three things move the guide along, and you rarely need to do anything by hand:

- **Jellyfin's Refresh Guide task** is what actually pulls a new guide. The app asks Jellyfin to run it.
- **On your EPG schedule**, this app refreshes its own EPG data from your EPG sources — every 6 hours unless you change **Refresh EPG every (hours)** on the Settings page.
- **Every ten minutes**, a background job compares the current channel list and guide with what was last pushed. If either changed, it asks Jellyfin to refresh — no more often than `MEDIA_SERVER_MIN_REFRESH_MINUTES` (default 30 minutes) apart, so a busy evening of edits does not hammer the server. Set it to `0` to remove the delay.

**Refresh now** on the card bypasses that delay and asks Jellyfin to refresh immediately.

The card's second chip tells you where the guide stands: *Guide up to date*, *Not synced yet*, *Refresh failed* (with the reason), or *Rescan the guide in Plex*.

## Plex

Plex Live TV needs an active **Plex Pass**. Without one, Plex does not offer tuner setup at all.

Plex also has no API for adding a tuner, so this part is done in Plex's own UI. The app gives you the exact values to paste, with copy buttons, on the server's card.

1. In Plex Web: **Settings › Live TV & DVR › Set Up Plex Tuner**.
2. Plex scans for tuners and will not find this one (it is not on the multicast discovery network). Click **"Don't see your HDHomeRun device? Enter its network address manually"** and paste the **tuner address** — `host:port/tuner`, for example `192.168.1.10:8000/tuner`. No `http://`.
3. Pick any country when asked, then choose **"Have an XMLTV guide on your server?"** and paste the **guide URL** — `http://192.168.1.10:8000/tuner/guide.xml`.
4. Review the channel mapping and finish.

**After channels change here, Plex needs a rescan**: **Live TV & DVR › Manage Channels › Rescan** (guide) in Plex. The app cannot do this for you unless you give it a token.

**Optional: automatic guide reloads.** Paste a Plex **owner token** (`X-Plex-Token`) into the server's API key field and the app finds your DVR and reloads its guide by itself, on the same ten-minute schedule as Jellyfin. Without a token the sync job still notices that channels changed — it just flags the card *Rescan the guide in Plex* instead of doing it. Finding your token is documented by Plex under "Finding an authentication token".

After completing setup in Plex, press **Connect** on the scraper's Plex card to
discover the DVR. The scraper matches its advertised DeviceID against Plex's
device `deviceId` or HDHomeRun `uuid` (also accepting the older identity in `uri`).
The card's **Connected** status means this DVR association is saved for guide
refreshes; Live TV can work before that association is found.

**The channel cap.** Plex stops saving channel maps somewhere around **450-480 channels** — the exact limit depends on how long your channel numbers and names are, and the failure is silent: the mapping simply does not stick. The tuner therefore stops at the **Most channels to publish** setting (default **450**) and tells you how many channels were left out. If you are near the limit, deactivate channels you do not watch rather than raising the number.

## Tuner settings

**Integrations › Media servers › Tuner settings**:

- **Tuner name** — what Jellyfin and Plex show for this tuner. Default "AceStream Scraper".
- **Streams at once** — how many channels may be streamed through the tuner at the same time (default 4). It is the number the tuner advertises to Jellyfin and Plex, and the one it actually enforces: a request beyond it is refused with "All 4 tuner slots are in use". Each concurrent stream is a real AceStream stream on your engine and real upload bandwidth, so keep this near what your connection can actually carry.
- **Publish only channels that are online** — off by default. With it off, a channel whose streams are all currently offline is still listed, so tuning it fails with a clear error instead of the channel vanishing from your TV app. Turn it on if you would rather see a shorter, verified list.

The addresses to paste into Plex, and the warnings about refused clients or channels left out, are shown where they matter: on the Plex card and in the **Public address** block above.

## Channel numbers

Each channel gets a **GuideNumber**, the number Jellyfin and Plex show and sort by:

- A channel with a **channel number** set under TV Channels keeps that number.
- Everything else gets an automatic number starting at 1000 (or just above your highest manual number).
- If two channels claim the same number, the first one in playlist order keeps it and the other gets an automatic number instead. Which channels this happened to is listed by `GET /api/v1/tuner/status` under `renumbered`.

**One caveat worth knowing.** Giving a channel a manual number that is *higher* than the automatic range — or removing the channel that holds your highest manual number — shifts the automatic numbers of every unnumbered channel. The lineup then looks completely new to the media server: Jellyfin re-identifies those channels, and Plex needs a rescan. If you plan to number your channels by hand, do it in one pass rather than one at a time.

## Troubleshooting

**Jellyfin or Plex gets 403 from the tuner.** The media server's address is outside `TUNER_ALLOWED_NETWORKS`. The **Public address** block names the most recent refusal and the address it came from — add that network to `TUNER_ALLOWED_NETWORKS`, or check that the app is seeing real client addresses (`-p 0.0.0.0:8000:8000`, and a reverse proxy listed in `FORWARDED_ALLOW_IPS`).

**Plex says the tuner is dead, or Jellyfin's tuner turns red.** The public address changed — a new DHCP lease, a moved container, a different port. Fix the **Public address** on the Integrations page, then press **Connect** again (Jellyfin) or re-enter the tuner address in Plex.

**No channels show up in Jellyfin.** Check the lineup itself, from a machine on an allowed network:

```bash
curl -s http://192.168.1.10:8000/tuner/lineup.json | head
```

An empty `[]` means the tuner has nothing to publish: channels need to be **active TV channels with at least one Acestream stream attached**. Acestream streams that are not linked to a TV channel are not published. If the list looks right, run Jellyfin's **Refresh Guide** task once by hand.

**A channel tunes but never plays.** That is the engine, not the tuner. Check the channel in the web player first — the error there names the cause. On 32-bit ARM (`linux/arm/v7`) playback needs a Premium AceStream account; see [Docker](Docker.md#playing-streams-on-arm).

**Nothing at all answers on `/tuner/`.** Check it directly:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.1.10:8000/tuner/discover.json
```

`200` means the tuner is fine and the problem is on the media-server side. `403` is the address gate. Anything else — no answer, `404` — means you are not reaching this app at that address.

## Related pages

- [Web Player](Web-Player.md) — play a channel straight in the browser
- [Remote Players](Remote-Players.md) — send channels to VLC or Kodi
- [Configuration](Configuration.md) — every setting mentioned here


## Channels with several streams

Jellyfin and Plex receive one stable URL per TV channel:
`/tuner/channel/<tv-channel-id>.ts`. The HDHomeRun lineup and tuner M3U both use
this URL. Refresh the media server's guide once after upgrading so it picks up
the new links; existing `/tuner/stream/<content-id>.ts` links still play that exact
source without failover.

On each tune, the app reads the channel's active sources whose saved status is
**online**. It tries known measured bitrates from highest to lowest, then sources
whose bitrate is unknown. Equal bitrates use content ID order. Offline, unchecked,
inactive, and malformed source IDs are excluded. If the TV channel is disabled or
has no eligible sources, playback returns `503 NO_ONLINE_STREAMS`.

Refused, empty, timed-out, or otherwise failed starts advance to the next source.
Each source is tried once, with a 15-second attempt deadline and a 45-second overall
startup budget. In-flight blocking engine calls and cleanup may finish after that
deadline before returning. One tuner slot stays reserved across all attempts.
If none starts, the response is `502 CHANNEL_STREAM_FAILED`.

By default the relay copies the original media without FFmpeg or encoding. If a
source ends, errors or stalls for 15 seconds after playback starts, the response
ends. The client must reconnect to the **same stable TV channel URL**. Recently
failed sources are deprioritized for 60 seconds, so working alternatives are tried
first. This failure memory is process-local and bounded; it does not overwrite
verified status results. Enable automatic reconnect in your player where supported.
The server cannot issue an HTTP redirect after sending media, and cannot force a
client to reconnect. Recovery timing therefore depends on the player.

**Integrations → Media servers → Tuner settings → Experimental transcoding recovery**
is off by default and applies to new connections. Enabling it requires FFmpeg and
attempts recovery on the same HTTP connection. Each viewer encodes video to MPEG-2
at 25 fps and audio to stereo AAC, using two video encoder threads. This is CPU
intensive, can overload small servers, increase bandwidth and reduce quality. Use
at your own risk; uninterrupted playback in Plex/Jellyfin is not guaranteed.
Attempts use fresh transport tables, discontinuities and timestamp offsets.
Programme positions are not synchronized. Every source is tried once per 45-second
recovery window; 30 seconds of delivery resets the budget. Exhaustion ends the
response. Disconnecting cancels recovery and cleans up the process/source session.

On **Playlist**, choose **TV channel relay (automatic failover)** or save a format
such as `http://scraper:8000/tuner/channel/{tv_channel_id}.ts`. This generates one
entry per TV channel, preserving its number and EPG ID, and excludes unassigned
streams. `{channel_id}` remains the hash of a specific AceStream source; use
`/tuner/stream/{channel_id}.ts` when deliberately pinning that source.

Successful channel status checks also take a bounded media sample (at most 2 MiB
and 10 seconds including analysis) to estimate encoded bitrate and discover audio
tracks with bundled ffprobe. P2P download speed is never treated as media bitrate.
Existing channels start with unknown metadata; normal status checks populate it.
A failed metadata probe leaves the previous measurement intact and does not turn
an otherwise broadcasting source offline. Measurements are estimates and can age.

The TV relay retains the source's audio tracks, encoding each as stereo AAC; Jellyfin/Plex can discover
them from the media. The channel API also exposes measured bitrate, its timestamp,
and known audio tracks. No database/network work stays attached to an hours-long
relay session.

### Source checks during playback

A GET of `/tuner/channel/{tv_channel_id}.ts` (HDHomeRun, tuner M3U, or a player
opening a stable channel URL) queues a quiet refresh of that channel's active
sources. Already-online sources start immediately. Newly verified alternatives
can join recovery within its 45-second budget, including when
all sources were previously offline. The app checks one channel at a time,
coalesces concurrent requests for that channel, and bounds the queue to 32 channels.
A full queue leaves playback using the currently known sources.

HEAD requests and direct content-ID URLs do not trigger these refreshes. Sources
currently used by an app relay or web player are protected from disruptive probes.
While the TV relay is active, refreshes repeat every 60 seconds and after source
failure. Viewers share the existing bounded refresh queue; active playback ownership
continues to protect sources from disruptive checks. Refreshing never switches away
from a source that is still delivering.

Playlist → **Include unassigned streams at the end** appends matching streams
without a TV channel after assigned channels. It is off by default in the page.
With a TV channel relay format, these entries use `/tuner/stream/<hash>.ts` on
the same relay server and have no channel failover; their numbers start at 9000
(or above the highest included TV number). Search, group and online filters still
apply. Favorites-only excludes unassigned streams. The playlist URL carries
`include_unassigned=true|false`; the all-streams endpoint includes them by default.

# Frequently Asked Questions

## Do I need an AceStream engine?

Not for scraping, organizing channels or generating playlists for clients with their own engine. Browser playback, engine catalogue search and server relays need a playback endpoint. Signal checks need a playback or dedicated checking endpoint. New scraper-only installs leave playback empty; with no engine configured, checks are skipped without changing saved results.

Choose bundled or external services with the [Docker command builder](https://pipepito.github.io/acestream-scraper/). Installed services remain off until enabled.

## What is the difference between a stream and a TV channel?

A stream is one AceStream content ID. A TV channel represents a station and groups primary/backup streams, a number, favorite flag and EPG mapping. **Acestream Channels** manages IDs; **TV Channels** manages stations; **Live TV** displays active stations with attached streams and a separate online-unassigned section.

## What is Acexy, and do I need it?

Acexy proxies engine streams and manages their sharing/cleanup. It is optional: direct engine mode is the app default. Enable the service in Docker, then select **Settings → Playback → Route playback through Acexy** if you want app playback to use it. The backend-facing Acexy URL and the player-facing published address may differ.

This routing applies to new web-player, tuner and remote-player sessions; it does not rewrite every copied or exported link. See [Playback routing](Remote-Players.md#playback-routing).

## Why use a separate checking engine?

It isolates signal checks from playback. Native engine 3.2.11 can stop another viewer of the same source despite different PIDs. The app coordinates its own sessions, but cannot track all players connected directly to the engine. A bundled or external checker avoids sharing that engine, at the cost of additional memory, cache and bandwidth. A failed dedicated checker never falls back to playback.

## Which playlist format should I choose?

| Player/setup | Format |
|---|---|
| One station entry with backup sources through this server | **TV channel relay (automatic failover)**: `/tuner/channel/{tv_channel_id}.ts` |
| One exact stream through this server | **Server relay**: `/tuner/stream/{channel_id}.ts` |
| A client with native AceStream support | **AceStream app**: `acestream://{channel_id}` |
| A player connecting directly to an engine or Acexy | **AceStream direct** or **Acexy**, using a host/port reachable from that player |

Add/select formats in **Playlist → Manage link formats** or **Settings → Stream links**. Default follows the saved default. Unassigned streams can be appended at the end; they have no TV-channel failover. The [walkthrough](Usage.md#step-7-build-the-playlist-url) explains filters and import.

## Does automatic failover mean uninterrupted playback?

No. Default stable TV relays preserve source bytes and close a failed response; the player must reconnect to the same channel URL to try alternatives. Raw stream URLs do not fail over. Experimental transcoding recovery can attempt a source change within one connection, but uses substantial CPU and is client-dependent. See [relay recovery](Media-Servers.md#channels-with-several-streams).

## Why does an online stream fail to play?

Online means the last check observed increasing P2P downloads and verified audio/video media. Broadcasts can stop, peers can disappear and browsers may not support the source's video codec. Catalogue availability and ID lookup are separate from verified signal. Try another stream or VLC/Kodi; see [playback troubleshooting](Troubleshooting.md#playback-will-not-start-or-stops).

## Can I choose another audio language?

Use **Audio track** in the browser player when tracks are detected. Changing audio restarts your viewer; other viewers retain their choices. Different audio selections count as separate sessions. Raw links and remote players retain the source audio tracks and choose audio in their own player.

## Where did the old setup wizard go?

Scraper uses **Settings → Playback / Automation / Stream links / API access**, **Integrations → Public address**, and **Scraper** for source URLs. Values persist in the database; `config/config.json` is no longer read. See [Configuration](Configuration.md).

## How often does automation run?

By default: scraping every 24 hours, EPG refresh every 6 hours, signal checks every 60 minutes. Change them in **Settings → Automation**; they apply immediately. **Overview → Scheduled jobs** retains launch times/results after restart and marks unfinished runs interrupted. Playback can also queue source checks.

## How do I reorder stations or hide a stream?

Edit **Number** on TV Channels and press Enter or leave the field; blank clears it. **Reorder channels** previews the complete catalogue with drag handles and keyboard/arrow controls, then saves consecutive numbers atomically. Cancel preserves the stored order. Favorites and advanced filters are separate controls.

Hide a stream through its Acestream Channels row actions to exclude it from generated playlists while retaining its record. See [Channel management](tasks/channel-management.md).

## How do I update without losing data?

Persist `/app/config`, back it up, keep the image tag/digest, and recreate with the same mounts:

```bash
docker compose pull
docker compose up -d
```

Also retain enabled service state/cache and optionally logs. Schema upgrades take a database backup before applying changes; rollback needs the matching old database, not just an older image. See [Installation](Installation.md#updating-to-a-newer-image). `develop` tags move after validation; `latest` changes only on explicit release promotion.

## Does it work on ARM?

The Docker images cover amd64, arm64 and arm/v7. Both ARM engine variants use the pinned community Android 3.2.17 distribution; ARMv7 remains experimental and requires real-hardware runtime validation. ARM engine playback is not promised by a successful image build. Raspberry Pi 5 needs a 4 KB page-size kernel for this engine. WARP/IPFS are unavailable in ARMv7 images; bundled ZeroNet is amd64-only. External gateways remain usable. See [Docker platforms](Docker.md).

## Do I need to expose the engine port?

Only for clients connecting to it directly. Browser playback and server relays use the scraper web port; the backend reaches the engine internally. Engine/Acexy APIs have no authentication and belong on trusted networks. `/tuner/*` uses an address allowlist, not `API_TOKEN`. Set the public address in Integrations and read [network configuration](Configuration.md#media-integrations).

## How do I enable WARP or troubleshoot IPFS/ZeroNet?

Use the builder's feature selection and the WARP page under System. Availability depends on architecture. See [optional-service troubleshooting](Troubleshooting.md#scraper-or-optional-service-fails) for runtime flags, gateway routing and connection checks.

## How can I get help or contribute?

Start with [Troubleshooting](Troubleshooting.md). For unresolved problems, [collect diagnostics and open a bug report](Bug-Reporting.md). For extraction improvements, read [Contributing Scraper Data](Contributing-Scraper-Data.md). Use sources you have permission to access; availability in a catalogue does not establish permission to view or redistribute a broadcast.

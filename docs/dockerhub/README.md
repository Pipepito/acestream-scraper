# Acestream Ids Scraper

A self-hosted web app for discovering AceStream streams, organizing TV channels, and watching or sharing your catalogue.

**[Docker command builder](https://pipepito.github.io/acestream-scraper/)** · [Docs](https://github.com/Pipepito/acestream-scraper/wiki) · [Source code](https://github.com/Pipepito/acestream-scraper)

![Live TV and programme guide](https://raw.githubusercontent.com/Pipepito/acestream-scraper/main/wiki/usage-09-live-tv.png)

## Features

- Import sources from web pages, playlists, JSON, text, ZeroNet, and IPFS.
- Create per-source extraction recipes using HTML selectors, regular expressions, or JSON field mappings, with a starter catalogue and result previews.
- Organize channels with numbers, categories, favorites, and programme guides.
- Watch Live TV in your browser, including stream and audio selection.
- Export M3U playlists, control VLC/Kodi, or connect Jellyfin/Plex.
- Schedule refreshes, check stream signal, and review service and job history.
- Inspect the latest measured peer count, transfer rates, and media bitrate.
- View container data directories and mounts, disk usage, and free filesystem space in Overview.

Scraping and playlist management work without an engine. Browser playback requires a configured playback engine. Choose optional bundled services or connect external ones.

## Get started

Use the **[Docker command builder](https://pipepito.github.io/acestream-scraper/)** for a ready-to-copy Docker command or Compose file with the right ports, persistent storage, and enabled services.

Follow the [installation guide](https://github.com/Pipepito/acestream-scraper/wiki/Installation), then the [first-run walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage). Persist `/app/config` to keep your catalogue and settings across container updates.

## Add your own sources

Open **Scraper → Extraction builder** to fetch a website or API response, select the channel name and AceStream ID fields, and test your extraction before saving it to a source. Use HTML selectors, record-based regular expressions, or JSON paths; optional fields include group, logo, and EPG ID.

The [user tools page](https://pipepito.github.io/acestream-scraper/) combines **Docker setup**, **Extraction builder**, and **Docs**. Its standalone builder accepts pasted or uploaded samples and exports recipes for your own installation, without exposing your scraper to the internet. Start with an editable catalogue example or create a recipe from scratch. Sources without a recipe retain automatic extraction.

The preview uses sanitized HTML; it cannot run website scripts or reproduce logins and live interactions. Raw text and manual JSON mappings provide fallbacks. Follow the [extraction recipe docs](https://github.com/Pipepito/acestream-scraper/wiki/Extraction-Recipes) for the workflow and limits.

## Stream and storage visibility

Stream checks record the latest available peer count, P2P download/upload rates, and media bitrate, with observation times. These are individual samples, not a historical chart. See [stream statistics](https://github.com/Pipepito/acestream-scraper/wiki/Stream-Statistics).

Overview shows configured data directories and discovered container mount paths, their measured usage, and free/total filesystem space. Shared filesystem space is not a per-directory quota, and host-side bind paths are not exposed. See [storage](https://github.com/Pipepito/acestream-scraper/wiki/Storage).

Existing installations can keep their legacy environment variable names. The app warns which names to update; explicitly configured replacement names take precedence. See [configuration](https://github.com/Pipepito/acestream-scraper/wiki/Configuration).

## What's included in `latest`?

`pipepito/acestream-scraper:latest` is the full image: the web app and its optional companion software in one container.

| Software | What it does | With default settings |
|---|---|---|
| **Scraper web app** | Sources, TV channels, programme guides, playlists, and integrations | Starts automatically |
| **FFmpeg and ffprobe** | Prepare browser playback and inspect stream media | Used when needed |
| **AceStream Engine** | Connect to AceStream streams for playback and signal checks | Off until enabled |
| **Acexy** | Provide an HTTP proxy for AceStream playback | Off until enabled |
| **Cloudflare WARP** | Route outbound traffic through WARP | Off until enabled |
| **IPFS (Kubo)** | Fetch sources from IPFS and IPNS | Off until enabled |
| **ZeroNet and Tor** | Fetch sources through a local ZeroNet node, with optional Tor | Off until enabled |

**Included does not mean running.** With no service options set, `latest` starts the web app; the engine, proxy, and other optional services stay off. Enable the ones you want in the [Docker command builder](https://pipepito.github.io/acestream-scraper/). Browser playback needs a bundled or external playback engine.

WARP, Kubo, ZeroNet, and Tor are bundled on **amd64 and arm64**. The app, FFmpeg, and the relevant engine/proxy variants also cover **arm/v7**, where bundled AceStream remains experimental. See [platform requirements](https://github.com/Pipepito/acestream-scraper/wiki/Requirements) for details.

## Choose your image

All tags below use the `pipepito/acestream-scraper` repository. Choose a smaller variant if you already run your own engine or don't need the proxy.

| Image tag | AceStream included | Acexy included | Best fit |
|---|---|---|---|
| **`latest`** | Yes | Yes | Full package for the current release |
| `scraper-acestream-acexy` | Yes | Yes | Explicit name for the same full package |
| `scraper-acestream` | Yes | No | Bundled engine, without Acexy |
| `scraper-acexy` | No | Yes | Acexy connected to your external engine |
| `scraper` | No | No | Scraping and playlists, or your own playback services |

**Every variant keeps the web app and FFmpeg**, plus WARP, Kubo, ZeroNet, and Tor on supported platforms. Changing the image selects which software is installed; the command builder selects which services start.

Use `latest` for the current release, `vX.Y.Z` or `vX.Y.Z-<flavor>` to pin a release, and `develop` or `develop-<flavor>` to try changes for the next one. See the [full image guide](https://github.com/Pipepito/acestream-scraper/wiki/Docker#image-tags-and-flavors) for setup details.

## Your channel catalogue

Organize stations, channel numbers, and favorites before watching or sharing a playlist.

![TV channel management](https://raw.githubusercontent.com/Pipepito/acestream-scraper/main/wiki/usage-04-tv-channels.png)

## Docs and support

[Configuration](https://github.com/Pipepito/acestream-scraper/wiki/Configuration) · [Storage](https://github.com/Pipepito/acestream-scraper/wiki/Storage) · [Troubleshooting](https://github.com/Pipepito/acestream-scraper/wiki/Troubleshooting) · [Report a bug](https://github.com/Pipepito/acestream-scraper/wiki/Bug-Reporting)

[Source code and MIT license](https://github.com/Pipepito/acestream-scraper) · [Full wiki](https://github.com/Pipepito/acestream-scraper/wiki)

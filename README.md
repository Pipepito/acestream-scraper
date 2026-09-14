# Acestream Ids Scraper

Discover AceStream streams, organize your TV channels, and watch or share them with your favorite players — all from a self-hosted web app.

Scraper brings sources, programme guides, playlists, and playback together. Import links from web pages, playlists, JSON, text, ZeroNet, or IPFS, then turn them into a catalogue you can browse and maintain.

**[Get started](https://pipepito.github.io/acestream-scraper/)** · [Docker Hub](https://hub.docker.com/r/pipepito/acestream-scraper) · [User guides](https://github.com/Pipepito/acestream-scraper/wiki)

![Live TV with the channel catalogue and programme guide](wiki/usage-09-live-tv.png)

*See what's on, pick a stream, and watch from your browser.*

## What you can do

- **Find and organize channels.** Collect AceStream IDs from multiple sources, match them to TV stations, and manage names, numbers, categories, favorites, and channel order.
- **See what's on.** Import XMLTV programme guides and browse current and upcoming shows alongside your channels.
- **Watch in the browser.** Open Live TV, switch between available streams and audio tracks, or keep browsing while a channel plays.
- **Use the players you already have.** Generate M3U playlists, send channels to VLC or Kodi, or connect your catalogue to Jellyfin and Plex.
- **Keep your catalogue up to date.** Schedule source and guide refreshes, verify stream signal, and review job history and service health.
- **Choose your setup.** Use optional bundled services or connect your own AceStream engine, Acexy proxy, ZeroNet node, or IPFS gateway.

An engine is optional for scraping and playlist management. In-app playback needs a configured playback engine; signal checks need a playback or checking engine.

## Get started

Use the **[Docker command builder](https://pipepito.github.io/acestream-scraper/)** to generate a command or Compose file for your machine, then follow the **[installation guide](https://github.com/Pipepito/acestream-scraper/wiki/Installation)** and **[first-run walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage)**.

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

## A look inside

**Your channels, in your order.** Match streams to stations, choose favorites, and organize the catalogue you share with your players.

![TV channel management with channel numbers, favorites, and filters](wiki/usage-04-tv-channels.png)

### Service dashboard

Check service health, control the engines, and review scheduled jobs from one place.

![Overview with service health, engine controls, and scheduled jobs](wiki/usage-01-overview.png)

This example has optional services enabled. Your dashboard shows which components are installed, enabled, and running in your own setup.

The [illustrated walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage) covers importing sources, adding programme guides, and creating your first playlist.

## Explore the guides

| I want to… | Guide |
|---|---|
| Install, update, or migrate from v1 | [Installation and upgrades](https://github.com/Pipepito/acestream-scraper/wiki/Installation) |
| Choose services, ports, and storage | [Docker](https://github.com/Pipepito/acestream-scraper/wiki/Docker) · [Requirements](https://github.com/Pipepito/acestream-scraper/wiki/Requirements) |
| Manage channels, guides, and playlists | [Walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage) |
| Watch in the browser | [Live TV and web player](https://github.com/Pipepito/acestream-scraper/wiki/Web-Player) |
| Use VLC, Kodi, Jellyfin, or Plex | [Remote players](https://github.com/Pipepito/acestream-scraper/wiki/Remote-Players) · [Media servers](https://github.com/Pipepito/acestream-scraper/wiki/Media-Servers) |
| Configure playback and automation | [Configuration](https://github.com/Pipepito/acestream-scraper/wiki/Configuration) |
| Solve a problem or report a bug | [Troubleshooting](https://github.com/Pipepito/acestream-scraper/wiki/Troubleshooting) · [Bug reporting](https://github.com/Pipepito/acestream-scraper/wiki/Bug-Reporting) |

## Contribute

Found a bug or have an idea? [Open an issue](https://github.com/Pipepito/acestream-scraper/issues). To help with source formats, see [contributing scraper data](https://github.com/Pipepito/acestream-scraper/wiki/Contributing-Scraper-Data).

For code contributions, start with the [development guide](https://github.com/Pipepito/acestream-scraper/wiki/Development) and [technical documentation](docs/README.md). Pull requests target `develop`.

Licensed under MIT.

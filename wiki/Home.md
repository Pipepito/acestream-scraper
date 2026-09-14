# Acestream Ids Scraper guides

Discover streams, organize your TV catalogue, and watch in the browser or through your own players. These guides take you from installation to everyday use.

Use `latest` for the current release. The moving `develop` channel is for testing changes for the next release.

## Start here

1. Generate a command or Compose file with the [Docker command builder](https://pipepito.github.io/acestream-scraper/).
2. Follow [Installation](Installation.md), including persistent storage and upgrade guidance.
3. Open the [illustrated walkthrough](Usage.md) to import sources, add programme guides, and start watching.

![Live TV and programme guide](usage-09-live-tv.png)

## Help by task

| I want to… | Open |
|---|---|
| Install, choose optional services or upgrade from v1 | [Installation](Installation.md), [Docker](Docker.md) |
| Watch and choose streams/audio | [Live TV and Web Player](Web-Player.md) |
| Assign IDs, number stations and reorder the catalogue | [Channel management](tasks/channel-management.md) |
| Publish a playlist with backup streams | [Playlist walkthrough](Usage.md#step-7-build-the-playlist-url) |
| Use VLC/Kodi or Jellyfin/Plex | [Remote Players](Remote-Players.md), [Media Servers](Media-Servers.md) |
| Configure a separate checker or schedules | [Configuration](Configuration.md#application-settings) |
| Fix playback, guide, source or startup problems | [Troubleshooting](Troubleshooting.md) |
| Collect evidence for an issue | [Bug Reporting](Bug-Reporting.md) |

Engines are optional for scraping and playlist management. A playback endpoint is needed for browser viewing, engine search and server relays. Status checks can use a dedicated engine; a configured checker outage never falls back to playback.

## More resources

- [Configuration reference](Configuration.md) — saved settings, environment variables, ports, and volumes.
- [Docker guide](Docker.md) and [requirements](Requirements.md) — image choices, optional services, and storage.
- [Development](Development.md) — local setup, checks, and code contributions.
- [Contributing scraper data](Contributing-Scraper-Data.md) — help support source formats.
- [Project and license](https://github.com/Pipepito/acestream-scraper) · [Docker Hub](https://hub.docker.com/r/pipepito/acestream-scraper) · [Issues](https://github.com/Pipepito/acestream-scraper/issues).

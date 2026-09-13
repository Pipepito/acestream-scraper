# Acestream Ids Scraper

## Project Overview

Acestream Ids Scraper is a Python-based web application that automatically retrieves Acestream channel information from various sources and generates M3U playlists that can be used with any media player supporting the Acestream protocol.

Built on a FastAPI + SQLAlchemy + BeautifulSoup backend with a React + Material UI front end, this application provides a comprehensive solution for managing and accessing Acestream channels through an intuitive web interface.

## Start Here

1. Open the [Docker command builder](https://pipepito.github.io/acestream-scraper/) to generate the right command or Compose file for your CPU, image flavor, ports, and optional services.
2. Read the [Installation Guide](Installation.md) and start the container.
3. Follow the illustrated [Usage Guide](Usage.md) from first launch through playlist import.
4. Use the [project README](https://github.com/Pipepito/acestream-scraper#readme) for the release overview, supported platforms, development setup, and links to operator documentation.

![Acestream Ids Scraper Overview](usage-01-overview.png)

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

These guides cover Acestream Ids Scraper. Version 2 updates the codebase while preserving its core scraping and playlist functionality. Select the moving **develop** image channel to test the upcoming release; **latest** changes only on explicit release promotion.

## Key Features

- **Automated Channel Discovery**: Scrapes Acestream channel information from multiple URLs
- **Multiple Format Support**: Extracts data from both JSON and HTML content
- **M3U Playlist Generation**: Creates playlists compatible with popular media players
- **On-Demand Updates**: Refreshes channel data when needed
- **Web Interface**: User-friendly dashboard for managing channels and configuration
- **ZeroNet Support**: Can scrape content from ZeroNet sites
- **IPFS Support**: Can scrape `ipfs://` / `ipns://` content through a bundled Kubo daemon or any IPFS gateway
- **Database Management**: Complete with migration support
- **Built-in Acestream Integration**: Optional integrated Acestream engine with Acexy proxy
- **External Acestream Support**: Connect to existing Acestream Engine instances
- **Live TV and Web Player**: Browse programmes and watch compatible streams in the browser; choose alternatives and audio tracks
- **Remote Players**: Send channels to VLC or Kodi elsewhere on your network and control playback from the app
- **Jellyfin and Plex**: Publish your channels as an HDHomeRun tuner with a full XMLTV guide, so they appear in the media server you already use
- **Cloudflare WARP Integration**: Optional outbound tunnel with connection controls
- **Verified Signal Checks**: Distinguish engine ID lookup from observed audio/video delivery, with optional dedicated checker isolation
- **In-App Configuration**: Manage engine, link formats, automation, API access, and sources from the web interface
- **Search Functionality**: Find specific channels quickly
- **Automatic Rescanning**: Configure intervals for automatic updates
- **API Documentation**: OpenAPI/Swagger UI for developers
- **Health Monitoring**: Comprehensive system health checks

## Architecture

The application follows a service-oriented architecture with:

- Repository pattern for data access
- Service layer for business logic
- Migrations support for database changes
- Async task management
- Clear separation of concerns
- Integration with external services (Acestream, Acexy, ZeroNet, IPFS)

## Wiki Navigation

- [Docker Command Builder](https://pipepito.github.io/acestream-scraper/) - Generate the exact `docker run` command or `docker-compose.yml` for your setup
- [Project README](https://github.com/Pipepito/acestream-scraper#readme) - project overview, quick start, platform support and contributor entry points
- [Installation Guide](Installation.md) - How to install and set up the application
- [Docker Guide](Docker.md) - Learn about Docker and how it works with this app
- [Usage Guide](Usage.md) - How to use the application's features
- [Web Player](Web-Player.md) - Play a channel straight in the browser
- [Remote Players](Remote-Players.md) - Send channels to VLC or Kodi on your network and control them from the app
- [Media Servers](Media-Servers.md) - Watch your channels in Jellyfin or Plex, with a full guide
- [Configuration Reference](Configuration.md) - Detailed configuration information
- [Requirements](Requirements.md) - System and software requirements
- [FAQ](FAQ.md) - Frequently asked questions
- [Troubleshooting](Troubleshooting.md) - Diagnose playback, sources, guide and startup failures
- [Bug Reporting](Bug-Reporting.md) - Collect and share useful diagnostics

## License

This project is licensed under the MIT License.

## Acknowledgements

Special thanks to the developers of FastAPI, SQLAlchemy, BeautifulSoup, React, Material UI, and other dependencies used in this project.

- [Acexy](https://github.com/Javinator9889/acexy) - Enhanced Acestream proxy interface
- [Acestream-http-proxy](https://github.com/martinbjeldbak/acestream-http-proxy) - HTTP proxy for Acestream

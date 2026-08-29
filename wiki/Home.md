# Acestream Scraper

## Project Overview

Acestream Scraper is a Python-based web application that automatically retrieves Acestream channel information from various sources and generates M3U playlists that can be used with any media player supporting the Acestream protocol.

Built on a FastAPI + SQLAlchemy + BeautifulSoup backend with a React + Material UI front end, this application provides a comprehensive solution for managing and accessing Acestream channels through an intuitive web interface.

Continuous integration (pull-request validation and Docker image releases) runs on the project's Jenkins controller; the GitHub Actions workflows and their status badge were retired on 2026-08-26.

## Key Features

- **Automated Channel Discovery**: Scrapes Acestream channel information from multiple URLs
- **Multiple Format Support**: Extracts data from both JSON and HTML content
- **M3U Playlist Generation**: Creates playlists compatible with popular media players
- **On-Demand Updates**: Refreshes channel data when needed
- **Web Interface**: User-friendly dashboard for managing channels and configuration
- **ZeroNet Support**: Can scrape content from ZeroNet sites
- **Database Management**: Complete with migration support
- **Built-in Acestream Integration**: Optional integrated Acestream engine with Acexy proxy
- **External Acestream Support**: Connect to existing Acestream Engine instances
- **Cloudflare WARP Integration**: Enhanced privacy and geo-unblocking capabilities
- **Channel Status Monitoring**: Check which channels are online or offline
- **Interactive Setup**: Easy configuration through a setup wizard
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
- Integration with external services (Acestream, Acexy, ZeroNet)

## Wiki Navigation

- [Docker Command Builder](https://pipepito.github.io/acestream-scraper/) - Generate the exact `docker run` command or `docker-compose.yml` for your setup
- [Installation Guide](Installation.md) - How to install and set up the application
- [Docker Guide](Docker.md) - Learn about Docker and how it works with this app
- [Usage Guide](Usage.md) - How to use the application's features
- [Configuration Reference](Configuration.md) - Detailed configuration information
- [Requirements](Requirements.md) - System and software requirements
- [FAQ](FAQ.md) - Frequently asked questions

## License

This project is licensed under the MIT License.

## Acknowledgements

Special thanks to the developers of FastAPI, SQLAlchemy, BeautifulSoup, React, Material UI, and other dependencies used in this project.

- [Acexy](https://github.com/Javinator9889/acexy) - Enhanced Acestream proxy interface
- [Acestream-http-proxy](https://github.com/martinbjeldbak/acestream-http-proxy) - HTTP proxy for Acestream

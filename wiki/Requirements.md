# Requirements

This page outlines the requirements for running Acestream Scraper.

## System Requirements

### Hardware Requirements

Minimum specifications for running Acestream Scraper:

| Component | Minimum | Recommended |
|-----------|---------|------------|
| CPU | 1 core | 2+ cores |
| RAM | 512MB | 1GB+ |
| Storage | 1GB | 5GB+ |
| Network | 10 Mbps | 100+ Mbps |

### Operating System Support

Acestream Scraper can run on any system that supports Docker:

- **Linux**: All major distributions (Ubuntu, Debian, CentOS, Fedora, etc.)
- **macOS**: 10.14 (Mojave) or newer
- **Windows**: Windows 10/11 with Docker Desktop

For manual installation (without Docker), a Linux-compatible environment is recommended.

## Software Requirements

### Docker Installation

If using Docker (recommended approach):

- **Docker**: Version 19.03 or newer
- **Docker Compose**: Version 1.27.0 or newer (if using docker-compose)

### Manual Installation

If installing directly on the host:

- **Python**: 3.10 or higher
- **pip**: Latest version
- **Git**: For cloning the repository (optional)
- **Virtual Environment**: Recommended for isolation

### External Dependencies

These may be needed depending on your configuration:

- **Acestream Engine**: If not using the built-in engine
- **ZeroNet**: Built-in, but requires connection to ZeroNet network
- **Tor**: Optional, for anonymous ZeroNet connections

## Network Requirements

### Ports

The following ports need to be available on your system:

| Port | Service | Required |
|------|---------|----------|
| 8000 | Web interface | Yes |
| 8080 | Acexy proxy | Only if enabled |
| 6878 | Acestream Engine | Only if built-in engine is enabled |
| 43110 | ZeroNet Web UI | Only if using ZeroNet |
| 43111 | ZeroNet transport | Only if using ZeroNet |
| 26552 | ZeroNet peer | Only if using ZeroNet |
| 8621 | Acestream P2P | Only if built-in engine is enabled |

### Connectivity

- **Internet connection**: Required for scraping URLs and connecting to Acestream network
- **Firewall rules**: Allow outbound connections for Acestream P2P functionality
- **Port forwarding**: May be required for optimal Acestream Engine performance

## Browser Support

The web interface is compatible with:

- **Chrome/Chromium**: Version 90+
- **Firefox**: Version 90+
- **Safari**: Version 14+
- **Edge**: Version 90+

## Media Player Requirements

To use the generated playlists:

### Direct Acestream Protocol

If using `acestream://` URLs:
- Acestream Engine installed locally
- Media player with Acestream protocol support or appropriate plugin

### HTTP Streaming

If using HTTP URLs:
- Any media player supporting M3U playlists and HTTP streams (VLC, Kodi, etc.)
- Network access to the Acestream Engine (local or remote)

## Storage Requirements

- **Database**: SQLite database grows based on number of channels (typically <50MB)
- **ZeroNet data**: Can grow to several GB if using ZeroNet extensively
- **Logs**: Rotation enabled, typically <100MB

## Development Requirements

Additional requirements for development work:

- **Python development tools**: python-dev, build-essential
- **Testing tools**: pytest, coverage
- **Code quality tools**: flake8, black, isort

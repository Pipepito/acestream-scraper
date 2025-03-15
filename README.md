# Acestream Scraper

A Python-based web scraping application that retrieves Acestream channel information and generates M3U playlists. Built using Flask, BeautifulSoup, and SQLAlchemy.

[![Release Pipeline](https://github.com/Pipepito/acestream-scraper/actions/workflows/release.yml/badge.svg)](https://github.com/Pipepito/acestream-scraper/actions/workflows/release.yml)

## Features

- Scrapes Acestream channel information from multiple URLs
- Extracts channel names and URLs from both JSON data and HTML content
- Generates M3U playlists with optional refresh
- Refreshes channel data on demand
- Displays channel metadata via web interface
- Supports ZeroNet URLs
- Database migrations support
- Service-oriented architecture
- Repository pattern for data access
- **Built-in Acestream engine with Acexy proxy (optional)**
- **Support for external Acestream Engine instances**
- Channel status checking
- Acexy status display in the dashboard
- **Interactive setup wizard for easy configuration**
- **Channel search functionality**
- **Automatic rescraping at configurable intervals**
- **API documentation via OpenAPI/Swagger UI**
- **Enhanced health checking for all components**

# [Detailed Wiki](https://github.com/Pipepito/acestream-scraper/wiki)

## Quick Start

### Using Docker Compose (Easiest Method)

1. **Create a docker-compose.yml file:**

   ```yaml
   version: '3.8'

   services:
     acestream-scraper:
       image: pipepito/acestream-scraper:latest
       container_name: acestream-scraper
       environment:
         - TZ=Europe/Madrid
         - ENABLE_TOR=false
         - ENABLE_ACEXY=true
         - ENABLE_ACESTREAM_ENGINE=true
         - ACESTREAM_HTTP_PORT=6878
         - FLASK_PORT=8000
         - ACEXY_LISTEN_ADDR=:8080
         - ACEXY_HOST=localhost
         - ACEXY_PORT=6878
         - ALLOW_REMOTE_ACCESS=no
         - ACEXY_NO_RESPONSE_TIMEOUT=15s
         - ACEXY_BUFFER_SIZE=5MiB
         - ACESTREAM_HTTP_HOST=localhost
       ports:
         - "8000:8000"  # Flask application
         - "8080:8080"  # Acexy proxy
         - "8621:8621"  # Acestream P2P Port
         - "43110:43110"  # ZeroNet UI
         - "43111:43111"  # ZeroNet peer
         - "26552:26552"  # ZeroNet peer
       volumes:
         - ./data/zeronet:/app/ZeroNet/data
         - ./data/config:/app/config
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "/app/healthcheck.sh"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 60s
   ```

2. **Start the service:**

   ```bash
   docker-compose up -d
   ```

3. **Access the application at `http://localhost:8000`**

### Using Docker (Alternative)

[Image in Docker Hub](https://hub.docker.com/r/pipepito/acestream-scraper)

1. **Pull and run the container:**

   ```bash
   docker pull pipepito/acestream-scraper:latest
   docker run -d \
     -p 8000:8000 \
     -v "${PWD}/config:/app/config" \
     --name acestream-scraper \
     pipepito/acestream-scraper:latest
   ```

2. **Access the setup wizard:**
   
   Open your browser and navigate to `http://localhost:8000`
   
   The first-time setup wizard will guide you through configuration:
   - Base URL format (acestream:// or http://)
   - Acestream Engine settings
   - Source URLs to scrape
   - Rescrape interval

3. **Alternative: Manual configuration**

   Create a `config/config.json` file:

   ```json
   {
       "urls": [
           "https://example.com/url1",
           "https://example.com/url2"
       ],
       "base_url": "http://127.0.0.1:8008/ace/getstream?id=",
       "ace_engine_url": "http://127.0.0.1:6878"
   }
   ```

### Running with Acexy and Internal Acestream Engine

The image includes an embedded Acestream engine with the Acexy proxy interface, which provides a user-friendly web UI:

```bash
docker run -d \
  -p 8000:8000 \
  -p 8080:8080 \
  -e ENABLE_ACEXY=true \
  -e ENABLE_ACESTREAM_ENGINE=true \
  -e ALLOW_REMOTE_ACCESS=yes \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

Acexy only exposes an status endpoint available at `http://localhost:8080/ace/status`.

### Using with External Acestream Engine

You can connect the Acexy proxy to an external Acestream Engine instance:

```bash
docker run -d \
  -p 8000:8000 \
  -p 8080:8080 \
  -e ENABLE_ACEXY=true \
  -e ENABLE_ACESTREAM_ENGINE=false \
  -e ACEXY_HOST=192.168.1.100 \
  -e ACEXY_PORT=6878 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### Using with ZeroNet

The application can scrape ZeroNet sites for channel information:

#### Running with TOR disabled

```bash
docker run -d \
  -p 8000:8000 \
  -p 43110:43110 \
  -p 43111:43111 \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/zeronet_data:/app/ZeroNet/data" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

#### Running with TOR enabled

```bash
docker run -d \
  -p 8000:8000 \
  -p 43110:43110 \
  -p 43111:43111 \
  -e ENABLE_TOR=true \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/zeronet_data:/app/ZeroNet/data" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### Manual Installation

1. **Prerequisites:**
   - Python 3.10 or higher
   - pip

2. **Setup:**

   ```bash
   git clone https://github.com/Pipepito/acestream-scraper.git
   cd acestream-scraper
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create config and run:**

   ```bash
   mkdir -p config
   # Create config/config.json as shown above
   python run_dev.py  # For development
   # or
   python wsgi.py     # For production
   ```

## Usage Guide

### Web Interface

Access the web interface at `http://localhost:8000`

![image](https://github.com/user-attachments/assets/17e000b7-20de-4a80-a990-9d0d5b225754)
![image](https://github.com/user-attachments/assets/17006755-43ff-4817-be2c-36397cf9631b)

#### Dashboard

The main dashboard provides:
- Channel statistics (total, online, offline)
- Search functionality for channels
- Download playlist button
- Add/delete channels
- URL management
- Configuration options

#### Channel Management

- **Adding channels**: Enter a channel ID and name in the form
- **Searching**: Use the search box to filter channels by name
- **Status checking**: Click the "Check Status" button to verify if a channel is online
- **Delete channels**: Remove unwanted channels with the delete button

#### URL Management

- **Add new URLs**: Enter URLs to scrape in the "Add New URL" form
- **Refresh URLs**: Update channel data by clicking "Refresh" on a URL
- **Enable/Disable URLs**: Toggle URLs on/off without deleting them
- **Delete URLs**: Remove URLs you no longer want to scrape

### M3U Playlist

Get the M3U playlist for your media player:

- Current playlist: `http://localhost:8000/playlist.m3u`
- Force refresh: `http://localhost:8000/playlist.m3u?refresh=true`
- Search channels: `http://localhost:8000/playlist.m3u?search=sports`

To use in your media player (like VLC):
1. Copy the playlist URL (http://localhost:8000/playlist.m3u)
2. In your media player, select "Open Network Stream" or similar option
3. Paste the URL and play

**URL Formatting Note:**
- When using Acexy proxy (port 8080), stream URLs are formatted as `{base_url}{channel_id}`
- For all other configurations, `&pid={local_id}` is automatically appended to each stream URL: `{base_url}{channel_id}&pid={local_id}`
- This ensures proper channel identification in various player environments

### API Documentation

The application provides OpenAPI/Swagger documentation:

- Access at: `http://localhost:8000/api/docs`
- Interactive API documentation for developers
- Test endpoints directly from the browser

### Acexy Interface

If you enabled Acexy (recommended):

- Access the Acexy interface at: `http://localhost:8080`
- Check Acexy status directly in the main dashboard
- Manage your Acestream connections through a user-friendly web interface

## Configuration

### Application Settings

Configure through the setup wizard or directly in `config.json`:

- `urls`: Array of URLs to scrape for Acestream channels
- `base_url`: Base URL format for playlist generation (e.g., `acestream://` or `http://localhost:6878/ace/getstream?id=`)
- `ace_engine_url`: URL of your Acestream Engine instance (default: `http://127.0.0.1:6878`)
- `rescrape_interval`: How often to refresh URLs (in hours, default: 24)

### Environment Variables

#### Core Application

- `FLASK_PORT`: Port the Flask application runs on (default: `8000`)

#### Acestream Configuration

- `ENABLE_ACESTREAM_ENGINE`: Enable built-in Acestream Engine (default: matches `ENABLE_ACEXY`)
- `ACESTREAM_HTTP_PORT`: Port for Acestream engine (default: `6878`)
- `ACESTREAM_HTTP_HOST`: Host for Acestream engine (default: uses value of `ACEXY_HOST`)

#### Acexy Configuration

Acexy provides an enhanced proxy interface for Acestream, with a web UI for better management:

- `ENABLE_ACEXY`: Set to `true` to enable Acexy proxy (default: `false`)
- `ACEXY_LISTEN_ADDR`: Address for Acexy to listen on (default: `:8080`)
- `ACEXY_HOST`: Hostname of the Acestream Engine to connect to (default: `localhost`)
- `ACEXY_PORT`: Port of the Acestream Engine to connect to (default: `6878`)
- `ALLOW_REMOTE_ACCESS`: Set to `yes` to allow external connections (default: `no`)
- `ACEXY_NO_RESPONSE_TIMEOUT`: Timeout for Acestream responses (default: `15s`)
- `ACEXY_BUFFER_SIZE`: Buffer size for data transfers (default: `5MiB`)

#### Other Settings

- `ENABLE_TOR`: Enable TOR for ZeroNet connections (default: `false`)
- `TZ`: Timezone for the container (default: `Europe/Madrid`)

### Channel Status Checking

The application verifies if channels are available:

- Shows which channels are online/offline in the dashboard
- Click "Check Status" button to verify individual channels
- Status history and error messages displayed in the UI

To use this feature:

1. Ensure you have Acestream Engine running (built-in if ENABLE_ACESTREAM_ENGINE=true)
2. Configure `ace_engine_url` to point to your Acestream Engine instance
3. Use the "Check Status" buttons in the UI to verify channel availability

### Port Mapping

- `8000`: Main web interface (configurable via `FLASK_PORT`)
- `43110`: ZeroNet web interface (if ZeroNet enabled)
- `43111`: ZeroNet transport port (if ZeroNet enabled)
- `8080`: Acexy web interface (if enabled)
- `6878`: Acestream HTTP API port (configurable via `ACESTREAM_HTTP_PORT`)
- `26552`: Additional ZeroNet peer port

### Volumes

When using Docker, mount these volumes:

- `/app/config`: Configuration files
- `/app/ZeroNet/data`: ZeroNet data directory (if using ZeroNet)

### ZeroNet Configuration

The application looks for a `zeronet.conf` file in the `/app/config` directory. If none exists, it creates one with default values:

```bash
[global]
ui_ip = *
ui_host =
 0.0.0.0
 localhost
ui_port = 43110
```

To customize ZeroNet access:

1. Create your own `config/zeronet.conf`:

```bash
[global]
ui_ip = *
ui_host =
 127.0.0.1
 your.domain.com
 localhost:43110
ui_port = 43110
```

2. Mount it when running the container:

```bash
docker run -d \
  -p 8000:8000 \
  -p 43110:43110 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### Running Behind a Reverse Proxy

The application includes proper headers handling for running behind a reverse proxy:

- Automatic handling of SSL/TLS termination
- Correct handling of X-Forwarded-Proto and X-Forwarded-Host headers
- Works with nginx, Apache, Traefik or other reverse proxies

### Security Note

- Add your domain(s) to `ui_host` for public access
- Always include `localhost` for local access
- Set `ALLOW_REMOTE_ACCESS=no` to restrict Acestream access to localhost only

### Healthchecks

The container includes comprehensive health checking:

- Main application health check at `/health` endpoint providing detailed status
- Acexy health check (if enabled)
- Acestream Engine health check (if enabled)
- Automatic monitoring of internal services
- Graceful handling of service dependencies

### Development

For development, use `run_dev.py` which provides:

- Debug mode
- Auto-reloading
- Windows compatibility

## Architecture

The application follows a service-oriented architecture with:

- Repository pattern for data access
- Service layer for business logic
- Migrations support for database changes
- Async task management
- Clear separation of concerns
- Integration with external services (Acestream, Acexy, ZeroNet)

## Testing

### Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_repositories.py

# Run with coverage report
pytest --cov=app tests/
```

### Test Structure

- `tests/unit`: Unit tests for individual components
- `tests/integration`: Integration tests for API endpoints
- `tests/conftest.py`: Test fixtures and configuration

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

Special thanks to the developers of Flask, BeautifulSoup, SQLAlchemy, and other dependencies used in this project.

- [Acexy](https://github.com/Javinator9889/acexy) - Enhanced Acestream proxy interface
- [Acestream-http-proxy](https://github.com/martinbjeldbak/acestream-http-proxy) - HTTP proxy for Acestream

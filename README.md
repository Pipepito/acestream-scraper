# Acestream Scraper

Acestream Scraper is a Python-based web scraping application that retrieves Acestream channel information and generates M3U playlists. The application is built using Flask, BeautifulSoup, SQLAlchemy, and can be run locally or inside a Docker container.

## Features

- Scrapes Acestream channel information from multiple URLs.
- Extracts channel names and URLs from both JSON data within script tags and HTML content.
- Generates M3U playlists.
- Refreshes channel data on demand.
- Displays channel metadata on a web interface.
- Supports ZeroNet URLs.

## Prerequisites

- Python 3.9 or higher
- pip
- Docker (optional)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/acestream-scraper.git
    cd acestream-scraper
    ```

2. **Create and activate a virtual environment:**

    On macOS and Linux:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

    On Windows:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up the configuration:**

    Create a directory named `config` and add a `config.json` file inside it with the following content:

    ```json
    {
        "urls": [
            "https://example.com/url1",
            "https://example.com/url2"
        ],
        "base_url": "http://127.0.0.1:8008/ace/getstream?id="
    }
    ```

5. **Run the application:**

    ```bash
    python wsgi.py
    ```

## Usage

### Access the Web Interface

Open your web browser and navigate to `http://localhost:8000` to access the Acestream Scraper web interface. You can view the channel metadata and add new URLs for scraping.

### Retrieve M3U Playlist

- Retrieve the M3U playlist without refreshing:

    ```bash
    curl http://localhost:8000/list.m3u
    ```

- Retrieve the M3U playlist with a refresh:

    ```bash
    curl http://localhost:8000/list.m3u?refresh=true
    ```

## Running with Docker

1. **Pull the Docker image:**

    ```bash
    docker pull pipepito/acestream-scraper:latest
    ```

    Or build it locally:

    ```bash
    docker build -t pipepito/acestream-scraper:latest .
    ```

2. **Run the Docker container:**

    ```bash
    docker run -d \
      -p 8000:8000 \
      -p 43110:43110 \
      -p 43111:43111 \
      -v ${PWD}/config:/app/config \
      pipepito/acestream-scraper:latest
    ```

    Where:
    - `8000`: Main application web interface
    - `43110`: ZeroNet web interface
    - `43111`: ZeroNet transport port
    - `${PWD}/config`: Local directory for configuration and database files

# Docker Setup for Acestream Scraper

This document provides an overview of the required and optional variables and paths for setting up the Acestream Scraper application using Docker. Follow these instructions to ensure a smooth setup experience.

## Required Variables and Paths

### HOST_PORT

- **Description:** The port on which the Flask application will run inside the Docker container.
- **Default Value:** `8000`
- **Usage:** This environment variable specifies the port on which the Flask application will listen for incoming requests. You can change it by setting the `HOST_PORT` environment variable when running the Docker container.

    ```bash
    docker run -p <your_host_port>:<HOST_PORT> -e HOST_PORT=<HOST_PORT> -v /path/to/your/config:/app/config acestream-scraper
    ```

### /app/config

- **Description:** The directory inside the Docker container where the configuration file (`config.json`) and the database file (`acestream.db`) are stored.
- **Usage:** You need to map a local directory containing the configuration and database files to `/app/config` inside the Docker container.

    ```bash
    docker run -p 8000:8000 -p 43110:43110 --name acestream-scraper-container -v /path/to/your/config:/app/config acestream-scraper
    ```

- **Directory Structure:**
    ```
    /path/to/your/config
    ├── config.json
    └── acestream_channels.db
    ```

## Optional Variables and Paths

### Custom Base URL

- **Description:** The base URL used to generate the M3U playlist.
- **Default Value:** `"http://127.0.0.1:8008/ace/getstream?id="`
- **Usage:** You can change the base URL by updating the `base_url` value in the `config.json` file.

    ```json
    {
        "urls": [
            "https://example.com/url1",
            "https://example.com/url2"
        ],
        "base_url": "http://custom-base-url/ace/getstream?id="
    }
    ```

## Required Ports

### Application Ports
- **8000**: Main web interface for Acestream Scraper
- **43110**: ZeroNet web interface (required for ZeroNet URL scraping)
- **43111**: ZeroNet transport port (required for peer connections)

### Volumes
- **/app/config**: Configuration directory that should contain:
  - `config.json`: Configuration file
  - `acestream.db`: SQLite database (created automatically)

## Configuration Example

Create a [config.json](http://_vscodecontentref_/3) file in your local directory with:

```json
{
    "urls": [
        "https://ipfs.io/ipns/your-ipfs-url",
        "http://127.0.0.1:43110/your-zeronet-address"
    ],
    "base_url": "http://your-acestream-host:8008/ace/getstream?id="
}
```


### Accessing the Application

After running the Docker container, you can access the Acestream Scraper application in your web browser at [http://localhost:8000](http://localhost:8000).

### Notes

- Make sure the local directory containing the configuration and database files exists before running the Docker container.
- If the configuration file (`config.json`) does not exist, the application will create it with default values.
- The container now includes ZeroNet support out of the box
- ZeroNet ports (43110 and 43111) are required for proper functionality
- Configuration files are persisted through the mounted volume

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements

Special thanks to the developers of Flask, BeautifulSoup, SQLAlchemy, and other dependencies used in this project.

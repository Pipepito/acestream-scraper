# Frequently Asked Questions

## General Questions

### What is Acestream Scraper?
Acestream Scraper is an application that automatically discovers, manages, and organizes Acestream channels from various sources. It provides a web interface for channel management and generates M3U playlists that can be used with media players.

### Is this application legal?
Acestream Scraper itself is just a tool that manages links and generates playlists. The legality depends on the content you access and the laws in your region. The application doesn't host or distribute any content directly - it only organizes links that are already available elsewhere. Always ensure you have the proper rights to access any content and follow your local regulations.

### What is Acestream?
Acestream is a peer-to-peer (P2P) media streaming technology based on the BitTorrent protocol. It allows users to stream audio and video content with minimal latency. Unlike traditional streaming, it distributes the load across users, making it efficient for high-quality streams.

### How does Acestream Scraper relate to Acestream Engine?
Acestream Scraper is a management layer that works with Acestream Engine. The Engine handles the actual streaming, while the Scraper finds, organizes, and provides an interface to access channels. The Scraper can either use a built-in Acestream Engine or connect to an external one.

### What's the difference between Acestream Engine and Acexy?
- **Acestream Engine**: The core technology that handles the P2P streaming
- **Acexy**: An enhanced proxy interface for Acestream Engine that manages multiple connections efficiently

Acexy acts as a connection manager between clients and the Acestream Engine. When multiple users access the same stream, the Acestream Engine needs a unique process identifier (PID) for each connection to handle them independently. Without proper PID management, when one stream ends, it might affect other clients.

Acexy handles this PID management automatically under the hood, so you don't need to manually add `pid=id` parameters to your stream URLs. It then proxies these properly formatted requests to the Acestream Engine, greatly simplifying the user experience and making multi-client setups more reliable.

## Installation Questions

### Do I need Docker to use Acestream Scraper?
No, but it's the recommended method. Docker simplifies installation by packaging all dependencies. You can also install manually if you have Python 3.10+ installed on your system, but you'll need to manage dependencies yourself.

### How do I update to the latest version?
If using Docker Compose:
```bash
docker-compose pull
docker-compose up -d
```

If using Docker directly:
```bash
docker pull pipepito/acestream-scraper:latest
docker stop acestream-scraper
docker rm acestream-scraper
# Then run the container again with your preferred configuration
```

### Will my data be lost when I update?
No, as long as you've properly mounted the volumes for `/app/config` and (if using ZeroNet) `/app/ZeroNet/data`. These volumes store your configuration and data persistently outside the container.

## Configuration Questions

### What's the difference between base_url and ace_engine_url?
- **base_url**: The URL format used in the generated M3U playlists (e.g., `acestream://` or `http://localhost:6878/ace/getstream?id=`)
- **ace_engine_url**: The URL of your Acestream Engine for checking channel status (e.g., `http://localhost:6878`)

### What's the difference between Acestream Engine and Acexy?
- **Acestream Engine**: The core technology that handles the P2P streaming
- **Acexy**: An enhanced proxy interface for Acestream Engine

### Which Base URL format should I use?
It depends on your setup:
- Use `acestream://` if your media player supports the Acestream protocol directly
- Use `http://localhost:6878/ace/getstream?id=` for local HTTP streaming
- Use `http://[server-ip]:8080/ace/getstream?id=` if using Acexy proxy
- Use `http://[external-acestream]:port/ace/getstream?id=` for remote Acestream instances

### How often does it update the channel list?
By default, it rescans URLs every 24 hours. You can change this with the `rescrape_interval` setting in the configuration page or by setting the value when going through the setup wizard.

### What is Cloudflare WARP and why would I use it?
Cloudflare WARP is a privacy-focused VPN-like service that encrypts your traffic and routes it through Cloudflare's global network. Benefits include:
- **Privacy**: Encrypts your internet traffic
- **Access**: Can bypass certain geographical restrictions
- **Performance**: Often provides optimized routing through Cloudflare's network
- **Security**: Protection against certain network-based attacks

### How do I enable WARP in Acestream Scraper?
You need to add specific Docker capabilities and environment variables:
```bash
docker run -d \
  --cap-add NET_ADMIN \
  --cap-add SYS_ADMIN \
  -e ENABLE_WARP=true \
  -p 8000:8000 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### What WARP modes are available?
- **WARP**: Full tunnel mode - routes all traffic through WARP
- **DoT**: DNS-over-TLS mode - only DNS traffic is secured
- **Proxy**: Proxy mode - selective routing through WARP
- **Off**: WARP disabled but the service remains running

### How do I use WARP+ or Team features?
If you have a license key for WARP+ or a WARP Team account:
1. Navigate to the Configuration page in the web interface
2. Find the WARP License Management section
3. Enter your license key and register it
4. Alternatively, set the `WARP_LICENSE_KEY` environment variable when starting the container

## Usage Questions

### How do I access the web interface?
After starting the container, open your browser and navigate to:
- `http://localhost:8000` (or replace localhost with your server IP)

### Why are some channels offline?
Acestream channels may go offline for several reasons:
- The original broadcaster stopped streaming
- Network issues between you and the peers
- Not enough peers to provide the stream
- Channel ID has changed

### How do I add my own channels manually?
1. Go to the Dashboard
2. Find the "Add Channel" form
3. Enter the Acestream ID (the hash) and a name for the channel
4. Click "Add"

### How do I use the playlist with my media player?
1. Copy the playlist URL: `http://[your-server]:8000/playlist.m3u`
2. In your media player (like VLC), select "Open Network Stream" or similar
3. Paste the URL and play
4. For auto-updating playlists, use the URL directly rather than downloading the file

## Troubleshooting Questions

### My channels are all showing as offline
1. Check if your Acestream Engine is running (`ENABLE_ACESTREAM_ENGINE=true` or external)
2. Verify the `ace_engine_url` points to the correct address
3. Make sure the necessary ports are open (6878 for Acestream Engine)
4. Try refreshing one of your URLs to get updated channel information

### The Docker container fails to start
Check the logs for errors:
```bash
docker logs acestream-scraper
```
Common issues include:
- Port conflicts (another service using port 8000)
- Invalid environment variables
- Insufficient permissions on mounted volumes

### ZeroNet is not working
1. If using TOR, ensure TOR is properly configured (`ENABLE_TOR=true`)
2. Check if ports 43110 and 43111 are mapped correctly
3. Some ZeroNet sites may be unavailable or require specific permissions

### Media player can't access the streams
1. Ensure your media player has access to the Acestream Engine
2. Check if you're using the correct Base URL format for your setup
3. Verify the channel is online using the "Check Status" button
4. If using Acexy, make sure it's properly configured and running

### WARP shows as "Running but Not Connected"
1. Check the WARP section in the Configuration page
2. Try clicking the "Connect" button
3. If connection fails, try changing the WARP mode to a different setting
4. Ensure your container has the proper capabilities (`NET_ADMIN` and `SYS_ADMIN`)
5. Check container logs for WARP-related errors

## Advanced Questions

### Can I run multiple instances?
Yes, but you need to change the port mappings to avoid conflicts. For example:
```yaml
ports:
  - "8001:8000"  # First instance
  - "8002:8000"  # Second instance
```

### How can I contribute to the project?
Contributions are welcome! You can:
- Fork the repository on GitHub
- Submit pull requests with improvements
- Report bugs or suggest features
- Help improve the documentation

### Can I customize the appearance of the web interface?
The web interface uses Bootstrap and standard Flask templates. You can customize it by:
1. Mounting your custom templates to `/app/app/templates`
2. Adding custom CSS through static files
3. Developing your own theme (advanced)

### How do I monitor the application's health?
The application includes comprehensive health checks:
- HTTP endpoint: `/health`
- Docker health checks are configured
- You can use monitoring tools like Prometheus with the health endpoint

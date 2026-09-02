# Usage Guide

This guide explains how to use Acestream Scraper once it's installed.

## Contents
- [Web Interface](#web-interface)
  - [Dashboard](#dashboard)
  - [Channel Management](#channel-management)
  - [URL Management](#url-management)
  - [Configuration Page](#configuration-page)
  - [WARP Management](#warp-management)
- [M3U Playlist](#m3u-playlist)
- [API Documentation](#api-documentation)
- [Acexy Interface](#acexy-interface)
- [Cloudflare WARP](#cloudflare-warp)

## Web Interface

Open `http://localhost:8000` in your browser. The left navigation has eight pages; the label in the menu is always the page title.

### Overview

The landing page answers three questions: is it running, what is loaded, what runs next.

- A HEALTHY / ATTENTION chip in the header and a one-line summary (engine version, streams online, TV channels, guide channels, last scrape, last EPG refresh).
- **Services**: everything the image ships (AceStream engine, Acexy, IPFS, ZeroNet, WARP), whether each is switched on and answering, and a Restart button for services supervised by the container entrypoint. WARP has its own page reachable from here.
- **Inventory**: stream, TV channel and guide totals.
- **Scheduled jobs**: every background job with what it did last ("2 sources, 0 errors") and when it runs next.

### Scraper

Source URLs and the channels each one yields. Add a URL, pick its type (Auto-detect, Regular HTTP, ZeroNet, IPFS), then scrape it with the play button in its row. The Enabled switch controls whether scheduled scrapes visit the source; the row menu (⋯) offers Edit, Harvest bare IDs and Delete. The summary line shows how many sources are enabled, when the last scrape ran, how many channels were found and how many sources are failing.

When choosing the URL type:
- **Regular HTTP** for standard websites.
- **ZeroNet** for any ZeroNet URL, internal (`zero://`, `http://127.0.0.1:43110/`) or through a gateway.
- **IPFS** for IPFS content: native `ipfs://<cid>/path` and `ipns://<name>/path` (also auto-detected), gateway URLs (`https://gateway.example/ipfs/<cid>/...`) when you want them fetched as IPFS sources, and a bare `ipfs://<cid>` whose content is an M3U playlist (detected by content, not extension).

### Search

Searches the AceStream engine's catalogue. Results show the name, categories, bitrate and availability; Add puts one result into your channels, or tick several and add them in one go. The summary line counts results, selected rows and what you added this session.

### Acestream Channels

Every stream the scraper or search found. Filter by name, group, online state or playlist visibility above the grid. Each row has Check status and a TV-channel link (assign, or open the linked TV channel); the row menu offers Edit, Hide from playlist / Show in playlist, TV favourite and Delete. Header actions: Add channel, Refresh, Check all statuses, Export CSV. Hidden channels stay in the inventory but leave the playlist.

### TV Channels

The channels you publish. Each TV channel groups its streams and carries the EPG id used in the playlist. The list shows favourites (star), stream count and status; Open goes to the channel page, where you can:

- edit the main fields (name, category, number, EPG id) with the rest behind "More fields";
- add streams one by one or paste many IDs at once, and remove them;
- see the guide schedule for the linked EPG channel: what is on now and next, then day tabs for the week.

### EPG

Programme guides, in five tabs:

- **Sources**: XMLTV feeds. Add one, refresh it by hand; refreshes also run on the interval set in Settings. Failures show as plain text under the source status.
- **Channels**: guide channels found in the sources, with a link to each channel's page and whether it is linked to a TV channel. Select unlinked ones to create TV channels from them.
- **Matching**: finds scraped streams that belong to unlinked guide channels and creates the TV channels in one go.
- **Rules**: include/exclude patterns that decide which scraped names match a guide channel (rules are added from a guide channel's page).
- **Export**: download an XMLTV file with only your TV channels.

### Playlist

One M3U link with your channels. Options: name search, only online channels (with the live online/total count), favourite TV channels only, the stream link format, and group filters. The absolute link can be copied, downloaded or shown as a QR code for a player on another device.

### Settings

- **Engine**: the AceStream engine URL and whether the backend can reach it.
- **Stream link formats**: named formats for the playlist links (a prefix such as `acestream://`, or a template using `{channel_id}` and `{pid}`). The Default is used unless a playlist asks for another; until you add a named default, the built-in Default is editable in place.
- **Automation**: how often sources are scraped and the EPG is refreshed (changes apply right away), plus the PID and AppID switches for players that need them.
- **API access**: the token this browser sends when the server sets `API_TOKEN`.

### WARP

Reachable from the Overview services panel. One status row (Connected / Disconnected / Not running, mode, account, exit location) with Connect and Disconnect; connection details (public IP, exit location, tunnel and registration) and the mode/licence form appear while the service runs. When WARP is not running, the page says how to enable it (`ENABLE_WARP=true` plus the `NET_ADMIN` and `SYS_ADMIN` capabilities).

## M3U Playlist

The M3U playlist can be used with media players like VLC, Kodi, or any other player that supports M3U playlists.

### Accessing the Playlist

Base URL: `http://localhost:8000/playlist.m3u`

#### Playlist Options

- **Force refresh**: `http://localhost:8000/playlist.m3u?refresh=true`
- **Search channels**: `http://localhost:8000/playlist.m3u?search=sports`
- **Combined options**: `http://localhost:8000/playlist.m3u?refresh=true&search=sports`

### Using in Media Players

1. Copy the playlist URL (http://localhost:8000/playlist.m3u)
2. In your media player, select "Open Network Stream" or similar option
3. Paste the URL and play

### URL Formatting Note

- When using Acexy proxy (port 8080), stream URLs are formatted as `{base_url}{channel_id}`
- For all other configurations, `&pid={local_id}` is automatically appended to each stream URL: `{base_url}{channel_id}&pid={local_id}`
- This ensures proper channel identification in various player environments

## API Documentation

Acestream Scraper provides an OpenAPI/Swagger interface for developers:

1. Access the API docs at: `http://localhost:8000/api/docs`
2. Browse available endpoints and their parameters
3. Test API calls directly from the browser interface

### Key API Endpoints

- `/api/channels` - Manage channels
- `/api/urls` - Manage URLs to scrape
- `/api/stats` - Get system statistics
- `/api/config` - View and update configuration
- `/api/playlists` - Generate playlists
- `/api/health` - Check system health
- `/api/warp` - Manage Cloudflare WARP connection

## Acexy Interface

If you enabled Acexy (recommended):

1. Access the Acexy status endpoint at: `http://localhost:8080/ace/status`
2. Check Acexy status directly in the main dashboard
3. Manage your Acestream connections through this web interface

## Cloudflare WARP

When enabled, Cloudflare WARP provides these benefits:

1. **Enhanced Privacy**: Your traffic is encrypted and routed through Cloudflare's network
2. **Geo-Blocking Bypass**: Access content that might be regionally restricted
3. **Improved Security**: Protection from various network-based attacks
4. **Better Performance**: Optimized routing through Cloudflare's global network

To use WARP features:
1. Make sure the container is running with `-e ENABLE_WARP=true` and required capabilities (`--cap-add NET_ADMIN --cap-add SYS_ADMIN`)
2. Navigate to the Configuration page
3. Use the WARP controls to connect, disconnect, or change modes
4. Optionally register a WARP+ or Team license for premium features

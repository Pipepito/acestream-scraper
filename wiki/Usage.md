# Usage Guide

This guide explains how to use Acestream Scraper once it's installed.

## Contents
- [Web Interface](#web-interface)
  - [Dashboard](#dashboard)
  - [Channel Management](#channel-management)
  - [URL Management](#url-management)
  - [Configuration Page](#configuration-page)
- [M3U Playlist](#m3u-playlist)
- [API Documentation](#api-documentation)
- [Acexy Interface](#acexy-interface)

## Web Interface

Access the web interface by navigating to `http://localhost:8000` in your browser.

![Dashboard Screenshot](https://github.com/user-attachments/assets/17e000b7-20de-4a80-a990-9d0d5b225754)

### Dashboard

The dashboard provides an overview of your Acestream channels and system status. From here you can:

- View channel statistics (total, online, offline)
- Search for specific channels
- Download the M3U playlist
- Access configuration settings
- View Acexy proxy status (if enabled)

#### Dashboard Controls

- **Search Box**: Filter channels by name
- **Check All Status**: Verify which channels are currently online
- **Refresh**: Update the dashboard data
- **Download Playlist**: Generate and download the M3U playlist
- **Configuration**: Access the settings page

### Channel Management

![Channels Screenshot](https://github.com/user-attachments/assets/17006755-43ff-4817-be2c-36397cf9631b)

Acestream Scraper allows you to manage channels in several ways:

#### Adding Channels Manually

1. Enter a channel ID (the Acestream hash) and name in the form
2. Click "Add Channel"
3. The channel will appear in your channel list

#### Searching Channels

1. Use the search box to filter channels by name
2. The list will update in real-time as you type
3. Channel count will reflect your search results

#### Checking Channel Status

1. Click the "Check Status" button next to a channel or "Check All Status" at the top
2. The system will verify if the channel is available
3. Status will be displayed with color coding (green for online, red for offline)

#### Deleting Channels

1. Find the channel you want to delete
2. Click the "Delete" button next to it
3. Confirm deletion when prompted

### URL Management

URLs are sources that contain Acestream channel information. The system will scrape these URLs to discover channels.

#### Adding URLs

1. Go to the Configuration page
2. Enter a URL in the "Add New URL" form
3. Click "Add URL"
4. The system will begin scraping the URL for channels

#### Refreshing URLs

1. Find the URL in the list
2. Click the "Refresh" button
3. The system will scrape the URL again for updated channel information

#### Enabling/Disabling URLs

1. Find the URL in the list
2. Click the "Enable/Disable" button
3. Disabled URLs won't be included in automatic rescans

#### Deleting URLs

1. Find the URL in the list
2. Click the "Delete" button
3. Confirm deletion when prompted

### Configuration Page

The configuration page allows you to modify system settings:

- **Base URL**: How to format channel URLs in the playlist
- **Ace Engine URL**: Connection to your Acestream Engine
- **Rescrape Interval**: How often to automatically check for new channels
- **Acexy Status**: View the status of the Acexy proxy (if enabled)
- **Acestream Engine Status**: View the status of the Acestream Engine

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

## Acexy Interface

If you enabled Acexy (recommended):

1. Access the Acexy status endpoint at: `http://localhost:8080/ace/status`
2. Check Acexy status directly in the main dashboard
3. Manage your Acestream connections through this web interface

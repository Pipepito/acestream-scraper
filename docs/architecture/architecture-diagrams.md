# Architecture Diagrams

This document provides visual representations of the Acestream Scraper architecture to help with the rewrite process.

## System Architecture

```mermaid
graph TD
    User[User/Client] --> WebUI[React Frontend]
    User --> M3UClient[M3U Clients\nKodi/VLC/IPTV Player]
    WebUI --> FastAPI[FastAPI Backend]
    FastAPI --> DB[(SQLite Database)]
    FastAPI --> AceEngine[Acestream Engine]
    FastAPI --> AcexyProxy[Acexy Proxy]
    FastAPI --> WARP[Cloudflare WARP]
    FastAPI --> EPGSources[EPG Data Sources]
    M3UClient --> Playlist[M3U Playlist Endpoint]
    M3UClient --> EPGEndpoint[EPG XML Endpoint]
    Playlist --> FastAPI
    EPGEndpoint --> FastAPI
    AceEngine --> InternetP2P[P2P Network]
```

## Database Schema

```
┌─────────────────────┐      ┌────────────────────┐
│ acestream_channels  │      │ scraped_urls       │
├─────────────────────┤      ├────────────────────┤
│ id (PK)             │      │ id (PK)            │
│ name                │      │ url                │
│ added_at            │      │ status             │
│ last_processed      │      │ last_processed     │
│ status              │      │ error_count        │
│ source_url          │      │ last_error         │
│ scraped_url_id (FK) │◄────►│ enabled            │
│ group               │      │ added_at           │
│ logo                │      │ url_type           │
│ tvg_id              │      └────────────────────┘
│ tvg_name            │
│ m3u_source          │      ┌────────────────────┐
│ original_url        │      │ tv_channels        │
│ is_online           │      ├────────────────────┤
│ last_checked        │      │ id (PK)            │
│ check_error         │      │ name               │
│ epg_update_protected│      │ description        │
│ tv_channel_id (FK)  │◄────►│ logo_url           │
└─────────────────────┘      │ category           │
                             │ country            │
                             │ language           │
┌─────────────────────┐      │ website            │
│ epg_sources         │      │ epg_id             │
├─────────────────────┤      │ epg_source_id (FK) │◄─┐
│ id (PK)             │◄────►│ created_at         │  │
│ url                 │      │ updated_at         │  │
│ name                │      │ is_active          │  │
│ enabled             │      │ is_favorite        │  │
│ last_updated        │      │ channel_number     │  │
│ error_count         │      └────────────────────┘  │
│ last_error          │                              │
└─────────────────────┘                              │
       ▲                                             │
       │                                             │
┌──────┴──────────────┐     ┌─────────────────────┐  │
│ epg_channels        │     │ epg_programs        │  │
├─────────────────────┤     ├─────────────────────┤  │
│ id (PK)             │     │ id (PK)             │  │
│ epg_source_id (FK)  │◄────│ epg_channel_id (FK) │  │
│ channel_xml_id      │     │ program_xml_id      │  │
│ name                │     │ start_time          │  │
│ icon_url            │     │ end_time            │  │
│ language            │     │ title               │  │
│ created_at          │     │ subtitle            │  │
│ updated_at          │     │ description         │  │
└─────────────────────┘     │ ...                 │  │
                            └─────────────────────┘  │
                                                     │
┌─────────────────────┐                              │
│ epg_string_mappings │                              │
├─────────────────────┤                              │
│ id (PK)             │                              │
│ search_pattern      │                              │
│ epg_channel_id      │                              │
│ is_exclusion        │                              │
└─────────────────────┘                              │

┌─────────────────────┐                              │
│ settings            │                              │
├─────────────────────┤                              │
│ key (PK)            │                              │
│ value               │                              │
│ last_updated        │                              │
└─────────────────────┘                              │
```

## Services Architecture

```mermaid
graph TD
    WARP --> Internet[Internet]
    
    subgraph "Backend Services"
        ChannelService[Channel Service]
        ScrapeService[Scraper Service]
        PlaylistService[Playlist Service]
        EPGService[EPG Service]
        WARPService[WARP Service]
        StatusService[Status Service]
    end
      FastAPI --> ChannelService
    FastAPI --> ScrapeService
    FastAPI --> PlaylistService
    FastAPI --> EPGService
    FastAPI --> WARPService
    FastAPI --> StatusService
    
    ChannelService --> DB
    ScrapeService --> DB
    PlaylistService --> DB
    EPGService --> DB
    StatusService --> DB
    
    ScrapeService --> Internet
    EPGService --> Internet
    WARPService --> WARP
end
```

## Database Entity Relationship Diagram

```mermaid
erDiagram
    AcestreamChannel ||--o{ ScrapedURL : "sourced from"
    AcestreamChannel ||--o{ TVChannel : "linked to"
    TVChannel ||--o{ EPGChannel : "mapped to"
    EPGSource ||--o{ EPGChannel : "provides"
    EPGChannel ||--o{ EPGProgram : "contains"
    EPGStringMapping ||--o{ EPGChannel : "maps"
    
    AcestreamChannel {
        string id PK
        string name
        datetime added_at
        datetime last_processed
        string status
        string source_url
        integer scraped_url_id FK
        string group
        string logo
        string tvg_id
        string tvg_name
        text m3u_source
        text original_url
        boolean is_online
        datetime last_checked
        text check_error
        boolean epg_update_protected
        integer tv_channel_id FK
    }
    
    ScrapedURL {
        integer id PK
        string url
        string url_type
        boolean enabled
        datetime last_scraped
        integer channels_found
    }
    
    TVChannel {
        integer id PK
        string name
        string logo
        integer epg_channel_id FK
        string epg_id
    }
    
    EPGSource {
        integer id PK
        string name
        string url
        datetime last_updated
        integer channels_count
    }
    
    EPGChannel {
        integer id PK
        integer source_id FK
        string channel_id
        string display_name
        string icon
    }
    
    EPGProgram {
        integer id PK
        integer channel_id FK
        datetime start_time
        datetime end_time
        string title
        text description
    }
    
    EPGStringMapping {
        integer id PK
        string from_string
        string to_string
    }
```

## API Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI Backend
    participant Service
    participant Repository
    participant Database
    participant External as External Services
    
    %% Channel Status Check Flow
    Client->>API: POST /api/v1/channels/{id}/check_status
    API->>Service: check_channel_status(channel_id)
    Service->>Repository: get_channel(channel_id)
    Repository->>Database: SELECT * FROM acestream_channels WHERE id = ?
    Database-->>Repository: channel data
    Repository-->>Service: Channel object
    Service->>External: Check status via Acestream Engine API
    External-->>Service: Status response
    Service->>Repository: update_channel(id, is_online, last_checked)
    Repository->>Database: UPDATE acestream_channels SET ...
    Database-->>Repository: Success
    Repository-->>Service: Updated channel
    Service-->>API: Status result
    API-->>Client: Channel status response
    
    %% Playlist Generation Flow
    Client->>API: GET /api/v1/playlists/m3u?search=sports
    API->>Service: generate_playlist(search="sports")
    Service->>Repository: get_channels(filter={"search": "sports"})
    Repository->>Database: SELECT * FROM acestream_channels WHERE ...
    Database-->>Repository: Matching channels
    Repository-->>Service: Channel list
    Service->>Service: Format channels as M3U
    Service-->>API: M3U content
    API-->>Client: M3U playlist file
```

## Frontend Component Structure

```mermaid
graph TD
    App --> Router
    Router --> Routes
    
    Routes --> Dashboard
    Routes --> ChannelsPage
    Routes --> URLsPage
    Routes --> PlaylistPage
    Routes --> EPGPage
    Routes --> SettingsPage
    Routes --> StatusPage
    
    subgraph "Shared Components"
        NavBar
        Footer
        Notifications
        LoadingSpinner
    end
    
    subgraph "Channel Components"
        ChannelList
        ChannelItem
        ChannelForm
        StatusBadge
    end
    
    subgraph "URL Components" 
        URLList
        URLItem
        URLForm
    end
    
    subgraph "Playlist Components"
        PlaylistOptions
        DownloadButton 
    end
    
    subgraph "EPG Components"
        EPGSourceList
        EPGMappings
    end
    
    Dashboard --> ChannelList
    ChannelsPage --> ChannelList
    ChannelsPage --> ChannelForm
    URLsPage --> URLList
    URLsPage --> URLForm
    ChannelList --> ChannelItem
    ChannelItem --> StatusBadge
    URLList --> URLItem
    PlaylistPage --> PlaylistOptions
    PlaylistPage --> DownloadButton
    EPGPage --> EPGSourceList
    EPGPage --> EPGMappings
```

## Data Flow Diagram

```mermaid
graph TD
    subgraph "External Data Sources"
        WebSources[Web Sources]
        ZeroNet[ZeroNet Sites]
        EPGProviders[EPG Providers]
    end
    
    subgraph "Data Collection"
        WebScraper[Web Scraper]
        ZeroNetScraper[ZeroNet Scraper]
        EPGFetcher[EPG Fetcher]
    end
    
    subgraph "Data Processing"
        ChannelProcessor[Channel Processor]
        EPGProcessor[EPG Processor]
        StatusChecker[Status Checker]
    end
    
    subgraph "Data Storage"
        ChannelDB[(Channel Database)]
        EPGDB[(EPG Database)]
        ConfigDB[(Configuration)]
    end
    
    subgraph "API Endpoints"
        ChannelsAPI[Channels API]
        PlaylistAPI[Playlist API]
        EPGAPI[EPG API]
        ConfigAPI[Configuration API]
    end
    
    WebSources --> WebScraper
    ZeroNet --> ZeroNetScraper
    EPGProviders --> EPGFetcher
    
    WebScraper --> ChannelProcessor
    ZeroNetScraper --> ChannelProcessor
    EPGFetcher --> EPGProcessor
    
    ChannelProcessor --> ChannelDB
    EPGProcessor --> EPGDB
    StatusChecker --> ChannelDB
    
    ChannelDB --> ChannelsAPI
    ChannelDB --> PlaylistAPI
    EPGDB --> EPGAPI
    ConfigDB --> ConfigAPI
    
    ChannelsAPI --> StatusChecker
```

These diagrams should help visualize the complex relationships and workflows in our application, making it easier to understand the architecture during the rewrite process.

# Development Phases for Acestream Scraper Rewrite

This document outlines the development phases for rewriting the Acestream Scraper application within the existing repository structure. The goal is to create a completely new application in a separate folder while maintaining the current one until the new version is fully ready.

## Project Goal

To rebuild Acestream Scraper with modern technologies:
- **Backend**: FastAPI (replacing Flask-RESTX)
- **Frontend**: React with TypeScript
- **Database**: SQLAlchemy with modern typing
- **Documentation**: OpenAPI-driven API documentation
- **Deployment**: Unified deployment with Docker

## Development Strategy

Rather than migrating the application in-place, we will:

1. Create a new `v2/` directory in the repository
2. Develop the new application in this isolated directory
3. Keep the current application running unmodified
4. When the new application is ready, switch to it completely

## Phase 1: Setup and Base Structure

### 1.1 Project Setup
- Create `v2/` directory structure
- Set up FastAPI application skeleton
- Configure Poetry/pip for dependency management
- Set up React application with TypeScript
- Configure Docker for development

### 1.2 Database Schema Design
- Map all current models to modern SQLAlchemy with type annotations
- Implement database configuration that can use the existing database file
- Ensure backward compatibility with the data structure
- Set up Alembic migrations for future schema changes

### 1.3 Core Utilities
- Implement configuration management
- Set up logging
- Implement dependency injection system
- Create base repository and service patterns

## Phase 2: Core Scraping Engine

### 2.1 Scraper Base Implementation
- Port the `BaseScraper` abstract class with identical functionality
- Implement common functionality for acestream link extraction
- Port regex patterns and extraction logic
- Implement the scraper factory pattern for URL handling

### 2.2 HTTP Scraper
- Port the `HTTPScraper` implementation for regular HTTP/HTTPS URLs
- Ensure identical behavior for web scraping functionality
- Implement error handling and retry logic
- Ensure proper M3U file detection and processing

### 2.3 ZeroNet Scraper
- Port the `ZeronetScraper` implementation for ZeroNet URLs
- Ensure correct integration with the ZeroNet service
- Implement specialized content extraction for ZeroNet pages
- Maintain advanced parsing for various data formats

### 2.4 Content Extraction Logic
- Port all specialized extraction methods for acestream links
- Implement parsing logic for various page structures
- Ensure all edge cases are handled properly
- Port channel name cleaning and metadata extraction

## Phase 3: Core Domain Models and Services

### 3.1 Channel Management
- SQLAlchemy models for channels
- Pydantic DTOs for API request/response
- Repository implementation
- Service layer with business logic
- API controllers/routers
- Integration with scrapers

Specific endpoints to implement:
- `GET /api/v1/channels/` - List all channels
- `GET /api/v1/channels/{id}` - Get a specific channel
- `POST /api/v1/channels/` - Create a new channel
- `PUT /api/v1/channels/{id}` - Update a channel
- `DELETE /api/v1/channels/{id}` - Delete a channel
- `POST /api/v1/channels/{id}/check_status` - Check channel status
- `POST /api/v1/channels/check_status_all` - Check all channels

### 2.2 URL Management and Scraping
- Models, DTOs, repositories and services for scraped URLs
- Implement scraper services for different URL types
- API controllers for URL management

Specific endpoints to implement:
- `GET /api/v1/urls/` - List all URLs
- `POST /api/v1/urls/` - Add a new URL
- `GET /api/v1/urls/{id}` - Get URL details
- `PUT /api/v1/urls/{id}` - Update URL
- `DELETE /api/v1/urls/{id}` - Delete URL
- `POST /api/v1/urls/{id}/refresh` - Refresh URL

### 2.3 TV Channels Management
- Models, DTOs, repositories and services for TV channels
- Channel-to-stream association logic
- API controllers for TV channel management

Specific endpoints to implement:
- `GET /api/v1/tv-channels/` - List all TV channels
- `POST /api/v1/tv-channels/` - Create TV channel
- `GET /api/v1/tv-channels/{id}` - Get TV channel
- `PUT /api/v1/tv-channels/{id}` - Update TV channel
- `DELETE /api/v1/tv-channels/{id}` - Delete TV channel
- `GET /api/v1/tv-channels/{id}/acestreams` - Get associated acestreams
- `POST /api/v1/tv-channels/{id}/acestreams` - Associate acestream
- `DELETE /api/v1/tv-channels/{id}/acestreams/{acestream_id}` - Remove association

## Phase 3: Advanced Features

### 3.1 Playlist Generation
- Implement playlist service
- M3U formatting
- EPG XML generation
- API controllers for playlist/EPG endpoints

Specific endpoints to implement:
- `GET /api/v1/playlists/m3u` - Generate full M3U playlist
- `GET /api/v1/playlists/tv-channels/m3u` - Generate TV channels playlist
- `GET /api/v1/playlists/epg.xml` - Generate EPG XML

### 3.2 EPG Integration
- EPG models (source, channel, program)
- EPG service implementation
- String mapping for channel matching
- API controllers for EPG management

Specific endpoints to implement:
- `GET /api/v1/epg/sources` - List EPG sources
- `POST /api/v1/epg/sources` - Add EPG source
- `DELETE /api/v1/epg/sources/{id}` - Delete EPG source
- `GET /api/v1/epg/mappings` - List string mappings
- `POST /api/v1/epg/auto-scan` - Run auto-mapping
- `POST /api/v1/epg/update-channels` - Update all channels' EPG data

### 3.3 Search Integration
- Acestream engine search integration
- Search service implementation
- API controllers for search functionality

Specific endpoints to implement:
- `GET /api/v1/search` - Search channels
- `POST /api/v1/search/add` - Add a channel from search
- `POST /api/v1/search/add_multiple` - Batch add channels

### 3.4 External Services Integration
- Cloudflare WARP integration
- Acexy proxy integration
- API controllers for WARP/proxy management

Specific endpoints to implement:
- `GET /api/v1/warp/status` - Get WARP status
- `POST /api/v1/warp/connect` - Connect WARP
- `POST /api/v1/warp/disconnect` - Disconnect WARP

### 3.5 System Configuration and Health
- Configuration service
- Health check service
- Stats collection
- API controllers for config/health/stats

Specific endpoints to implement:
- `GET /api/v1/config/base_url` - Get base URL
- `PUT /api/v1/config/base_url` - Update base URL
- `GET /api/v1/health` - Get system health
- `GET /api/v1/stats` - Get statistics

## Phase 4: Frontend Implementation (TypeScript-Only)

### 4.1 Core UI Components
- Design system setup with strict TypeScript
- Core component library in TypeScript
- Layout components with proper type definitions
- Common utilities and hooks with TypeScript
- TypeScript configuration (strict mode, no JavaScript allowed)

### 4.2 Channel Management UI
- Channel list/grid view
- Channel detail view
- Add/edit channel forms
- Status check interface

### 4.3 URL Management UI
- URL list view
- Add/edit URL forms
- URL refresh interface

### 4.4 TV Channel Management UI
- TV channel list/grid view
- TV channel detail view
- Acestream association interface

### 4.5 Playlist and EPG UI
- Playlist generation interface
- Playlist options and filtering
- EPG management interface
- EPG source management

### 4.6 Search and Import UI
- Search interface
- Search results display
- Import functionality

### 4.7 Configuration and Status UI
- Settings interface
- Health dashboard
- Statistics display

## Phase 5: Testing and Documentation

### 5.1 Backend Tests
- Unit tests for services and repositories
- API integration tests
- Load and performance tests

### 5.2 Frontend Tests
- Component unit tests
- Integration tests
- End-to-end tests

### 5.3 Documentation
- API documentation (auto-generated from OpenAPI)
- User documentation
- Deployment documentation

## Phase 6: Deployment and Transition

### 6.1 Docker Integration
- Multi-architecture Docker setup (x86_64 and arm64)
- Docker Compose configuration
- Volume mapping for data persistence

### 6.2 Transition Plan
- Database conversion/migration if needed
- User transition guide
- Switch from old to new application

## Working with the Existing Database

To ensure compatibility with the current application, we can:

1. **Use the same database file**: Configure the new application to use the existing SQLite database file.

2. **Maintain schema compatibility**: Ensure models in the new application match the current database schema to avoid breaking changes.

3. **Add new tables separately**: Use table prefixes for new features to avoid clashing with the existing schema.

4. **Migration script**: Create a migration script to run when transitioning fully to the new application.

## Development Guidelines

- **Parallel development**: Develop new features independently from the existing application.
- **Feature parity first**: Ensure the new application matches all current functionality before adding new features.
- **Testing**: Implement comprehensive tests to ensure the new application works as expected.
- **Documentation**: Document all APIs, features, and configuration options.
- **AI-driven development**: Leverage AI coding assistants to accelerate development.

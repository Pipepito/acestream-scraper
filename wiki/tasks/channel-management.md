
## Overview
This feature creates a "TV Channel" entity that serves as a grouping mechanism for multiple Acestream channels (streams) broadcasting the same TV channel content. This allows users to manage real TV channels independently from the individual Acestream streams.

## Implemented Components

### Data Model
- Created `TVChannel` model in `app/models/tv_channel.py` with:
  - Core fields: id, name, description, logo_url, category, country, language, website
  - EPG-related fields: epg_id, epg_source_id
  - Meta fields: created_at, updated_at, is_active
- Added `tv_channel_id` foreign key to `AcestreamChannel` model with a bidirectional relationship

### Database Migration
- Created migration `20250409_add_tv_channels.py` that:
  - Creates the `tv_channels` table with all required fields
  - Adds `tv_channel_id` column to `acestream_channels` table
  - Sets up the foreign key constraint
  - Includes safety checks to prevent errors on rerun

### Repository Layer
- Implemented `TVChannelRepository` with:
  - CRUD operations (create, read, update, delete)
  - Methods to filter channels by various criteria (category, country, language)
  - Pagination support for listing operations
  - Methods to get unique filter values (categories, countries, languages)
  - Association management between TV channels and Acestream channels
  - Bulk update functionality for updating multiple channels at once

### API Controller
- Created `tv_channels_controller.py` with endpoints for:
  - GET /tv-channels - List all TV channels with filtering and pagination
  - POST /tv-channels - Create a new TV channel
  - GET /tv-channels/{id} - Get details of a specific TV channel
  - PUT /tv-channels/{id} - Update a TV channel
  - DELETE /tv-channels/{id} - Delete a TV channel
  - POST /tv-channels/{id}/acestreams - Assign Acestream channels
  - DELETE /tv-channels/{id}/acestreams/{acestream_id} - Remove assignment
  - POST /tv-channels/{id}/sync-epg - Synchronize EPG data
  - GET /tv-channels/unassigned-acestreams - Get acestreams not assigned to any channel
  - POST /tv-channels/batch-assign - Batch assign acestreams based on patterns
  - POST /tv-channels/associate-by-epg - Associate acestreams by matching EPG IDs
  - POST /tv-channels/bulk-update-epg - Update EPG data for all channels
  - POST /tv-channels/generate-from-acestreams - Generate TV channels from existing acestreams
  - POST /tv-channels/bulk-update - Update multiple TV channels at once

### Service Layer
- Created `TVChannelService` with business logic for:
  - Finding best acestream based on online status and metadata quality
  - EPG data synchronization between TV channels and acestreams
  - Batch operations for acestream assignments
  - Smart generation of TV channels from acestreams based on metadata
  - Grouping algorithms based on name patterns or EPG IDs

### Frontend Components
- Templates:
  - `tv_channels.html` - Main listing page with filters and actions
  - `tv_channel_detail.html` - Detailed view with tabs for acestreams, EPG info, and details
  - Modal partials for adding/editing channels and assigning acestreams
  - Bulk edit functionality for multiple channels

- JavaScript:
  - `tv-channels.js` - Main list page interactions, filtering, pagination, selection
  - `tv-channel-detail.js` - Detail page with acestream management

### EPG Management Enhancement
- Created dedicated EPG management page (`epg.html`) separated from configuration
- Moved EPG functionality from config section to its own tab in the navigation
- Implemented comprehensive EPG UI with:
  - Sources management
  - Channel mapping rules
  - Auto-mapping functionality
  - EPG channel browsing
  - Program schedule viewing

### Integration with Existing Features
- Added namespace registration in `app/api/__init__.py`
- Added routes in `app/views/main.py` for frontend pages
- Added TV channel statistics endpoint in `stats_controller.py`
- Added links to TV channels in the dashboard
- Enhanced the UI with modern design elements and responsive layouts

## Architecture Decisions

### Many-to-One Relationship
- Each Acestream can only belong to one TV channel (to avoid duplicating streams in playlists)
- A TV channel can have multiple Acestream channels (for reliability and quality options)

### EPG Integration
- TV channels can have an `epg_id` that links to EPG data
- When a TV channel has EPG data, it can propagate this to its acestreams
- Acestreams can be protected from EPG updates with the `epg_update_protected` flag
- Dedicated EPG management interface for better organization

### Bulk Operations
- Support for bulk editing multiple channels at once
- Batch assignment of acestreams based on patterns
- Bulk EPG data synchronization
- Smart channel generation from existing acestreams

### UI Enhancements
- Responsive design for all screen sizes
- Interactive channel selection with bulk edit capabilities
- Improved layout for action buttons
- Tab-based organization of related functions
- Real-time feedback for user actions

## UI Flow
1. Main dashboard has a link to TV Channels management
2. TV Channels page shows all channels with filters and statistics
3. Detail page for each channel shows:
   - Associated acestreams and their status
   - EPG information
   - Channel metadata and stats
4. Modal interfaces for:
   - Creating/editing channels
   - Assigning acestreams to channels
   - Bulk editing multiple channels

## Known Limitations & Considerations
- Creating too many TV channels can slow down the UI
- EPG synchronization can be resource-intensive
- Consider performance impacts when batch generating channels from large acestream collections
- Name-based matching for channel generation is not perfect and may require manual review
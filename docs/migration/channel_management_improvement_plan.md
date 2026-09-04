# Channel Management Gaps & Migration Plan

## Overview

This plan outlines the steps required to achieve a robust, decoupled channel management system in V2, supporting:

- Independent management of Acestream channels and TV channels
- Assignment of multiple Acestream channels to a single TV channel
- Playlist generation from Acestream channels, with optional TV channel/group filtering
- Migration from V1 patterns to a modern, maintainable architecture

---

## 1. Current State Analysis

### 1.1 Models

- **AcestreamChannel** (`backend/app/models/models.py`): Represents a stream source, can be linked to a TV channel via `tv_channel_id`.
- **TVChannel** (`backend/app/models/models.py`): Represents a logical TV channel, can have multiple Acestream channels assigned.

### 1.2 Functionality

- **Frontend “Channels” page** (`frontend/src/pages/Channels.tsx`): Currently manages Acestream channels only.
- **Backend services**:
  - CRUD for AcestreamChannel (`backend/app/services/channel_service.py`)
  - Playlist generation from Acestream channels (`backend/app/services/playlist_service.py`)
  - Search/import for Acestream channels (`backend/app/services/search_service.py`)
- **No dedicated UI for TV channel management or assignment.**

---

## 2. Target Architecture

### 2.1 Data Model

- **AcestreamChannel**: Can exist independently or be assigned to a TV channel.
- **TVChannel**: Can exist independently, can have many Acestream channels assigned.
- **Assignment**: Many AcestreamChannels → One TVChannel; One TVChannel ← Many AcestreamChannels.

### 2.2 Functional Requirements

- Manage Acestream channels independently (manual, search, scraper import).
- Manage TV channels independently (manual, EPG import).
- Assign/unassign Acestream channels to TV channels.
- View all Acestream channels assigned to a TV channel.
- Generate M3U playlists from Acestream channels, with optional TV channel/group filtering.

---

## 3. Migration & Implementation Steps

### 3.1 Backend

#### 3.1.1 Models

- **Review** `AcestreamChannel` and `TVChannel` in `models.py` for correct relationships.
- **Ensure**: `AcestreamChannel.tv_channel_id` is nullable and supports many-to-one.

#### 3.1.2 API Endpoints

- **AcestreamChannel CRUD**: Expose endpoints for create, read, update, delete.
- **TVChannel CRUD**: Expose endpoints for create, read, update, delete.
- **Assignment**:
  - Endpoint to assign/unassign Acestream channels to TV channels.
  - Endpoint to list all Acestream channels for a given TV channel.
- **Playlist Generation**:
  - Update `playlist_service.py` to support filtering by TV channel/group.
  - Ensure endpoints allow playlist download by TV channel/group.

#### 3.1.3 Services

- **Update** `channel_service.py` and `search_service.py` to support assignment logic.
- **Ensure**: All assignment/unassignment operations are robust and transactional.

#### 3.1.4 Migration Scripts

- **If needed**, create migration scripts to decouple any legacy “channel” data into AcestreamChannel and TVChannel.

---

### 3.2 Frontend

#### 3.2.1 Pages & Navigation

- **Split** “Channels” into:
  - “Acestream Channels” management page (`src/pages/AcestreamChannels.tsx`)
  - “TV Channels” management page (`src/pages/TVChannels.tsx`)
- **Update navigation** to allow easy switching between these pages.

#### 3.2.2 Acestream Channels Page

- List, create, edit, delete Acestream channels.
- Assign/unassign to TV channels (dropdown or modal).
- Show assigned TV channel (if any).

#### 3.2.3 TV Channels Page

- List, create, edit, delete TV channels.
- In TV channel detail, show all assigned Acestream channels.
- Allow assignment/unassignment of Acestream channels.

#### 3.2.4 Assignment UX

- In both pages, provide clear UI for assigning/unassigning streams.
- Consider drag-and-drop, multi-select, or modal assignment for bulk operations.

#### 3.2.5 Playlist Download

- Allow playlist download from Acestream channels page, with optional TV channel/group filter.

---

### 3.3 Testing

- **Backend**: Add tests for assignment logic, playlist generation, CRUD for both models.
- **Frontend**: Add tests for new pages, assignment flows, and playlist download.

---

### 3.4 Documentation

- **Update** `docs/` with:
  - This migration plan (`channel_management_improvement_plan.md`)
  - Updated architecture diagrams (if available)
  - API documentation for new endpoints
  - UX documentation for new flows

---

## 4. File References

- `backend/app/models/models.py`: Data models for AcestreamChannel and TVChannel
- `backend/app/services/playlist_service.py`: Playlist generation logic
- `backend/app/services/channel_service.py`: Channel CRUD and assignment logic
- `backend/app/services/search_service.py`: Search/import logic for Acestream channels
- `frontend/src/pages/Channels.tsx`: Current Acestream channel management page
- `frontend/src/pages/TVChannels.tsx` (to be created): TV channel management page
- `frontend/src/pages/AcestreamChannels.tsx` (to be created): Acestream channel management page
- `docs/`: Documentation and migration plans

---

## 5. Open Questions / Decisions

- Should assignment be possible from both Acestream and TV channel pages, or only one?
- Should playlist generation support advanced filtering (e.g., by TV channel, group, or other metadata)?
- How should legacy “channels” be migrated if their type is ambiguous?

---

## 6. Next Steps

1. Review and approve this plan.
2. Create migration scripts and new API endpoints as needed.
3. Refactor frontend to split management pages and add assignment UX.
4. Update documentation and tests.
5. Validate with real data and iterate.

---

_Plan authored by GitHub Copilot, 2025-07-11_

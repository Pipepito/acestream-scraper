# Acestream Scraper - Acceptance Criteria (Gherkin Format, API & Frontend, Full Coverage)

#####################################################################
# API USE CASES (Controllers, Endpoints, Error, and Edge Case Coverage)
#####################################################################

Feature: Channel API

  Scenario: List all channels
    When a GET request is made to /api/v1/channels/
    Then the API responds with a list of all channels and their metadata

  Scenario: Search channels by name or source URL
    When a GET request is made to /api/v1/channels/?search=term&url_id=sourceId
    Then only channels matching the search and source are returned

  Scenario: Get single channel by ID
    Given a channel exists
    When a GET request is made to /api/v1/channels/{id}
    Then the API responds with the channel data

  Scenario: Create a new channel
    When a POST request is made to /api/v1/channels/ with valid id and name
    Then the API creates the channel and returns its data

  Scenario: Update a channel's metadata
    Given a channel exists
    When a PATCH request is made to /api/v1/channels/{id} with updated fields
    Then the API updates the channel and returns the new data

  Scenario: Delete a channel
    Given a channel exists
    When a DELETE request is made to /api/v1/channels/{id}
    Then the channel is deleted and no longer returned in lists

  Scenario: Check status of a channel
    Given a channel exists
    When a POST request is made to /api/v1/channels/{id}/check_status
    Then the API updates and returns the channel's online/offline status

  Scenario: Check status of all channels
    When a POST request is made to /api/v1/channels/check_status_all
    Then all channels' statuses are updated

  Scenario: Protect/unprotect EPG mapping for a channel
    Given a channel exists
    When a PATCH request updates epg_update_protected
    Then the EPG mapping is locked/unlocked

  Scenario: Channel CRUD validation errors
    When a POST, PATCH or DELETE is made with invalid data or IDs
    Then the API responds with a relevant error and message

Feature: URLs API

  Scenario: List all URL sources
    When a GET request is made to /api/v1/urls/
    Then all URL sources and their statuses are returned

  Scenario: Add a new URL to scrape
    When a POST request is made to /api/v1/urls/ with url and url_type
    Then the URL is created and queued for scraping

  Scenario: Enable/disable a URL
    Given a URL exists
    When a PATCH request is made to /api/v1/urls/{id} with enabled true/false
    Then the URL is enabled/disabled

  Scenario: Refresh a URL
    Given a URL exists
    When a POST request is made to /api/v1/urls/{id}/refresh
    Then the URL is scraped again for channels

  Scenario: Delete a URL
    Given a URL exists
    When a DELETE request is made to /api/v1/urls/{id}
    Then the URL and associated channels are deleted

  Scenario: Adding duplicate or invalid URLs
    When a POST is made with a duplicate or invalid URL
    Then the API responds with an error

Feature: Playlist/EPG API

  Scenario: Download full M3U playlist
    When a GET request is made to /api/v1/playlists/m3u
    Then the full playlist is returned as audio/x-mpegurl

  Scenario: Download TV channels playlist
    When a GET request is made to /api/v1/playlists/tv-channels/m3u
    Then only TV channels playlist is returned

  Scenario: Download EPG XML guide
    When a GET request is made to /api/v1/playlists/epg.xml
    Then XMLTV-compliant EPG is returned

  Scenario: Playlist/EPG with filters
    When GET requests are made with search and favorites_only parameters
    Then only matching channels are included

  Scenario: Playlist/EPG error handling
    When playlist or EPG generation fails
    Then the API returns a descriptive error

Feature: EPG API

  Scenario: List all EPG sources
    When a GET request is made to /api/v1/epg/sources
    Then a list of all EPG sources is returned

  Scenario: Add a new EPG source
    When a POST request is made to /api/v1/epg/sources with a valid URL
    Then the source is added if unique and valid

  Scenario: Prevent duplicate EPG sources
    When a POST is made with an existing source URL
    Then the API responds with a conflict error

  Scenario: Delete an EPG source
    When a DELETE request is made to /api/v1/epg/sources/{id}
    Then the EPG source is removed

  Scenario: List all EPG string mappings
    When a GET request is made to /api/v1/epg/mappings
    Then all string mappings are returned

  Scenario: Add or delete EPG string mappings
    When a POST or DELETE is made to /api/v1/epg/mappings
    Then mappings are added or removed accordingly

  Scenario: Run EPG auto-scan and update all channels
    When a POST request is made to /api/v1/epg/auto_scan
    Then channels are auto-mapped to EPG data

  Scenario: Update all channels' EPG data
    When a POST request is made to /api/v1/epg/update_channels
    Then EPG mapping is updated for all channels

  Scenario: EPG error and edge cases
    When invalid URLs or data are used
    Then the API responds with validation or not found errors

Feature: Search API

  Scenario: Search channels by query and filters
    When a GET is made to /api/v1/search with query, category, page, or page_size
    Then paginated matching channels are returned

  Scenario: Add a searched channel to the database
    When a POST is made to /api/v1/search/add with id and name
    Then the channel is created

  Scenario: Batch import channels from search results
    When a POST is made to /api/v1/search/add_multiple with a list of channels
    Then all valid channels are imported, and existing ones are reported

  Scenario: Search API error handling
    When invalid or incomplete search data is submitted
    Then the API responds with a relevant error

Feature: Stats API

  Scenario: Get application statistics
    When a GET request is made to /api/v1/stats/
    Then channel/url stats, health, and config are returned

Feature: Config API

  Scenario: Get and update base URL
    When a GET or PUT is made to /api/v1/config/base_url
    Then the current or new base URL is returned/stored

  Scenario: Get and update Acestream Engine URL
    When a GET or PUT is made to /api/v1/config/ace_engine_url
    Then the current or new engine URL is returned/stored

  Scenario: Get and update rescrape interval
    When a GET or PUT is made to /api/v1/config/rescrape_interval
    Then the current or new interval is returned/stored

  Scenario: Get Acexy and Acestream Engine status
    When a GET is made to /api/v1/config/acexy_status or /api/v1/config/acestream_status
    Then the status is returned (enabled, available, message, etc.)

Feature: Health API

  Scenario: Get full system health
    When a GET request is made to /api/v1/health/
    Then the API returns app, database, acexy, acestream, and task manager status

  Scenario: Health endpoint error handling
    When a component is down
    Then the health report reflects the degraded status and error details

Feature: WARP API

  Scenario: Get WARP status
    When a GET is made to /api/v1/warp/status
    Then current WARP status, mode, and account info are returned

  Scenario: Connect/disconnect WARP
    When a POST is made to /api/v1/warp/connect or /api/v1/warp/disconnect
    Then WARP is connected or disconnected

  Scenario: Change WARP mode
    When a POST is made to /api/v1/warp/mode with a valid mode
    Then the mode is changed

  Scenario: Register WARP license key
    When a POST is made to /api/v1/warp/license with a key
    Then the key is registered

  Scenario: WARP API error handling
    When WARP is not enabled or fails
    Then the API responds with an error and message

Feature: OpenAPI & Documentation

  Scenario: OpenAPI schema is always available
    When a GET request is made to /openapi.json
    Then the full and current schema is returned

  Scenario: Swagger UI is always available
    When a GET request is made to /docs
    Then the UI is displayed and includes all endpoints

Feature: Error, Validation, and Edge Cases

  Scenario: All endpoints return proper HTTP error codes
    When invalid data or method is used
    Then the API returns 400, 404, 409, 422, or 500 as appropriate

  Scenario: Deleting resources cleans up related data (e.g., channels when URL is deleted)
    When a parent resource is deleted
    Then all related child data is also removed

  Scenario: Unauthorized access is rejected (if authentication is enabled)
    When no or invalid credentials are provided to protected endpoints
    Then the API returns 401 Unauthorized

  Scenario: All endpoints have required CORS and content-type headers
    When requests are made from browsers or tools
    Then responses include appropriate headers

#####################################################################
# FRONTEND USE CASES (SPA Features)
#####################################################################

Feature: Dashboard and Channel Management

  Scenario: List, search, and filter channels in the dashboard
    When the user visits the dashboard
    Then all channels are listed, and searching/filtering works

  Scenario: Add, edit, and delete channels via the UI
    When the user uses the forms and buttons for channels
    Then channels are created, edited, or deleted in the backend and UI

  Scenario: Check channel status from the UI
    When the user clicks 'Check Status'
    Then the online/offline status is updated and reflected in the UI

  Scenario: Channel EPG lock/unlock
    When the user sets/unsets EPG protection
    Then the UI and backend reflect the new state

Feature: URL Source Management

  Scenario: List, add, enable/disable, refresh, and delete URLs via the UI
    When the user manages URLs
    Then the changes are visible in the UI and persisted

Feature: Playlist and EPG

  Scenario: Download playlist/EPG via the UI
    When the user clicks 'Download Playlist' or 'Download EPG'
    Then the file is downloaded and valid

  Scenario: Filter playlist/EPG by search or favorites
    When the user applies filters
    Then only matching channels are included in the download

Feature: EPG Source and Mapping Management

  Scenario: List/add/delete EPG sources and mappings
    When the user manages EPG sources/mappings
    Then the UI reflects changes and backend is updated

  Scenario: Run EPG auto-mapping and update all channels
    When the user triggers auto-mapping
    Then channels are mapped and UI updates

Feature: Search and Import

  Scenario: Search for new channels and import them
    When the user searches Acestream channels
    Then results are paginated and can be imported as single or batch

Feature: Configuration and Status

  Scenario: View and update configuration in the UI
    When the user edits configuration fields
    Then settings are saved and used in future operations

  Scenario: View Acexy, Acestream Engine, and WARP status in the UI
    When the user visits status sections
    Then the latest status is shown

Feature: System Health and Stats

  Scenario: View system health, stats, and logs in the UI
    When the user visits the health/stats section
    Then all relevant info is current and accurate

Feature: Error and Feedback

  Scenario: All errors and warnings are clearly shown in the UI
    When API errors occur
    Then the user sees a readable message

Feature: SPA Integration

  Scenario: SPA and API are served from the same endpoint
    When the user accesses the app
    Then only one URL is used for both frontend and API

Feature: OpenAPI Client

  Scenario: Frontend uses autogenerated API client for all requests
    When the OpenAPI schema changes
    Then the frontend API client is regenerated and used

Feature: Accessibility and Responsiveness

  Scenario: UI is accessible and responsive
    When the app is used on different devices and by all users
    Then all features work as expected

Feature: Authentication (if enabled)

  Scenario: User logs in/out and protected routes are enforced
    When authentication is required
    Then the UI and API enforce user login, and unauthorized access is blocked

#####################################################################
# END-TO-END/INTEGRATION USE CASES
#####################################################################

Feature: End-to-end Integration

  Scenario: All frontend actions are reflected in backend state and vice versa
    When the user performs any action in the UI
    Then the backend data and API responses match the UI state

  Scenario: Backend and frontend work on x86_64 and arm64
    When the stack is deployed on any supported architecture
    Then all features, endpoints, and UI work as specified

  Scenario: Documentation and help are available in the UI
    When the user visits help/docs sections
    Then the latest guides, FAQs, and API docs are visible

# Dashboard Activity & Status: Full-Stack Implementation Plan

## 1. Requirements Overview

- **Recent Activity Log**: Store and expose recent activity (scrapes, background tasks, errors, user actions, system events, etc.) with user-configurable retention (0–30 days, default 7).
- **Background Task Status**: Expose last run, next run, status, errors, and results for all background tasks (scraping, EPG refresh, playlist generation, etc.).
- **Active Streams Count**: Expose the number of active streams (preferably via acexy, fallback to acestream if possible; handle gracefully if not available).
- **Warp Status**: Expose current warp status (connected, disconnected, error, etc.) and relevant details.
- **Auto-Refresh & Retention Controls**: User can set auto-refresh interval (e.g., 10s–10min) and retention period (0–30 days).
- **All data must be live, not mocked.**
- **Robust error handling and clear loading states in UI.**

---

## 2. Backend Implementation Plan

### 2.1. Activity Log System

#### Data Model

- Create a new SQL table `activity_log`:
  - `id` (PK, autoincrement)
  - `timestamp` (UTC, indexed)
  - `type` (enum/string: scrape, task, error, user_action, system, etc.)
  - `message` (short summary)
  - `details` (JSON/text, optional, for structured data or stack traces)
  - `user` (nullable, for user-initiated actions)
- Alembic migration for table creation.

#### Logging Integration

- Add utility function (e.g., `log_activity(type, message, details=None, user=None)`) in a shared module.
- Call this function in:
  - Scraper start/finish/error
  - Background task start/finish/error
  - EPG refresh, playlist generation, config changes
  - User actions (if applicable)
  - System events (startup, shutdown, errors)
- Ensure error stack traces and relevant context are captured in `details`.

#### Retention Policy

- Store retention config in DB (settings table) or config file (default 7 days, min 0, max 30).
- Implement scheduled cleanup (e.g., daily background job) to delete logs older than retention period.
- Expose current retention setting via API (see config endpoints).

#### API Endpoint: `/api/v1/activity/recent`

- **GET**: Query params:
  - `days` (int, 0–30, default 7)
  - `limit` (int, default 100, max 1000)
  - `type` (optional, filter by type)
- Returns: List of activity log entries, sorted by `timestamp` desc.
- Each entry: `{ id, timestamp, type, message, details, user }`
- If `days=0`, return only today’s activity; if `days` omitted, use default.
- Paginate if result set is large.

---

### 2.2. Background Task Status

#### Data Model

- If not already present, create a `background_task_status` table or in-memory store:
  - `task_name` (PK)
  - `last_run` (UTC)
  - `next_run` (UTC, if scheduled)
  - `status` (enum: running, idle, error, etc.)
  - `last_error` (text/JSON)
  - `last_result` (JSON/text, e.g., stats, counts)
- Update this table/store at the start/end/error of each background task.

#### API Endpoint: `/api/v1/background-tasks/status`

- **GET**: Returns a list of all background tasks with:
  - `task_name`, `last_run`, `next_run`, `status`, `last_error`, `last_result`
- Ensure this endpoint is fast and always up-to-date.

---

### 2.3. Active Streams Count

#### acexy Integration

- If acexy is used, query its API endpoint (e.g., `/api/v1/streams/active` or similar) for current active streams count.
- If only acestream is available, check for any status endpoint or CLI command that can provide this info; if not possible, return `{ count: null }` and document limitation.
- Cache result for a few seconds to avoid overloading acexy/acestream.

#### API Endpoint: `/api/v1/streams/active`

- **GET**: Returns `{ count: int|null, source: 'acexy'|'acestream'|'unavailable' }`
- Handle errors gracefully and log failures to activity log.

---

### 2.4. Warp Status

#### Data Source

- Query warp service/module for current status (connected, disconnected, error, etc.), last connection time, error details if any.

#### API Endpoint: `/api/v1/warp/status`

- **GET**: Returns `{ status: string, last_connected: datetime, error: string|null, details: object }`
- Ensure this endpoint is robust and does not block on slow network calls.

---

### 2.5. Configuration Endpoints

#### API Endpoint: `/api/v1/config/dashboard`

- **GET**: Returns `{ retention_days: int, auto_refresh_interval: int }`
- **PATCH/POST**: Accepts `{ retention_days: int, auto_refresh_interval: int }` (validate: 0–30 days, interval reasonable, e.g., 10–600 seconds)
- Store config in DB (settings table) or config file.
- Changes should take effect immediately for new queries/refreshes.

---

### 2.6. Documentation & Testing

- Document all new endpoints, data models, and settings in API docs.
- Add/extend unit and integration tests for:
  - Activity logging and retention
  - Background task status updates
  - Streams/warp endpoints
  - Config endpoints
- Test error cases, large data sets, and edge cases (e.g., 0-day retention).

---

## 3. Frontend Implementation Plan

### 3.1. State Management

- Add React hooks/services for:
  - Fetching recent activity (`/api/v1/activity/recent`)
  - Fetching background task status (`/api/v1/background-tasks/status`)
  - Fetching active streams (`/api/v1/streams/active`)
  - Fetching warp status (`/api/v1/warp/status`)
  - Fetching and updating dashboard config (`/api/v1/config/dashboard`)
- Use React Query or similar for caching, refetching, and error handling.

---

### 3.2. Dashboard UI Enhancements

#### Recent Activity

- Display a scrollable list/table of recent activity:
  - Columns: Timestamp, Type (icon/color), Message, Details (expandable/collapsible), User (if present)
  - Allow filtering by type (dropdown/chips)
  - Show retention period selector (0–30 days, slider or dropdown)
  - Show message if no activity in period
  - Paginate or virtualize if large data set

#### Background Tasks

- List all background tasks with:
  - Name, Last Run, Next Run, Status (color/icon), Last Error (expandable), Last Result (expandable)
  - Show loading and error states
  - Option to manually trigger certain tasks (if supported by backend)

#### Active Streams & Warp Status

- Show real-time count of active streams (with source: acexy/acestream/unavailable)
- Show warp status (connected/disconnected/error), last connected time, error details if any
- Use clear icons/colors for status

#### Auto-Refresh Controls

- Add toggle for auto-refresh (on/off)
- Add interval selector (dropdown or slider: 10s, 30s, 1m, 5m, 10m)
- Use setInterval or React Query refetchInterval to update all dashboard data
- Show last refreshed time

#### Error & Loading States

- All sections must handle loading and error states gracefully (spinners, alerts, retry buttons)
- If backend returns error or data is unavailable, show clear message and fallback UI

---

### 3.3. API Integration

- Update or create service modules for all new/updated endpoints
- Ensure all data is fetched live, not mocked
- Use consistent error handling and data validation

---

### 3.4. Testing & Polish

- Add/extend tests for all new UI features and error cases
- Ensure settings (retention, auto-refresh) persist and are respected
- Polish UI for clarity, accessibility, and usability
- Test with large data sets and slow/failed backend responses

---

## 4. Risks & Considerations

- **Data Volume**: Use indexed queries, pagination, and efficient data fetching for activity logs.
- **acexy/Acestream API**: If active streams count is not available, document and handle gracefully in UI.
- **User Experience**: Ensure auto-refresh does not overload backend or degrade UX; throttle requests as needed.
- **Security**: Protect sensitive info in logs/status endpoints; restrict access if needed.
- **Backward Compatibility**: Ensure new endpoints do not break existing clients.

---

## 5. Next Steps

1. Design and implement backend data model, migrations, and endpoints as detailed above.
2. Integrate and test backend changes, including logging and retention.
3. Update frontend to consume new endpoints and provide full UI/UX as specified.
4. Test, document, and polish; review with stakeholders for feedback.

---

## 6. Actionable Tasks for Coding Assistants

### Backend Tasks

1. **Activity Log Table**
   - Create Alembic migration for `activity_log` table as specified.
2. **Logging Utility**
   - Implement `log_activity` utility and integrate into scrapers, background tasks, and error handlers.
3. **Retention Policy**
   - Add retention config to settings and implement scheduled cleanup job.
4. **Activity Log API**
   - Implement `/api/v1/activity/recent` endpoint with filtering, pagination, and retention logic.
5. **Background Task Status Table**
   - Create/extend `background_task_status` table or in-memory store.
6. **Background Task Status API**
   - Implement `/api/v1/background-tasks/status` endpoint.
7. **Active Streams API**
   - Integrate with acexy/acestream and implement `/api/v1/streams/active` endpoint.
8. **Warp Status API**
   - Implement `/api/v1/warp/status` endpoint.
9. **Dashboard Config API**
   - Implement `/api/v1/config/dashboard` GET and PATCH/POST endpoints.
10. **Testing & Documentation**
    - Add/extend tests and update API documentation for all new endpoints and models.

### Frontend Tasks

1. **API Service Modules**
   - Create/update service modules for all new/updated endpoints.
2. **State Management**
   - Add hooks for fetching and updating activity, task status, streams, warp, and config.
3. **Recent Activity UI**
   - Implement scrollable, filterable, paginated activity log with retention selector.
4. **Background Tasks UI**
   - Display all background tasks with status, errors, and results.
5. **Streams & Warp UI**
   - Show real-time active streams and warp status with clear indicators.
6. **Auto-Refresh Controls**
   - Add toggle and interval selector for auto-refresh; wire up to all dashboard data.
7. **Error & Loading States**
   - Ensure all sections handle errors and loading gracefully.
8. **Testing & Polish**
   - Add/extend tests, ensure settings persist, and polish UI for usability and accessibility.

---

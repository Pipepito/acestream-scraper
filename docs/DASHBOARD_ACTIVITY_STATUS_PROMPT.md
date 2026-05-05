# Dashboard Activity & Status System: Implementation Prompt (backend)

You are an expert full-stack developer and prompt engineer. Your task is to design and implement a robust, production-ready dashboard activity and status system for a modern web application. The dashboard must provide real-time, actionable insights into system activity, background tasks, stream status, and configuration, with a focus on configurability, reliability, and user experience.

## Requirements

- **Recent Activity Log**: Store and expose recent activity (scrapes, background tasks, errors, user actions, system events, etc.) with user-configurable retention (0–30 days, default 7).
- **Background Task Status**: Expose last run, next run, status, errors, and results for all background tasks (scraping, EPG refresh, playlist generation, etc.).
- **Active Streams Count**: Expose the number of active streams (preferably via acexy, fallback to acestream if possible; handle gracefully if not available).
- **Warp Status**: Expose current warp status (connected, disconnected, error, etc.) and relevant details.
- **Auto-Refresh & Retention Controls**: User can set auto-refresh interval (e.g., 10s–10min) and retention period (0–30 days).
- **All data must be live, not mocked.**
- **Robust error handling and clear loading states in UI.**

## Backend Implementation (backend)

- For each feature, create new modules/files if they do not exist, following the backend project structure:
  - Endpoints: `/backend/app/api/endpoints/`
  - Services: `/backend/app/services/`
  - Repositories: `/backend/app/repositories/`
  - Tasks: `/backend/app/tasks/`
  - Utils: `/backend/app/utils/`
- Implement a SQLAlchemy data model for activity logs, including fields for id, timestamp, type, message, details, and user. Place the model in `/backend/app/models/`.
- Provide Alembic (or equivalent) migrations for all new tables.
- Implement a logging utility for recording activity from scrapers, background tasks, user actions, and system events. Ensure error stack traces and context are captured. Place this in `/backend/app/utils/`.
- Store retention configuration in a settings table or config file. Implement a scheduled cleanup job in `/backend/app/tasks/` to purge logs older than the retention period.
- Expose a `/api/v1/activity/recent` endpoint in `/backend/app/api/endpoints/`, supporting filtering by days (0–30), type, and pagination. Return activity entries sorted by timestamp descending. Register the endpoint in the API router.
- Track background task status in a table or in-memory store, including last run, next run, status, last error, and last result. Expose this via `/api/v1/background-tasks/status`.
- Integrate with acexy or acestream to provide a `/api/v1/streams/active` endpoint returning the current active streams count. Handle unavailability gracefully.
- Expose warp status via `/api/v1/warp/status`, including connection state, last connected time, and error details.
- Provide a `/api/v1/config/dashboard` endpoint for getting and updating retention and auto-refresh settings. Validate all inputs.
- Register all new endpoints in the API router and ensure they are included in the OpenAPI schema (`openapi.json`).
- Document all endpoints and add/extend tests for all new models and APIs.
- **Add/extend Python unit and integration tests in `/backend/tests/` to cover all new endpoints, models, and business logic.**
- **Do not make any changes to the legacy `/app` folder in the repository root.**

## Frontend Implementation (frontend)

- For each feature, create or update API service modules in `/frontend/src/services/`.
- Add React hooks/services for fetching and updating activity logs, background task status, streams, warp status, and dashboard config. Use React Query or similar for caching and refetching. Place hooks in `/frontend/src/hooks/`.
- Implement a dashboard UI in `/frontend/src/pages/Dashboard.tsx` with:
  - A scrollable, filterable, paginated activity log with retention selector, displaying real data from the backend.
  - A background tasks section showing all tasks, their status, errors, and results, using live data.
  - Real-time display of active streams and warp status with clear indicators, using live data.
  - Auto-refresh controls (toggle and interval selector) affecting all dashboard data. These controls must persist user settings and update all sections at the configured interval.
  - Robust error and loading states for all sections, with clear user feedback.
- Ensure all settings persist and are respected. Polish UI for clarity, accessibility, and usability.
- Add/extend tests for all new UI features and error cases.
- Import and use all new services and hooks in the relevant pages/components.

## Output Format

- All backend code should be production-ready Python (FastAPI preferred), with SQLAlchemy models, migrations, and OpenAPI-compliant endpoints. All endpoints must return data in a consistent, documented JSON schema.
- All frontend code should be production-ready React (TypeScript), using functional components, hooks, and Material UI (or similar modern UI library).
- All configuration and settings should be validated and persisted.
- All code should be well-documented and tested.
- **All backend tests must be placed in `/backend/tests/` and cover all new endpoints, models, and business logic.**

## Examples

- Example activity log entry:
  - `{ "id": 1, "timestamp": "2025-07-10T12:00:00Z", "type": "scrape", "message": "Scrape completed", "details": {"duration": 12.3}, "user": null }`
- Example background task status:
  - `{ "task_name": "epg_refresh", "last_run": "2025-07-10T11:00:00Z", "next_run": "2025-07-10T13:00:00Z", "status": "idle", "last_error": null, "last_result": {"programs": 1200} }`
- Example streams count:
  - `{ "count": 5, "source": "acexy" }`
- Example warp status:
  - `{ "status": "connected", "last_connected": "2025-07-10T10:00:00Z", "error": null, "details": {} }`

## Notes

- All endpoints and UI must handle errors and loading states gracefully, with clear user feedback.
- All data must be live and up-to-date, with no static or mocked values.
- The system must be secure, efficient, and scalable for large data volumes.
- All features must be fully tested and documented.
- All new modules, endpoints, and services must be imported and registered as needed in the project.
- **All backend tests for new features must be placed in `/backend/tests/` and provide full coverage for endpoints, models, and business logic.**
- **Do not make any changes to the legacy `/app` folder in the repository root.**

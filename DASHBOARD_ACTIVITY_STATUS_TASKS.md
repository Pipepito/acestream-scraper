# Dashboard Activity & Status System: Task List

This file tracks the implementation progress for the dashboard activity and status system as described in `DASHBOARD_ACTIVITY_STATUS_PROMPT.md`.

## Backend Implementation

- [x] Activity Log: SQLAlchemy model, migration, logging utility, repository, service
- [x] Activity Log: `/api/v1/activity/recent` endpoint (filtering, pagination, registration)
- [x] Activity Log: Scheduled cleanup task for retention
- [x] Migration script creates all tables and works for fresh DB
- [x] Unit/integration tests for activity log endpoint
- [x] Background Task Status: model/store
- [x] Background Task Status: service
- [x] Background Task Status: `/api/v1/background-tasks/status` endpoint
- [x] Streams Count: service (acexy/acestream integration)
- [x] Streams Count: `/api/v1/streams/active` endpoint
- [x] Warp Status: service
- [x] Warp Status: `/api/v1/warp/status` endpoint
- [x] Dashboard Config: model/service (retention, auto-refresh)
- [x] Dashboard Config: `/api/v1/config/dashboard` endpoint
- [x] Register all new endpoints in API router/OpenAPI
- [x] Unit/integration tests for all new endpoints/models/business logic

## Frontend Implementation

- [x] API service modules in `/frontend/src/services/`
- [x] React hooks/services in `/frontend/src/hooks/`
- [x] Dashboard UI in `/frontend/src/pages/Dashboard.tsx`
- [x] Auto-refresh/retention controls, error/loading states, settings persistence
- [x] Tests for all new UI features and error cases

---

**This file will be updated and checked off as each item is completed.**

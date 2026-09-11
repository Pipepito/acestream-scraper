# CHANNEL_MANAGEMENT_PROMPT.md

You are an expert migration and parity engineer. Your task is to ensure that the V2 acestream-scraper project (FastAPI backend, React frontend) achieves full feature parity and UX parity with the original V1 Flask-based app for all channel management functionality.

You must analyze and compare the following areas for channel management:

- V1: `app/controllers`, `app/services`, `app/repositories`, `app/static/js`, `app/templates`
- V2: `backend/app/api/endpoints/channels.py`, `backend/app/services/channel_service.py`, `backend/app/repositories/channel_repository.py`, `frontend/src/pages/Channels.tsx` (and related components/services)

**All new work, improvements, and fixes must be implemented exclusively in the canonical codebase:**

- V2 backend: `backend` (e.g., `app/api/endpoints/channels.py`, `app/services/channel_service.py`, `app/repositories/channel_repository.py`)
- V2 frontend: `frontend` (e.g., `src/pages/Channels.tsx` and related components/services)

For each feature, you must:

- Identify if it is present in V1, and if so, how it is implemented (controller, service, template, JS, etc).
- Identify if it is present in V2, and if so, how it is implemented (endpoint, service, repository, React component, etc).
- Mark the feature as ✅ Completed, ⚠️ Partially Complete, or ❌ Missing in V2.
- For any feature that is not fully complete, provide a clear, actionable requirement for what must be implemented or improved in V2 (frontend and/or backend).
- For features that are improved in V2, briefly note the improvement.

# Channel Management Parity Checklist

| Feature                                   | V1 Implementation              | V2 Implementation             | Status                | Action/Notes                                                                          |
| ----------------------------------------- | ------------------------------ | ----------------------------- | --------------------- | ------------------------------------------------------------------------------------- |
| CRUD (Create, Read, Update, Delete)       | [controllers, templates, JS]   | [REST API, React UI]          | ✅ Completed          | Full parity, improved API and UI                                                      |
| Channel ID Generation                     | [Backend auto, int/uuid]       | [Backend auto, uuid]          | ✅ Completed          | Now backend-generated in V2                                                           |
| Group Management                          | [controllers, templates, JS]   | [API, React UI]               | ✅ Completed          | Parity                                                                                |
| Channel Status (online/offline)           | [service, JS, UI]              | [API, React, status endpoint] | ✅ Completed          | Improved real-time status in V2                                                       |
| Channel Search/Filter                     | [basic, JS, UI]                | [advanced, API, React]        | ✅ Completed          | Improved in V2                                                                        |
| Pagination                                | [none]                         | [API, React]                  | ✅ Completed          | Improved in V2                                                                        |
| Bulk Operations                           | [batch modals, JS, controller] | [UI present, backend partial] | ⚠️ Partially Complete | Implement backend endpoints in `backend` and wire up React UI in `frontend`           |
| Channel-EPG Association                   | [controller, template]         | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel-TV Association                    | [controller, template]         | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Logo/Metadata                     | [controller, template]         | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Import (M3U/EPG)                  | [controller, JS, template]     | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Export (CSV, M3U)                 | [controller, JS, template]     | [API (M3U only), React]       | ⚠️ Partially Complete | Implement CSV export in `backend` and `frontend`                                      |
| Channel Deletion                          | [controller, template, JS]     | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Edit                              | [modal, template, JS]          | [React dialog/page, API]      | ✅ Completed          | Parity                                                                                |
| Channel Source Tracking                   | [controller, template]         | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Sorting                           | [limited, JS, template]        | [advanced, React, API]        | ✅ Completed          | Improved in V2                                                                        |
| Channel Import Validation                 | [controller, JS]               | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Error Handling                    | [controller, JS, template]     | [API, React]                  | ✅ Completed          | Parity                                                                                |
| Channel Activity Log                      | [controller, template]         | [API, React]                  | ⚠️ Partially Complete | Enhance React activity log in `frontend` to match V1 detail                           |
| Advanced Filtering                        | [limited, JS]                  | [React, API]                  | ⚠️ Partially Complete | Add custom field filters to React UI/API in `frontend` and `backend`                  |
| Modals/Dialogs (Batch Assign, Quick Edit) | [template, JS]                 | [React UI]                    | ❌ Missing            | Implement missing modals/dialogs in `frontend`                                        |
| Inline Edit/Quick Actions                 | [template, JS]                 | [React UI]                    | ❌ Missing            | Add inline edit/quick actions to React table in `frontend`                            |
| Error Handling (UI/UX)                    | [template, JS]                 | [React UI]                    | ⚠️ Partially Complete | Ensure all error cases are handled gracefully in `frontend`                           |
| Test Coverage (Edge Cases)                | [unit, integration]            | [pytest, React tests]         | ⚠️ Partially Complete | Add more tests for bulk ops, import, error handling in `backend` and `frontend`       |

# Output Format

- Output as a markdown table as above, followed by a section listing all actionable requirements for incomplete features.
- For each incomplete feature, provide a clear, concise, and actionable requirement (e.g. "Implement backend endpoint for bulk channel delete and wire up to React UI").
- Do not include code blocks unless specifically requested.

# Actionable Requirements

- Implement backend endpoints for bulk channel operations (edit, delete, activate) in `backend` and connect to React UI in `frontend`.
- Add CSV export functionality for channels in `backend` and `frontend`.
- Implement missing modals/dialogs in React for batch assign and quick edit in `frontend`.
- Enhance React activity log UI for channels to match V1 detail in `frontend`.
- Add advanced/custom field filtering to React UI and backend API in `frontend` and `backend`.
- Add inline edit and quick actions to React channel table in `frontend`.
- Ensure all error cases are handled gracefully in React UI in `frontend`.
- Add more tests for edge cases, especially for bulk operations, import, and error handling in `backend` and `frontend`.

# Notes

- Mark features as completed as progress is made.
- Update this prompt as new gaps are discovered or closed.
- Use this as a living checklist for full channel management migration and parity.

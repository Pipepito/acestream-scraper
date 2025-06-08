# Copilot/AI Instructions – Backend (FastAPI, Python)

Welcome, Copilot/AI! This is a backend FastAPI project for Acestream Scraper.  
Here’s how you should assist:

---

## 1. General Rules

- Use Python 3.11+ syntax and typing everywhere.
- All API request/response bodies must use Pydantic DTOs.
- Each module (api, services, dtos, models, repositories) should be single-responsibility.
- All classes and functions must have descriptive docstrings.

---

## 2. Project Structure

- `app/dtos/` – Pydantic DTOs (fully typed, docstringed, one per entity/request/response)
- `app/services/` – Business logic (scraper, playlist, epg, warp, etc.)
- `app/repositories/` – DB/data access (SQLAlchemy, no business logic)
- `app/api/` – FastAPI routers, one per domain (e.g. channels, urls, playlist, status)
- `app/core/` – Central config, settings, startup logic
- `app/static/` – Compiled frontend assets (served at `/`)

---

## 3. API & DTOs

- Every endpoint uses a well-documented DTO for input/output.
- Every DTO has field descriptions and examples.
- All endpoints are versioned (e.g. `/api/v1/channels/`).
- All endpoints and DTOs must appear in the OpenAPI schema.

---

## 4. Copilot/AI Prompts

- “Write a Pydantic DTO for AcestreamChannel with id, name, tvg_id, tvg_name, logo, group, is_online.”
- “Generate a FastAPI router for /api/v1/channels/ with GET, POST, PATCH, DELETE.”
- “Add a service function to scrape a URL and return channels.”
- “Write a test for the /api/v1/playlist endpoint.”

---

## 5. Error Handling

- All errors must return descriptive messages and correct HTTP status codes.
- Use FastAPI’s exception handlers for validation and server errors.

---

## 6. Tests

- All new features must include pytest-based unit/integration tests.
- Test all edge cases (bad input, missing resources, etc).

---

## 7. Static Frontend Integration

- Serve all files in `app/static/` at `/`.
- Fallback to `index.html` for SPA routing.

---

## 8. Formatting/Linting

- Use black, isort, flake8. All code must pass linting.
- No untyped code.

---

## 9. Authentication (if enabled)

- Use OAuth2/JWT or FastAPI security for protected endpoints.

---

## 10. Documentation

- All new endpoints, DTOs, and services must have docstrings.
- OpenAPI must always be current.

---

**For a new feature, always start with the DTO definition and docstring.**
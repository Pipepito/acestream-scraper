# Deployment & Dockerization

## Goals

- **Single endpoint:** Backend (API) and frontend (React) are served from the same URL/port (e.g., http://localhost:8000).
- **Multi-arch (x86_64 and arm64) Docker builds.**
- **Easy dev/prod setup with Docker Compose.**

---

## Serving React from FastAPI

- Build React app (`npm run build`).
- Copy build output to `backend/app/static/`.
- FastAPI serves:
  - `/api/*` - API endpoints.
  - `/*` - React SPA (static files + index.html fallback).

**Example FastAPI main.py:**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(...)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")

@app.get("/{full_path:path}")
async def react_spa(full_path: str):
    return FileResponse("app/static/index.html")
```

---

## Docker Compose Example

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app/static:/app/app/static
    environment:
      - ...
  frontend:
    build: ./frontend
    command: npm run build && cp -r dist/* /app/app/static/
    volumes:
      - ./backend/app/static:/app/app/static
      - ./frontend:/app
    depends_on:
      - backend
```

- In production, only `backend` is needed; React is a static build.

---

## ARM64 Support

- Use multi-arch base images (`python:3.11-slim`, `node:20-alpine`).
- Test on both x86_64 and arm64 hosts (Raspberry Pi, Apple Silicon, etc.).

---

## Static Assets

- All frontend assets are placed in `backend/app/static` and versioned if needed.

---

**See [`docs/dev/backend.md`](../dev/backend.md) and [`docs/dev/frontend.md`](../dev/frontend.md) for developer setup.**
"""
Main application entry point for Acestream Scraper v2 backend
"""
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.api import api_router
from app.config.settings import settings

app = FastAPI(
    title="Acestream Scraper API",
    description="API for scraping and managing Acestream channels",
    version="2.0.0",
)

# Add API routes with versioning
app.include_router(api_router, prefix="/api/v1")

# Add CORS middleware if needed
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Static files serving
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.FRONTEND_BUILD_PATH)
os.makedirs(frontend_dir, exist_ok=True)  # Ensure directory exists

# Check what static directories exist in the frontend build
static_dirs = []
for dirname in ["static", "assets"]:
    if os.path.isdir(os.path.join(frontend_dir, dirname)):
        static_dirs.append(dirname)

# Mount static files directories that exist
for dirname in static_dirs:
    app.mount(f"/{dirname}", StaticFiles(directory=os.path.join(frontend_dir, dirname)), name=dirname)

# Serve React app - handle all other routes to support client-side routing
@app.exception_handler(StarletteHTTPException)
async def spa_server(request: Request, exc: StarletteHTTPException):
    """Serve SPA for all non-API routes."""
    if exc.status_code == 404 and not request.url.path.startswith("/api"):
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    raise exc

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve the React frontend index page."""
    try:
        with open(os.path.join(frontend_dir, "index.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # If frontend build doesn't exist yet, return a placeholder
        return HTMLResponse(content="<html><body><h1>Acestream Scraper</h1><p>Frontend not built yet. Please run 'npm run build' in the frontend directory.</p></body></html>")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

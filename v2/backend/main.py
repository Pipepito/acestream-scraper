"""
Main application entry point for Acestream Scraper v2 backend
"""
import uvicorn
from fastapi import FastAPI
from app.api.api import api_router
from app.config.settings import settings

app = FastAPI(
    title="Acestream Scraper API",
    description="API for scraping and managing Acestream channels",
    version="2.0.0",
)

# Add API routes
app.include_router(api_router, prefix="/api")

# Add CORS middleware if needed
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

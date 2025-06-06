"""
API endpoints for scraper management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.config.database import get_db
from app.schemas.scraper import ScraperRequest, ScraperResult, URLResponse
from app.services.scraper_service import ScraperService

router = APIRouter()


@router.post("/scrape", response_model=ScraperResult)
async def scrape_url(
    request: ScraperRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Scrape a URL for Acestream channels.
    
    Request body:
    - url: The URL to scrape
    - url_type: (Optional) URL type ('auto', 'regular', 'zeronet')
    - run_async: (Optional) Run scraping in background
    """
    scraper_service = ScraperService(db)
    
    if request.run_async:
        # Run in background
        background_tasks.add_task(
            scraper_service.scrape_url, 
            request.url, 
            request.url_type
        )
        return ScraperResult(
            message="Scraping started in background", 
            channels=[],
            url=request.url
        )
    else:
        # Run synchronously
        channels, status = await scraper_service.scrape_url(request.url, request.url_type)
        
        if status != "OK":
            raise HTTPException(status_code=400, detail=f"Scraping failed: {status}")
            
        return ScraperResult(
            message="Scraping completed successfully", 
            channels=channels,
            url=request.url
        )


@router.get("/urls", response_model=List[URLResponse])
async def get_scraped_urls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of URLs that have been scraped.
    """
    scraper_service = ScraperService(db)
    return scraper_service.get_scraped_urls(skip=skip, limit=limit)

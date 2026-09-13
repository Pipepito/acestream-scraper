from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_url_service
from app.services.url_service import URLService

router = APIRouter()

@router.post("/{url_id}/refresh", status_code=202)
def refresh_url(url_id: int, url_service: URLService = Depends(get_url_service)):
    """
    Manually refresh a specific URL by ID.
    """
    refreshed = url_service.refresh_url(url_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="URL not found or refresh failed")
    return {"message": f"Refresh started for URL {url_id}", "success": True}

@router.post("/refresh-all", status_code=202)
def refresh_all_urls(url_service: URLService = Depends(get_url_service)):
    """
    Manually refresh all URLs.
    """
    count = url_service.refresh_all_urls()
    return {"message": f"Refresh started for {count} URLs", "success": True, "count": count}

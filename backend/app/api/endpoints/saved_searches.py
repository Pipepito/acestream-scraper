"""Saved-search configuration, read-only preview and FIFO run admission."""
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.saved_searches import (SavedSearchInput, SavedSearchUpdate, SavedSearchList,
    SavedSearchView, SavedSearchPreviewRequest, SavedSearchPreview, SavedSearchRunRequest)
from app.services.saved_search_service import SavedSearchService
from app.services.task_service import task_service
router = APIRouter()


@router.get('', response_model=SavedSearchList)
def list_searches(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    return SavedSearchService(db).list(offset, limit)


@router.post('', response_model=SavedSearchView, status_code=201)
def create_search(data: SavedSearchInput, db: Session = Depends(get_db)):
    return SavedSearchService(db).save(data)


@router.post('/preview', response_model=SavedSearchPreview)
def preview(data: SavedSearchPreviewRequest, db: Session = Depends(get_db)):
    return SavedSearchService(db).preview(data)


@router.get('/{search_id}', response_model=SavedSearchView)
def get_search(search_id: int, db: Session = Depends(get_db)):
    return SavedSearchService(db).get(search_id)


@router.patch('/{search_id}', response_model=SavedSearchView)
def update_search(search_id: int, data: SavedSearchUpdate, db: Session = Depends(get_db)):
    return SavedSearchService(db).save(data, search_id)


@router.delete('/{search_id}', status_code=204)
def delete_search(search_id: int, expected_revision: int = Query(ge=1), db: Session = Depends(get_db)):
    SavedSearchService(db).delete(search_id, expected_revision)
    return Response(status_code=204)


@router.post('/{search_id}/run', response_model=SavedSearchView, status_code=202)
def run_search(search_id: int, data: SavedSearchRunRequest, db: Session = Depends(get_db)):
    return SavedSearchService(db).run(search_id, data, task_service)

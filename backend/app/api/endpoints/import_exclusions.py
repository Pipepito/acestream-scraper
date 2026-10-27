"""Authenticated policy endpoints; sync handlers run outside the event loop."""
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.import_exclusions import (ExclusionInput, ExclusionUpdate, ExclusionList,
    ExclusionWrite, ExclusionPreviewRequest, ExclusionPreview)
from app.services.import_exclusion_service import ImportExclusionService
router = APIRouter()


@router.get('', response_model=ExclusionList)
def list_rules(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
               enabled: bool | None = None, rule_id: int | None = Query(None, ge=1), db: Session = Depends(get_db)):
    return ImportExclusionService(db).list(offset, limit, enabled, rule_id)


@router.post('', response_model=ExclusionWrite, status_code=201)
def create_rule(data: ExclusionInput, db: Session = Depends(get_db)):
    return ImportExclusionService(db).save(data)


@router.post('/preview', response_model=ExclusionPreview)
def preview(data: ExclusionPreviewRequest, db: Session = Depends(get_db)):
    return ImportExclusionService(db).preview(data)


@router.patch('/{rule_id}', response_model=ExclusionWrite)
def update_rule(rule_id: int, data: ExclusionUpdate, db: Session = Depends(get_db)):
    return ImportExclusionService(db).save(data, rule_id)


@router.delete('/{rule_id}', status_code=204)
def delete_rule(rule_id: int, expected_revision: int = Query(ge=1), db: Session = Depends(get_db)):
    ImportExclusionService(db).delete(rule_id, expected_revision)
    return Response(status_code=204)

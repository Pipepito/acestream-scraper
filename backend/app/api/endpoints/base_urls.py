"""
CRUD endpoints for named stream base URLs (#62).
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.base_url_repository import BaseUrlRepository
from app.schemas.base_url import BaseUrlCreate, BaseUrlResponse, BaseUrlUpdate

router = APIRouter()


def _repo(db: Session = Depends(get_db)) -> BaseUrlRepository:
    return BaseUrlRepository(db)


@router.get("", response_model=List[BaseUrlResponse])
async def list_base_urls(repo: BaseUrlRepository = Depends(_repo)):
    return repo.get_all()


@router.post("", response_model=BaseUrlResponse, status_code=201)
async def create_base_url(payload: BaseUrlCreate, repo: BaseUrlRepository = Depends(_repo)):
    if repo.get_by_name(payload.name):
        raise HTTPException(status_code=409, detail=f"Base URL '{payload.name}' already exists")
    return repo.create(payload.name, payload.pattern, payload.is_default)


@router.patch("/{base_url_id}", response_model=BaseUrlResponse)
async def update_base_url(base_url_id: int, payload: BaseUrlUpdate,
                          repo: BaseUrlRepository = Depends(_repo)):
    entry = repo.get(base_url_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Base URL not found")
    if payload.name and payload.name != entry.name and repo.get_by_name(payload.name):
        raise HTTPException(status_code=409, detail=f"Base URL '{payload.name}' already exists")
    return repo.update(entry, name=payload.name, pattern=payload.pattern,
                       is_default=payload.is_default)


@router.delete("/{base_url_id}", status_code=204)
async def delete_base_url(base_url_id: int, repo: BaseUrlRepository = Depends(_repo)):
    entry = repo.get(base_url_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Base URL not found")
    repo.delete(entry)

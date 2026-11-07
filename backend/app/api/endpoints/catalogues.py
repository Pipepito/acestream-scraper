"""W3U preview/import endpoints. Blocking work stays in FastAPI's worker pool."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError
from fastapi.routing import APIRoute
from fastapi.exceptions import RequestValidationError
from app.config.database import get_db
from app.schemas.catalogue import (CataloguePreviewRequest, CatalogueSaveRequest, CatalogueSummary, CatalogueView,
    FolderAssignRequest, FolderAssignResult, FolderMatchPreview, FolderMatchApplyRequest, FolderMatchApplyResult)
from app.services.catalogue_service import CatalogueService, ConflictError

class PrivateInputRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def guarded(request):
            try:
                return await handler(request)
            except RequestValidationError:
                # Pydantic's default error includes the original input, which
                # can contain a signed URL, header value or entire local file.
                raise HTTPException(422, 'Invalid catalogue request. Check the input fields and size limits.') from None
        return guarded


router = APIRouter(route_class=PrivateInputRoute)


def service(db: Session = Depends(get_db)):
    return CatalogueService(db)


def invoke(call, *args):
    try:
        return call(*args)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValidationError:
        raise HTTPException(422, 'Catalogue data cannot form a valid event; check the source metadata.') from None
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        raise HTTPException(503, 'Catalogue operation failed; existing channels were preserved.') from None


@router.get('', response_model=list[CatalogueSummary])
def list_catalogues(svc: CatalogueService = Depends(service)):
    return svc.list()


@router.post('/preview', response_model=CatalogueView)
def preview_catalogue(request: CataloguePreviewRequest, svc: CatalogueService = Depends(service)):
    return invoke(svc.preview, request)


@router.post('', response_model=CatalogueView)
def save_catalogue(request: CatalogueSaveRequest, svc: CatalogueService = Depends(service)):
    return invoke(svc.save, request)


@router.get('/{catalogue_id}', response_model=CatalogueView)
def get_catalogue(catalogue_id: int, svc: CatalogueService = Depends(service)):
    return invoke(svc.get, catalogue_id)


@router.delete('/{catalogue_id}', status_code=204)
def delete_catalogue(catalogue_id: int, svc: CatalogueService = Depends(service)):
    if not svc.repository.delete(catalogue_id):
        raise HTTPException(404, 'Catalogue not found')


@router.post('/{catalogue_id}/folders/{entry_id}/tv-channel', response_model=FolderAssignResult)
def assign_folder(catalogue_id: int, entry_id: str, request: FolderAssignRequest, svc: CatalogueService = Depends(service)):
    """Assign every imported stream under the folder (descendants included) to one TV channel."""
    return invoke(svc.assign_folder, catalogue_id, entry_id, request)


@router.post('/{catalogue_id}/folder-matches/preview', response_model=FolderMatchPreview)
def preview_folder_matches(catalogue_id: int, svc: CatalogueService = Depends(service)):
    """Read-only: which folders match a TV channel by name, which are already assigned, which need a choice."""
    return invoke(svc.folder_matches, catalogue_id)


@router.post('/{catalogue_id}/folder-matches/apply', response_model=FolderMatchApplyResult)
def apply_folder_matches(catalogue_id: int, request: FolderMatchApplyRequest, svc: CatalogueService = Depends(service)):
    """Apply the chosen folder assignments in one transaction; a vanished folder or TV channel rejects the whole request."""
    return invoke(svc.apply_folder_matches, catalogue_id, request)


from app.schemas.catalogue import CatalogueEventPreviewRequest
from app.schemas.events import EventPreview


@router.post('/{catalogue_id}/events/preview', response_model=EventPreview)
def preview_event(catalogue_id: int, request: CatalogueEventPreviewRequest, svc: CatalogueService = Depends(service)):
    return invoke(svc.preview_event, catalogue_id, request)

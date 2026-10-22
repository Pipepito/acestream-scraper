"""Authenticated event endpoints; blocking work uses FastAPI's worker pool."""
from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from pydantic import ValidationError
from app.config.database import get_db
from app.schemas.events import EventImport, EventPreview, EventApply, EventView, EventList, EventUpdate
from app.services.event_service import EventService


class PrivateEventRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def guarded(request):
            try:
                return await handler(request)
            except RequestValidationError as exc:
                # Error locations/messages are useful, but input/context may hold
                # signed stream URLs or private publisher headers.
                errors = [{'loc': list(e['loc']), 'msg': e['msg']} for e in exc.errors()[:10]]
                raise HTTPException(422, detail=errors) from None
        return guarded


router = APIRouter(route_class=PrivateEventRoute)


def service(db: Session = Depends(get_db)):
    return EventService(db)


def invoke(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from None
    except ValidationError:
        raise HTTPException(503, 'Stored event data could not be read; existing events were preserved') from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    except Exception:
        raise HTTPException(503, 'Event operation failed; saved events were preserved') from None


@router.get('', response_model=EventList)
def list_events(search: str = Query('', max_length=200), sport: str = Query('', max_length=100),
                competition: str = Query('', max_length=200), source: str = Query('', max_length=200),
                day: date | None = None, zone: str = Query('UTC', max_length=100),
                upcoming: bool = False, followed: bool = False, archived: bool = False,
                offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                svc: EventService = Depends(service)):
    try:
        ZoneInfo(zone)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(422, 'Choose a valid IANA timezone') from None
    return invoke(svc.list, search=search, sport=sport, competition=competition, source=source,
                  date=day, zone=zone, upcoming=upcoming, followed=followed, archived=archived, offset=offset, limit=limit)


@router.post('/preview', response_model=EventPreview)
def preview_events(request: EventImport, svc: EventService = Depends(service)):
    return invoke(svc.preview, request)


@router.post('/apply', response_model=list[EventView])
def apply_events(request: EventApply, svc: EventService = Depends(service)):
    return invoke(svc.apply, request)


@router.get('/{event_id}', response_model=EventView)
def get_event(event_id: str, svc: EventService = Depends(service)):
    return invoke(svc.get, event_id)


@router.patch('/{event_id}', response_model=EventView)
def update_event(event_id: str, request: EventUpdate, svc: EventService = Depends(service)):
    return invoke(svc.update, event_id, request)

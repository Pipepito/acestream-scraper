"""HDHomeRun-style tuner routes (spec 7.1). This plan ships the byte relay and
the JSON 404; plan 4 adds discover/lineup/guide and the token-gated
settings/status router."""
from __future__ import annotations

import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError, engine_url_from_settings
from app.services.stream_relay import RELAY_HEADERS, ClosingStreamingResponse, EngineStreamError, relay_engine_stream
from app.services.tuner_network import require_tuner_network

hdhr_router = APIRouter(prefix="/tuner", dependencies=[Depends(require_tuner_network)], tags=["hdhomerun"])
router = APIRouter()  # /api/v1/tuner settings + status (plan 4)

_CONTENT_ID = re.compile(r"^[0-9a-fA-F]{40}$")


def _engine(db: Session) -> EngineClient:
    return EngineClient(engine_url_from_settings(SettingsRepository(db)))


def _relay_client_factory(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


def _validate_content_id(content_id: str) -> str:
    if not _CONTENT_ID.match(content_id):
        raise HTTPException(status_code=422, detail="content_id must be a 40-character hex string")
    return content_id.lower()


# GET and HEAD are two registrations of one handler rather than a single
# api_route(methods=["GET", "HEAD"]): FastAPI derives the operation id from the
# route name, so one route serving both methods emits the same operationId
# twice and the OpenAPI document is no longer valid.
@hdhr_router.head("/stream/{content_id}.ts", include_in_schema=False)
@hdhr_router.get(
    "/stream/{content_id}.ts",
    summary="MPEG-TS relay of one channel",
    response_class=Response,
    responses={200: {"content": {"video/mp2t": {"schema": {"type": "string", "format": "binary"}}}}},
)
async def tuner_stream(content_id: str, request: Request, db: Session = Depends(get_db)):
    """Relays the engine's MPEG-TS bytes. Unknown query params (transcode,
    duration) are ignored. HEAD answers headers only and never starts a
    session."""
    content_id = _validate_content_id(content_id)
    if request.method == "HEAD":
        return Response(status_code=200, headers=RELAY_HEADERS)
    # The settings read is a blocking DB call: keep it off the event loop.
    try:
        engine = await run_in_threadpool(_engine, db)
    except EngineUnavailableError as exc:
        raise APIError(code="ENGINE_UNAVAILABLE", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    peer = request.client.host if request.client else "?"
    iterator = relay_engine_stream(engine, content_id, f"tuner:{peer}", client_factory=_relay_client_factory)
    # The first chunk is pulled here so an engine failure becomes a 502 body
    # instead of a truncated 200 stream. Every path that does not hand the
    # iterator to a response closes the engine's connection pool itself.
    try:
        first = await iterator.__anext__()
    except EngineRefusedError as exc:
        engine.close()
        raise APIError(code="ENGINE_REFUSED", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    except EngineUnavailableError as exc:
        engine.close()
        raise APIError(code="ENGINE_UNAVAILABLE", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    except EngineStreamError as exc:
        engine.close()
        raise APIError(code="ENGINE_STREAM_FAILED", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    except StopAsyncIteration:
        engine.close()
        return Response(status_code=200, headers=RELAY_HEADERS)

    async def body():
        try:
            yield first
            async for chunk in iterator:
                yield chunk
        finally:
            await iterator.aclose()
            engine.close()

    return ClosingStreamingResponse(body(), headers=RELAY_HEADERS)


@hdhr_router.api_route("/{path:path}", methods=["GET", "HEAD", "POST"], include_in_schema=False)
async def tuner_not_found(path: str):
    # Tuner clients must never receive the SPA's index.html for a typo'd path.
    raise HTTPException(status_code=404, detail="Unknown tuner path")

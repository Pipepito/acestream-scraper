"""HDHomeRun-style tuner routes (spec 7.1/7.2).

``hdhr_router`` is token-free by design -- a tuner client cannot send
credentials -- and is gated by ``TUNER_ALLOWED_NETWORKS`` instead. ``router``
carries the operator-facing ``/api/v1/tuner`` settings and status, which the
API token protects like every other ``/api/v1`` route.
"""
from __future__ import annotations

import html
import re
from dataclasses import asdict
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import SessionLocal, get_db
from app.repositories.settings_repository import SettingsRepository
from app.schemas.tuner import TunerSettingsResponse, TunerSettingsUpdate, TunerStatusResponse, TunerUrls
from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError, engine_url_from_settings
from app.services.epg_service import EPGService
from app.services.player_service import player_service
from app.services.public_url_service import resolve_public_base_url
from app.services.stream_relay import RELAY_HEADERS, ClosingStreamingResponse, EngineStreamError, relay_engine_stream, relay_registry
from app.services.tuner_network import get_tuner_gate, require_tuner_network
from app.services.tuner_service import TunerService

hdhr_router = APIRouter(prefix="/tuner", dependencies=[Depends(require_tuner_network)], tags=["hdhomerun"])
router = APIRouter()  # /api/v1/tuner settings + status

_CONTENT_ID = re.compile(r"^[0-9a-fA-F]{40}$")


def _engine() -> EngineClient:
    """Read the configured engine URL through a session of its own.

    Deliberately not a ``Depends(get_db)`` parameter on the route: FastAPI
    releases a request-scoped session only after the response has been fully
    sent, so an hours-long relay would pin one pooled connection for the whole
    stream (5 + 10 overflow for the process) to serve a single settings read.
    """
    db = SessionLocal()
    try:
        return EngineClient(engine_url_from_settings(SettingsRepository(db)))
    finally:
        db.close()


def _tuner_count() -> int:
    """The configured concurrent-relay cap, read through a session of its own
    for the same reason as :func:`_engine`."""
    db = SessionLocal()
    try:
        return TunerService(db).settings().tuner_count
    finally:
        db.close()


def _relay_client_factory(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


def _validate_content_id(content_id: str) -> str:
    if not _CONTENT_ID.match(content_id):
        # APIError, not HTTPException: the 403 and the 502s on this router all
        # answer with the {"error": {...}} envelope and this must match.
        raise APIError(
            code="INVALID_CONTENT_ID",
            message="content_id must be a 40-character hex string",
            status_code=422,
            context={"content_id": content_id},
        )
    return content_id.lower()


def _public(request: Request, db: Session) -> str:
    """The origin external clients must use for the URLs we hand out."""
    return resolve_public_base_url(request, SettingsRepository(db)).url


def _discover(request: Request, db: Session) -> dict:
    """The discover.json body, also the source of device.xml's fields."""
    service = TunerService(db)
    settings = service.settings()
    public = _public(request, db)
    return {
        "FriendlyName": settings.friendly_name, "Manufacturer": "Silicondust", "ModelNumber": "HDTC-2US",
        "FirmwareName": "hdhomeruntc_atsc", "FirmwareVersion": "20240101", "DeviceID": service.device_id(), "DeviceAuth": "",
        "BaseURL": f"{public}/tuner", "LineupURL": f"{public}/tuner/lineup.json", "TunerCount": settings.tuner_count,
    }


# --- HDHomeRun discovery -----------------------------------------------------
# All of these are include_in_schema=False: they are a device protocol Jellyfin
# and Plex speak, not part of the documented API.
@hdhr_router.get("/discover.json", include_in_schema=False)
def discover(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    return JSONResponse(_discover(request, db), headers={"Cache-Control": "no-store"})


@hdhr_router.get("/lineup.json", include_in_schema=False)
def lineup_json(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    public = _public(request, db)
    entries = TunerService(db).build_lineup().entries
    return JSONResponse(
        [{"GuideNumber": e.guide_number, "GuideName": e.guide_name, "URL": f"{public}/tuner/stream/{e.content_id}.ts"} for e in entries],
        headers={"Cache-Control": "no-store"},
    )


@hdhr_router.get("/lineup_status.json", include_in_schema=False)
def lineup_status() -> dict:
    # No scan to run: the lineup is whatever the database holds right now.
    return {"ScanInProgress": 0, "ScanPossible": 0, "Source": "Cable", "SourceList": ["Cable"]}


@hdhr_router.api_route("/lineup.post", methods=["GET", "POST"], include_in_schema=False)
def lineup_post() -> Response:
    # Media servers post here to trigger a channel scan; accepting it is enough.
    return Response(status_code=200)


@hdhr_router.get("/device.xml", include_in_schema=False)
def device_xml(request: Request, db: Session = Depends(get_db)) -> Response:
    info = _discover(request, db)
    body = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<root xmlns="urn:schemas-upnp-org:device-1-0">\n'
        '  <specVersion><major>1</major><minor>0</minor></specVersion>\n'
        f'  <URLBase>{html.escape(info["BaseURL"])}</URLBase>\n'
        '  <device>\n'
        '    <deviceType>urn:schemas-upnp-org:device:MediaServer:1</deviceType>\n'
        f'    <friendlyName>{html.escape(info["FriendlyName"])}</friendlyName>\n'
        '    <manufacturer>Silicondust</manufacturer>\n'
        '    <modelName>HDTC-2US</modelName>\n'
        '    <modelNumber>HDTC-2US</modelNumber>\n'
        f'    <serialNumber>{info["DeviceID"]}</serialNumber>\n'
        f'    <UDN>uuid:{info["DeviceID"]}</UDN>\n'
        '  </device>\n'
        '</root>\n'
    )
    return Response(content=body, media_type="application/xml")


# --- guide and playlist exports ---------------------------------------------
@hdhr_router.get("/guide.xml", include_in_schema=False)
def guide_xml(db: Session = Depends(get_db)) -> Response:
    """XMLTV keyed by GuideNumber -- how a media server matches an HDHomeRun
    lineup to its guide. Uncompressed: some servers refuse a gzipped guide."""
    service = TunerService(db)
    return Response(content=service.build_guide_xml(service.build_lineup()), media_type="application/xml",
                    headers={"Cache-Control": "no-store"})


@hdhr_router.get("/playlist.m3u", include_in_schema=False)
def playlist_m3u(request: Request, db: Session = Depends(get_db)) -> PlainTextResponse:
    """The same lineup as an M3U, for servers configured with an M3U tuner."""
    service = TunerService(db)
    return PlainTextResponse(service.build_playlist_m3u(service.build_lineup(), _public(request, db)),
                             headers={"Cache-Control": "no-store"})


@hdhr_router.get("/epg.xml", include_in_schema=False)
def epg_xml(db: Session = Depends(get_db)) -> Response:
    """XMLTV keyed by the upstream EPG ids, restricted to the lineup: the guide
    that goes with playlist.m3u, whose tvg-ids are those same ids."""
    ids = [entry.tv_channel_id for entry in TunerService(db).build_lineup().entries]
    return Response(content=EPGService(db).generate_epg_xml(tv_channel_ids=ids), media_type="application/xml",
                    headers={"Cache-Control": "no-store"})


# --- stream relay ------------------------------------------------------------
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
async def tuner_stream(content_id: str, request: Request):
    """Relays the engine's MPEG-TS bytes. Unknown query params (transcode,
    duration) are ignored. HEAD answers headers only and never starts a
    session."""
    content_id = _validate_content_id(content_id)
    if request.method == "HEAD":
        return Response(status_code=200, headers=RELAY_HEADERS)
    # The cap is checked before the engine is touched, so a busy tuner answers
    # 503 rather than starting a session it is about to refuse.
    limit = await run_in_threadpool(_tuner_count)
    if relay_registry.count_active() >= limit:
        raise APIError(
            code="TUNER_BUSY",
            message=f"All {limit} tuner slots are in use",
            status_code=503,
            context={"limit": limit},
        )
    # The settings read is a blocking DB call: keep it off the event loop.
    try:
        engine = await run_in_threadpool(_engine)
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


# --- operator API (/api/v1/tuner, token-gated) -------------------------------
@router.get("/settings", response_model=TunerSettingsResponse, summary="Tuner settings")
def get_tuner_settings(db: Session = Depends(get_db)) -> TunerSettingsResponse:
    return TunerSettingsResponse(**asdict(TunerService(db).settings()))


@router.put("/settings", response_model=TunerSettingsResponse, summary="Change the tuner settings")
def update_tuner_settings(payload: TunerSettingsUpdate, db: Session = Depends(get_db)) -> TunerSettingsResponse:
    return TunerSettingsResponse(**asdict(TunerService(db).update_settings(**payload.model_dump(exclude_none=True))))


@router.get("/status", response_model=TunerStatusResponse, summary="Lineup, URLs and allowlist state")
def tuner_status(request: Request, db: Session = Depends(get_db)) -> TunerStatusResponse:
    """Everything the Integrations page needs to explain the tuner: the lineup
    it would serve, the URLs to paste into a media server, and whether the
    allowlist can actually tell this caller apart from any other."""
    service = TunerService(db)
    lineup = service.build_lineup()
    public = _public(request, db)
    gate = get_tuner_gate()
    peer = (getattr(request.state, "peer", None) or (None, 0))[0]
    client_ip = request.client.host if request.client else None
    forwarded = bool(getattr(request.state, "forwarded", False))
    source = gate.classify_source(peer, forwarded)
    warnings: List[str] = []
    if source in ("docker-gateway", "loopback") and not forwarded:
        # Every client arrives as the same address, so the allowlist is a no-op.
        warnings.append("TUNER_ALLOWLIST_INEFFECTIVE")
    if lineup.overflow:
        warnings.append("TUNER_LINEUP_CAPPED")
    return TunerStatusResponse(
        channel_count=len(lineup.entries), renumbered=[asdict(entry) for entry in lineup.renumbered], overflow=lineup.overflow,
        device_id=service.device_id(),
        urls=TunerUrls(tuner=f"{public}/tuner", lineup=f"{public}/tuner/lineup.json", guide=f"{public}/tuner/guide.xml",
                       playlist=f"{public}/tuner/playlist.m3u", epg=f"{public}/tuner/epg.xml",
                       stream_template=f"{public}/tuner/stream/{{content_id}}.ts"),
        ffmpeg_available=player_service.capabilities()["ffmpeg_available"],
        allowed_networks=gate.allowed_networks, client_ip=client_ip, peer=peer,
        client_allowed=gate.is_allowed(peer) and gate.is_allowed(client_ip), client_source=source, warnings=warnings,
        recent_denials=[asdict(denial) for denial in gate.recent_denials()],
    )


# Must stay the last route on hdhr_router: it matches every /tuner/* path.
@hdhr_router.api_route("/{path:path}", methods=["GET", "HEAD", "POST"], include_in_schema=False)
async def tuner_not_found(path: str):
    # Tuner clients must never receive the SPA's index.html for a typo'd path.
    raise HTTPException(status_code=404, detail="Unknown tuner path")

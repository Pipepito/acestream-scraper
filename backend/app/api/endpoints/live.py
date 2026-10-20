"""`/live/{stream_id}`: open a stream that cannot be handed to the player as is.

Two kinds go through here:

- A broadcaster's live channel (`mediaset://T5`): resolved when opened and
  answered with a redirect to the freshly signed link.
- An HLS stream whose playlist publishes headers (101TV, PTV...): its
  manifests are fetched with those headers and served whole, because ffmpeg
  reads them cut short from the CDN and drops the list. See hls_manifest.

Mounted on the app, not on the API router: a player following a playlist
link cannot send the API token. Gated on TUNER_ALLOWED_NETWORKS instead,
like the tuner routes.

The playback headers travel in the playlist entry (`url|Referer=...`);
Kodi keeps sending them after a redirect and to every segment.
"""
import asyncio
import time
from urllib.parse import quote, urljoin

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.models import AcestreamChannel
from app.services import hls_manifest, live_providers
from app.services.tuner_network import require_tuner_network
from app.utils.bounded_source import source_get

live_router = APIRouter(prefix="/live", dependencies=[Depends(require_tuner_network)], tags=["live"])

# Opening one channel is a burst: Kodi asks with HEAD for the type, then GETs
# twice. Each GET would resolve again -- three requests and about six seconds
# on Mediaset -- so a link is reused for a few seconds. Far below the ~5 minutes
# a Mediaset master stays valid for opening; a later reconnect resolves anew.
REUSE_SECONDS = 30
HLS_TYPE = "application/vnd.apple.mpegurl"
_recent: dict = {}
# Whole budget for answering one GET, resolution or manifest fetch included.
# Kodi waits on this request in its interface thread: a broadcaster that
# hangs (Mediaset down: three requests of up to 20 s each) left the remote
# dead for 20 s and a surprise dialog a minute later. Past the budget the
# player gets a 502 at once, which it handles cleanly (dialog in 2 s, remote
# responsive). Mediaset's slowest measured resolution was about 6 s.
# 15 s and not 8: with the playlist's mimetype the budget no longer blocks
# the remote (measured 0 s), it only delays the error, so a slow broadcaster
# gets more room.
OPEN_BUDGET_SECONDS = 15
# A manifest is a few hundred KB at most (cdnmedia's DVR chunklist: 290 KB).
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_REDIRECTS = 5


async def _resolve_once(stream_url: str):
    now = time.monotonic()
    for key in [k for k, (at, _) in _recent.items() if now - at > REUSE_SECONDS]:
        del _recent[key]
    if stream_url in _recent:
        return _recent[stream_url][1]
    link = await live_providers.resolve_async(stream_url, timeout=OPEN_BUDGET_SECONDS)
    if link:
        _recent[stream_url] = (now, link)
    return link


async def _fetch_manifest(url: str, headers: dict, limit: int = MAX_MANIFEST_BYTES):
    """(final URL, body, content type), following redirects through the
    guarded client: every hop's address is checked, these URLs come from
    third-party playlists."""
    deadline = time.monotonic() + OPEN_BUDGET_SECONDS
    for _ in range(MAX_REDIRECTS + 1):
        response = await source_get(url, timeout=deadline - time.monotonic(), headers=headers, max_bytes=limit, media_limit=512)
        if response.status_code in (301, 302, 303, 307, 308) and response.headers.get('Location'):
            url = urljoin(url, response.headers['Location'])
            continue
        response.raise_for_status()
        if len(response.content) > limit:
            raise ValueError('response too large')
        return url, response.content, response.headers.get('Content-Type') or ''
    raise ValueError('too many redirects')


async def _serve_manifest(stream_id: str, url: str, headers: dict, root_path: str = ""):
    try:
        final_url, body, content_type = await _fetch_manifest(url, headers)
    except Exception:
        return JSONResponse({"detail": "The origin did not return a valid manifest"}, status_code=502)
    text = body.decode('utf-8', 'replace')
    if '#EXTM3U' not in text[:512]:
        # Not a manifest -- an origin that answers with the video itself.
        # Hand it over instead of buffering video here.
        return RedirectResponse(final_url, status_code=302)

    def link(absolute_url: str) -> str:
        return (f"{root_path}/live/{quote(stream_id, safe='')}?u={quote(absolute_url, safe='')}"
                f"&s={hls_manifest.sign(absolute_url)}")

    try:
        served = hls_manifest.serve(text, final_url, link)
    except ValueError:
        return JSONResponse({"detail": "The origin returned an unsupported manifest"}, status_code=502)
    # A plain body, so a Content-Length and never chunked: served this way
    # ffmpeg reads it whole.
    return Response(content=served.encode('utf-8'), media_type=HLS_TYPE)


@live_router.api_route("/{stream_id}", methods=["GET", "HEAD"], include_in_schema=False)
async def open_live_stream(stream_id: str, request: Request, db: Session = Depends(get_db)):
    def load_stream():
        try:
            stream = db.get(AcestreamChannel, stream_id)
            return getattr(stream, "stream_url", None), dict(getattr(stream, "stream_headers", None) or {})
        finally:
            db.close()
    stream_url, stream_headers = await run_in_threadpool(load_stream)
    # Errors are answered as JSON here: a 404 raised as an exception would
    # reach the SPA fallback and come back as index.html with HTTP 200.
    if hls_manifest.needs_manifest(stream_url, stream_headers):
        if request.method == "HEAD":
            return Response(status_code=200, media_type=HLS_TYPE)
        # A variant or nested manifest: only a URL we signed when rewriting
        # its master, never one a caller makes up.
        nested = request.query_params.get("u")
        if nested is not None:
            if not hls_manifest.is_signed(nested, request.query_params.get("s", "")):
                return JSONResponse({"detail": "Unsigned manifest URL"}, status_code=403)
        try:
            return await asyncio.wait_for(
                _serve_manifest(stream_id, nested or stream_url, stream_headers, request.scope.get("root_path", "").rstrip("/")),
                OPEN_BUDGET_SECONDS)
        except asyncio.TimeoutError:
            return JSONResponse({"detail": "The origin did not answer in time"}, status_code=502)
    if live_providers.for_stream_url(stream_url) is None:
        return JSONResponse({"detail": "Not a live channel"}, status_code=404)
    if request.method == "HEAD":
        # Kodi gives the HEAD five seconds and then retries it; resolving
        # Mediaset here took longer, and zapping took about 25 s. The HEAD
        # only asks what the link is, and all of these are HLS: answer at
        # once and let the GET resolve.
        return Response(status_code=200, media_type=HLS_TYPE)
    # Resolving makes one to three requests to the broadcaster; never on the
    # event loop.
    try:
        # Cancellation propagates to the provider HTTP worker. Only completed
        # resolutions enter the short-lived cache.
        link = await asyncio.wait_for(_resolve_once(stream_url), OPEN_BUDGET_SECONDS)
    except asyncio.TimeoutError:
        link = None
    if not link:
        return JSONResponse({"detail": "The broadcaster did not return a live link"}, status_code=502)
    return RedirectResponse(link, status_code=302)

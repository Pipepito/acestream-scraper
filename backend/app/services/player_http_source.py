"""Session-owned, guarded HTTP input for FFmpeg.

Only opaque loopback URLs reach FFmpeg. Every manifest reference (including
keys, init data and alternative audio) returns through the DNS-pinned client.
No upstream redirects, credentials or playlists are passed through verbatim.
"""
from __future__ import annotations

import asyncio
import re
import secrets
from collections import OrderedDict, deque
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import aiohttp
from aiohttp import web
from fastapi.concurrency import run_in_threadpool

from app.services import hls_manifest, live_providers
from app.services.hls_selection import best_variant
from app.services.player_subtitles import media_clock_webvtt
from app.utils.outbound_http import source_session

MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_SUBTITLE_BYTES = 512 * 1024
MAX_RESOURCES = 4096
MAX_REDIRECTS = 5
READ_TIMEOUT = 20
_URI = re.compile(r'(?<![A-Z0-9-])URI="([^"\r\n]+)"')
# Ignore unknown extension tags, particularly variable substitution and content
# steering: they must not introduce URLs outside this rewriter's control.
_TAGS = frozenset(('EXTM3U EXTINF EXT-X-VERSION EXT-X-TARGETDURATION '
    'EXT-X-MEDIA-SEQUENCE EXT-X-DISCONTINUITY-SEQUENCE EXT-X-ENDLIST '
    'EXT-X-PLAYLIST-TYPE EXT-X-INDEPENDENT-SEGMENTS EXT-X-DISCONTINUITY '
    'EXT-X-PROGRAM-DATE-TIME EXT-X-BYTERANGE EXT-X-GAP EXT-X-KEY EXT-X-MAP '
    'EXT-X-STREAM-INF EXT-X-MEDIA EXT-X-I-FRAME-STREAM-INF EXT-X-SESSION-KEY').split())


@dataclass(frozen=True)
class HTTPStreamSource:
    url: str
    headers: dict[str, str]


class HTTPMediaStatusError(ValueError):
    def __init__(self, status: int):
        super().__init__(f'Upstream HTTP {status}')
        self.status = status


def stored_http_source(content_id: str) -> HTTPStreamSource | None:
    """Read only persisted sources; never accept arbitrary URLs in the API."""
    from app.config.database import SessionLocal
    from app.repositories.channel_repository import ChannelRepository

    with SessionLocal() as db:
        channel = ChannelRepository(db).get_channel_by_id(content_id)
        if channel is None or not channel.stream_url:
            from app.repositories.event_repository import EventRepository
            media = EventRepository(db).media(content_id)
            return HTTPStreamSource(media.url, dict(media.headers)) if media else None
        return HTTPStreamSource(channel.stream_url, dict(channel.stream_headers or {}))


def _http_url(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname
            or parsed.username or parsed.password or len(url) > 16384
            or any(ord(char) < 32 for char in url) or '{$' in url):
        raise ValueError('Unsupported media URL')
    return url


def _origin(url: str) -> tuple:
    parsed = urlsplit(url)
    return parsed.scheme, parsed.hostname, parsed.port or (443 if parsed.scheme == 'https' else 80)


class PlayerHTTPSource:
    def __init__(self, url: str, headers: dict[str, str]):
        self.url = _http_url(url)
        self.select_best_variant = False
        # Host, Range and hop-by-hop headers belong to the guarded transport.
        self.headers = {key: value for key, value in headers.items()
                        if key.lower() in ('user-agent', 'referer', 'origin', 'authorization', 'cookie')}
        self._resources: OrderedDict[str, str] = OrderedDict()
        self._ids: dict[str, str] = {}
        self._runner: web.AppRunner | None = None
        self._tasks: set[asyncio.Task] = set()
        # Only status/type and our own resource suffix; never source URLs,
        # response bodies, headers or exception messages.
        self.failures: deque[str] = deque(maxlen=8)
        self._base = ''
        self._secret = secrets.token_hex(24)

    @classmethod
    async def open(cls, content_id: str, *, timeout: float) -> PlayerHTTPSource:
        async with asyncio.timeout(max(0, timeout)):
            stored = await run_in_threadpool(stored_http_source, content_id)
            if stored is None:
                raise ValueError('Unknown HTTP stream')
            url = stored.url
            if live_providers.for_stream_url(url) is not None:
                url = await live_providers.resolve_async(url, timeout=timeout)
            if not url:
                raise ValueError('Broadcaster did not return a live link')
            source = cls(url, stored.headers)
            try:
                await source.start()
            except BaseException:
                await source.close()
                raise
            return source

    async def start(self) -> None:
        app = web.Application(client_max_size=1024)
        app.router.add_get('/{secret}/{resource}', self._handle)
        self._runner = web.AppRunner(app, access_log=None, shutdown_timeout=1)
        await self._runner.setup()
        site = web.TCPSite(self._runner, '127.0.0.1', 0)
        await site.start()
        port = self._runner.addresses[0][1]
        self._base = f'http://127.0.0.1:{port}/{self._secret}/'

    @property
    def playback_url(self) -> str:
        return self.link(self.url, '.m3u8')

    def link(self, url: str, suffix: str = '.ts') -> str:
        url = _http_url(url)
        if url in self._ids:
            ident = self._ids[url]
            self._resources.move_to_end(ident)
        else:
            extension = urlsplit(url).path.rsplit('.', 1)[-1].lower()
            if extension in ('m3u8', 'ts', 'm4s', 'mp4', 'aac', 'mp3', 'key', 'vtt', 'webvtt'):
                suffix = '.' + extension
            ident = secrets.token_hex(16) + suffix
            self._resources[ident] = url
            self._ids[url] = ident
            while len(self._resources) > MAX_RESOURCES:
                old, target = self._resources.popitem(last=False)
                del self._ids[target]
        return self._base + ident

    def rewrite(self, text: str, origin: str) -> str:
        if not text.startswith('#EXTM3U'):
            raise ValueError('Invalid HLS manifest')
        # DVR lists can carry hours of entries; preserve the existing bounded
        # live window and explicit byte ranges before rewriting all resources.
        if self.select_best_variant and hls_manifest.is_master(text):
            text = best_variant(text)
        if not hls_manifest.is_master(text):
            text = hls_manifest.prune(text, origin)
        out = []
        variant = False
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            if not line.startswith('#'):
                out.append(self.link(urljoin(origin, line), '.m3u8' if variant else '.ts'))
                variant = False
                continue
            tag = line[1:].split(':', 1)[0]
            if tag not in _TAGS:
                continue
            if '{$' in line:
                raise ValueError('HLS variables are unsupported')
            suffix = '.mp4' if tag == 'EXT-X-MAP' else '.m3u8' if tag in (
                'EXT-X-MEDIA', 'EXT-X-I-FRAME-STREAM-INF') else '.key'
            # Reject malformed/unquoted URI attributes rather than allowing
            # FFmpeg to interpret an address that we did not rewrite.
            scrubbed = _URI.sub('', line)
            if re.search(r'\bURI\s*=', scrubbed, re.IGNORECASE):
                raise ValueError('Invalid HLS URI attribute')
            line = _URI.sub(lambda match: 'URI="' + self.link(urljoin(origin, match[1]), suffix) + '"', line)
            out.append(line)
            variant = tag == 'EXT-X-STREAM-INF'
        return '\n'.join(out) + '\n'

    async def _handle(self, request: web.Request) -> web.StreamResponse:
        if not secrets.compare_digest(request.match_info['secret'], self._secret):
            raise web.HTTPNotFound()
        url = self._resources.get(request.match_info['resource'])
        if url is None:
            raise web.HTTPNotFound()
        if len(self._tasks) >= 8:
            self.failures.append('request capacity exceeded')
            raise web.HTTPServiceUnavailable()
        task = asyncio.current_task()
        self._tasks.add(task)
        try:
            return await self._fetch(request, url)
        except asyncio.CancelledError:
            raise
        except ConnectionResetError:
            # FFmpeg abandons prefetched/unused rendition segments normally.
            # The upstream context has closed; this is a client disconnect.
            return web.Response(status=499)
        except Exception as exc:
            # Upstream URLs may be signed. Never log or return exception text.
            self._record_failure(request, exc)
            return web.Response(status=502, text='HTTP media unavailable')
        finally:
            self._tasks.discard(task)

    def _record_failure(self, request: web.Request, exc: Exception) -> None:
        kind = request.match_info['resource'].rsplit('.', 1)[-1]
        reason = f'HTTP {exc.status}' if isinstance(exc, HTTPMediaStatusError) else type(exc).__name__
        self.failures.append(f'{kind}: {reason}')

    async def _fetch(self, request: web.Request, url: str) -> web.StreamResponse:
        headers = dict(self.headers, **{"Accept-Encoding": "identity"})
        if _origin(url) != _origin(self.url):
            headers = {k: v for k, v in headers.items() if k.lower() not in ('authorization', 'cookie')}
        byte_range = request.headers.get('Range')
        if byte_range:
            if not re.fullmatch(r'bytes=\d+-\d*', byte_range):
                raise ValueError('Unsupported range')
            headers['Range'] = byte_range
        timeout = aiohttp.ClientTimeout(total=None, connect=READ_TIMEOUT, sock_read=READ_TIMEOUT)
        async with asyncio.timeout(READ_TIMEOUT) as budget:
            # Identity is asked for, but some CDNs (Telemadrid's) still gzip the
            # media playlist: decode whatever arrives encoded, or FFmpeg gets the
            # compressed bytes without the header and rejects the playlist.
            async with source_session(timeout=timeout, auto_decompress=True, cookie_jar=aiohttp.DummyCookieJar()) as client:
                for _ in range(MAX_REDIRECTS + 1):
                    _http_url(url)
                    async with client.get(url, headers=headers, allow_redirects=False) as upstream:
                        if upstream.status in (301, 302, 303, 307, 308):
                            target = _http_url(urljoin(url, upstream.headers['Location']))
                            if _origin(target) != _origin(url):
                                headers = {k: v for k, v in headers.items() if k.lower() not in ('authorization', 'cookie')}
                            url = target
                            continue
                        if upstream.status not in (200, 206):
                            raise HTTPMediaStatusError(upstream.status)
                        # readexactly is necessary: a TCP chunk may be only one byte.
                        try:
                            prefix = await upstream.content.readexactly(512)
                        except asyncio.IncompleteReadError as exc:
                            prefix = exc.partial
                        if prefix.lstrip(b'\xef\xbb\xbf \r\n').startswith(b'#EXTM3U'):
                            body = bytearray(prefix)
                            async for chunk in upstream.content.iter_chunked(65536):
                                body.extend(chunk)
                                if len(body) > MAX_MANIFEST_BYTES:
                                    raise ValueError('HLS manifest too large')
                            text = bytes(body).decode('utf-8-sig').lstrip()
                            return web.Response(text=self.rewrite(text, url), content_type='application/vnd.apple.mpegurl')
                        if prefix.lstrip(b'\xef\xbb\xbf').startswith(b'WEBVTT'):
                            body = bytearray(prefix)
                            async for chunk in upstream.content.iter_chunked(65536):
                                body.extend(chunk)
                                if len(body) > MAX_SUBTITLE_BYTES:
                                    raise ValueError('Subtitle segment too large')
                            return web.Response(text=media_clock_webvtt(bytes(body).decode('utf-8-sig')),
                                                content_type='text/vtt')
                        budget.reschedule(None)
                        # Stream media with backpressure; never buffer a whole live
                        # transport stream or segment. Range metadata is preserved.
                        # Lengths and ranges of an encoded body do not describe the
                        # decoded bytes sent on.
                        encoded = upstream.headers.get('Content-Encoding', 'identity').lower() != 'identity'
                        response = web.StreamResponse(status=upstream.status, headers={
                            key: upstream.headers[key] for key in ('Content-Length', 'Content-Range', 'Accept-Ranges')
                            if key in upstream.headers and not encoded
                        })
                        response.content_type = 'application/octet-stream'
                        await response.prepare(request)
                        try:
                            await response.write(prefix)
                            while True:
                                try:
                                    chunk = await upstream.content.read(65536)
                                except Exception as exc:
                                    self._record_failure(request, exc)
                                    raise
                                if not chunk:
                                    break
                                await response.write(chunk)
                            await response.write_eof()
                        except Exception:
                            # Headers/media have already been sent. A second
                            # HTTP response would corrupt FFmpeg's media input.
                            # Downstream disconnects are not upstream failures.
                            response.force_close()
                            if request.transport is not None:
                                request.transport.close()
                        return response
            raise ValueError('Too many redirects')

    async def close(self) -> None:
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        runner, self._runner = self._runner, None
        if runner is not None:
            await runner.cleanup()
        self._resources.clear()
        self._ids.clear()

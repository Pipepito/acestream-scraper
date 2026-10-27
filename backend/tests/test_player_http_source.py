"""Guarded browser HTTP playback, including real FFmpeg HLS ingestion."""
import asyncio
import contextlib
import os
import shutil
import subprocess
from types import SimpleNamespace
from urllib.parse import urlsplit

import aiohttp
from aiohttp import web
import pytest

from app.services import player_http_source as http_source
from app.services.player_http_source import HTTPStreamSource, PlayerHTTPSource
from app.services.player_service import PlayerService

HTTP_ID = 'url:' + 'a' * 40


@contextlib.asynccontextmanager
async def origin(handler):
    app = web.Application()
    app.router.add_get('/{path:.*}', handler)
    runner = web.AppRunner(app, access_log=None, shutdown_timeout=1)
    await runner.setup()
    await web.TCPSite(runner, '127.0.0.1', 0).start()
    try:
        yield f'http://127.0.0.1:{runner.addresses[0][1]}'
    finally:
        await runner.cleanup()


def test_manifest_rewrites_all_resources_and_rejects_unsafe_schemes():
    source = PlayerHTTPSource('https://origin.example/master', {})
    source._base = 'http://127.0.0.1:1234/secret/'
    master = source.rewrite('#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="a",URI="audio.m3u8"\n'
                            '#EXT-X-STREAM-INF:BANDWIDTH=1000\nvideo.m3u8\n', source.url)
    assert 'origin.example' not in master and 'audio.m3u8' not in master
    assert set(source._resources.values()) == {'https://origin.example/audio.m3u8', 'https://origin.example/video.m3u8'}
    media = source.rewrite('#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="key"\n'
                           '#EXT-X-MAP:URI="init.mp4"\n#EXTINF:2,\nseg.ts\n#EXT-X-ENDLIST\n', source.url)
    assert media.count(source._base) == 3
    for uri in ('file:///etc/passwd', 'crypto+http://remote/segment', 'data:secret', '{$host}/seg.ts'):
        with pytest.raises(ValueError):
            source.rewrite(f'#EXTM3U\n#EXTINF:2,\n{uri}\n', source.url)
    with pytest.raises(ValueError):
        source.rewrite('#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI=http://remote/key\n#EXTINF:2,\nseg.ts\n', source.url)


def test_resource_inventory_is_bounded(monkeypatch):
    monkeypatch.setattr(http_source, 'MAX_RESOURCES', 3)
    source = PlayerHTTPSource('https://origin.example/live', {})
    for number in range(10):
        source.link(f'https://origin.example/{number}.ts')
    assert len(source._resources) == len(source._ids) == 3


def test_proxy_headers_redirects_ranges_and_metadata_blocking(monkeypatch):
    seen = []
    async def run():
        async def handler(request):
            seen.append((request.path, dict(request.headers)))
            if request.path == '/master':
                return web.Response(text='#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000\nvariant.m3u8\n')
            if request.path == '/variant.m3u8':
                return web.Response(text='#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2,\nseg.ts\n')
            if request.path == '/blocked':
                raise web.HTTPFound('http://169.254.169.254/latest/meta-data/')
            if request.path == '/redirect':
                raise web.HTTPFound(other + '/segment')
            return web.Response(body=b'0123456789', status=206,
                                headers={'Content-Range': 'bytes 10-19/100', 'Accept-Ranges': 'bytes'})
        async with origin(handler) as other, origin(handler) as base:
            source = PlayerHTTPSource(base + '/master', {'Referer': 'https://broadcaster.example/',
                'Authorization': 'Bearer private', 'Cookie': 'private=1', 'Host': 'evil.invalid'})
            await source.start()
            try:
                async with aiohttp.ClientSession() as client:
                    async with client.get(source.playback_url) as response:
                        assert response.status == 200
                        master = await response.text()
                    variant = master.splitlines()[-1]
                    async with client.get(variant) as response:
                        media = await response.text()
                    async with client.get(media.splitlines()[-1], headers={'Range': 'bytes=10-19'}) as response:
                        assert response.status == 206
                        assert response.headers['Content-Range'] == 'bytes 10-19/100'
                        assert await response.read() == b'0123456789'
                    assert seen[-1][1]['Range'] == 'bytes=10-19'
                    assert seen[-1][1]['Authorization'] == 'Bearer private'
                    assert seen[-1][1]['Referer'] == 'https://broadcaster.example/'
                    assert seen[-1][1]['Host'] != 'evil.invalid'
                    async with client.get(source.link(base + '/redirect')) as response:
                        assert response.status == 206
                        await response.read()
                    assert 'Authorization' not in seen[-1][1] and 'Cookie' not in seen[-1][1]
                    async with client.get(source.link(base + '/blocked')) as response:
                        assert response.status == 502
                        assert '169.254' not in await response.text()
                    async with client.get(source.playback_url.replace(source._secret, 'wrong')) as response:
                        assert response.status == 404
            finally:
                await source.close()
            assert not source._tasks and not source._resources
    asyncio.run(run())


def test_source_keeps_sec_fetch_mode():
    """7 TV La Rioja's CDN answers 403 to a manifest request without it."""
    source = PlayerHTTPSource('https://origin.example/live', {'Sec-Fetch-Mode': 'cors', 'Host': 'evil.invalid'})
    assert source.headers == {'Sec-Fetch-Mode': 'cors'}


def test_broadcaster_resolution_is_fresh_and_cancellable(monkeypatch):
    monkeypatch.setattr(http_source, 'stored_http_source', lambda _: HTTPStreamSource('atresplayer://lasexta', {}))
    calls = []
    async def resolve(url, *, timeout):
        calls.append(url)
        return 'https://origin.example/live.m3u8?token=' + str(len(calls))
    monkeypatch.setattr(http_source.live_providers, 'resolve_async', resolve)
    async def run():
        for _ in range(2):
            source = await PlayerHTTPSource.open(HTTP_ID, timeout=2)
            await source.close()
        assert len(calls) == 2
        entered = asyncio.Event()
        async def slow(*args, **kwargs):
            entered.set()
            await asyncio.Future()
        monkeypatch.setattr(http_source.live_providers, 'resolve_async', slow)
        task = asyncio.create_task(PlayerHTTPSource.open(HTTP_ID, timeout=2))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(run())


def test_oversized_manifest_and_slow_origin_are_bounded(monkeypatch):
    monkeypatch.setattr(http_source, 'MAX_MANIFEST_BYTES', 512)
    monkeypatch.setattr(http_source, 'READ_TIMEOUT', 0.1)
    async def run():
        async def handler(request):
            if request.path == '/slow':
                await asyncio.sleep(0.2)
            return web.Response(body=b'#EXTM3U\n' + b'x' * 600)
        async with origin(handler) as base:
            source = PlayerHTTPSource(base + '/large', {})
            await source.start()
            try:
                async with aiohttp.ClientSession() as client:
                    for path in ('large', 'slow'):
                        async with client.get(source.link(base + '/' + path)) as response:
                            assert response.status == 502
            finally:
                await source.close()
    asyncio.run(run())


def test_gzip_manifest_is_decoded_even_when_identity_was_asked():
    """Telemadrid's CDN answers its media playlist with Content-Encoding: gzip
    although the proxy asks for identity; passed through, FFmpeg got the
    compressed bytes without the header and rejected the playlist."""
    import gzip

    async def run():
        async def handler(request):
            assert request.headers['Accept-Encoding'] == 'identity'
            if request.path == '/segment.ts':
                return web.Response(body=gzip.compress(b'G' * 188), headers={'Content-Encoding': 'gzip'})
            body = gzip.compress(b'#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment.ts\n')
            return web.Response(body=body, headers={'Content-Encoding': 'gzip'},
                                content_type='application/octet-stream')
        async with origin(handler) as base:
            source = PlayerHTTPSource(base + '/live.m3u8', {})
            await source.start()
            try:
                async with aiohttp.ClientSession(auto_decompress=False) as client:
                    async with client.get(source.playback_url) as response:
                        assert response.status == 200
                        assert 'Content-Encoding' not in response.headers
                        text = await response.text()
                    assert text.startswith('#EXTM3U')
                    segment = [line for line in text.splitlines() if line and not line.startswith('#')][0]
                    assert urlsplit(segment).hostname == '127.0.0.1' and 'segment.ts' not in segment
                    async with client.get(segment) as response:
                        assert 'Content-Encoding' not in response.headers
                        assert await response.read() == b'G' * 188
            finally:
                await source.close()
    asyncio.run(run())


def test_proxy_records_bounded_status_details_without_signed_urls():
    async def run():
        async def handler(request):
            return web.Response(status=492, text='private upstream response')
        async with origin(handler) as base:
            source = PlayerHTTPSource(base + '/live.m3u8?signature=private', {})
            await source.start()
            try:
                async with aiohttp.ClientSession() as client:
                    for _ in range(10):
                        async with client.get(source.playback_url) as response:
                            assert response.status == 502
                            assert await response.text() == 'HTTP media unavailable'
                assert list(source.failures) == ['m3u8: HTTP 492'] * 8
            finally:
                await source.close()
    asyncio.run(run())


def test_interrupted_media_closes_connection_without_injecting_http_error():
    async def run():
        disconnect = asyncio.Event()
        async def handler(request):
            response = web.StreamResponse(headers={'Content-Length': '4096'})
            await response.prepare(request)
            await response.write(b'x' * 600)
            await disconnect.wait()
            request.transport.close()
            return response
        async with origin(handler) as base:
            source = PlayerHTTPSource(base + '/segment.ts', {})
            await source.start()
            writer = None
            try:
                target = urlsplit(source.playback_url)
                reader, writer = await asyncio.open_connection(target.hostname, target.port)
                writer.write(f'GET {target.path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'.encode())
                await writer.drain()
                async with asyncio.timeout(3):
                    headers = await reader.readuntil(b'\r\n\r\n')
                    assert b'200 OK' in headers and b'Content-Length: 4096' in headers
                    assert await reader.readexactly(600) == b'x' * 600
                    disconnect.set()
                    # After headers are committed only media may follow, even
                    # when the upstream truncates its advertised body.
                    assert await reader.read() == b''
                assert list(source.failures) == ['ts: ClientPayloadError']
            finally:
                disconnect.set()
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                await source.close()
    asyncio.run(run())


@pytest.mark.parametrize("media_format", ["hls", "encrypted", "fmp4", "mpegts", "subtitles"])
def test_real_ffmpeg_reads_guarded_hls_without_engine(tmp_path, monkeypatch, media_format):
    ffmpeg = shutil.which('ffmpeg')
    fixture_tool = os.environ.get('FFMPEG_TEST_TOOL_PATH') or ffmpeg
    if not ffmpeg or not fixture_tool:
        pytest.skip('FFmpeg required for media integration')
    media_dir = tmp_path / 'origin'
    media_dir.mkdir()
    target = media_dir / ('stream.ts' if media_format == 'mpegts' else 'index.m3u8')
    options = ['-f', 'mpegts'] if media_format == 'mpegts' else ['-f', 'hls', '-hls_time', '2', '-hls_list_size', '0']
    if media_format == 'encrypted':
        key = media_dir / 'key'
        key.write_bytes(b'0123456789abcdef')
        key_info = tmp_path / 'key-info'
        key_info.write_text('key\n' + str(key) + '\n')
        options += ['-hls_key_info_file', str(key_info)]
    if media_format == 'fmp4':
        options += ['-hls_segment_type', 'fmp4']
    subprocess.run([fixture_tool, '-nostdin', '-hide_banner', '-loglevel', 'error',
                    '-f', 'lavfi', '-i', 'testsrc=size=160x90:rate=25',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000',
                    '-t', '12', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-g', '50',
                    '-c:a', 'aac', *options, str(target)], check=True, capture_output=True, timeout=30)
    if media_format == 'subtitles':
        # Broadcaster masters advertise separate WebVTT renditions. Exercise
        # their discovery, guarded fetching and conversion with real media.
        (media_dir / 'subtitles.m3u8').write_text('#EXTM3U\n#EXT-X-TARGETDURATION:12\n'
            '#EXTINF:12,\nsubtitles.webvtt\n#EXT-X-ENDLIST\n')
        (media_dir / 'subtitles.webvtt').write_text('WEBVTT\nX-TIMESTAMP-MAP=MPEGTS:270000,LOCAL:00:00:00.000\n\n00:00:00.000 --> 00:00:05.000\nCaption\n')
        target = media_dir / 'master.m3u8'
        target.write_text('#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="Spanish",'
            'LANGUAGE="es",URI="subtitles.m3u8"\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=1000000,SUBTITLES="subs"\nindex.m3u8\n')
    settings = SimpleNamespace(PLAYER_HLS_DIR=str(tmp_path / 'output'), PLAYER_MAX_SESSIONS=2,
                               PLAYER_START_TIMEOUT_SECONDS=15, FFMPEG_BINARY_PATH='')
    def no_engine():
        raise AssertionError('HTTP playback must not contact the engine')
    svc = PlayerService(settings_getter=lambda: settings, engine_factory=no_engine, ffmpeg_path=ffmpeg)
    async def run():
        async def handler(request):
            assert request.headers.get('Referer') == 'https://broadcaster.example/'
            path = media_dir / request.match_info['path']
            if path.suffix == '.ts':
                await asyncio.sleep(0.1)  # Leave time to observe readiness before VOD EOF.
            return web.FileResponse(path)
        async with origin(handler) as base:
            monkeypatch.setattr(http_source, 'stored_http_source', lambda _: HTTPStreamSource(
                base + '/' + target.name, {'Referer': 'https://broadcaster.example/'}))
            try:
                session = await svc.open_session(HTTP_ID, subtitle_index=0 if media_format == 'subtitles' else None)
                shared = await svc.open_session(HTTP_ID, subtitle_index=0 if media_format == 'subtitles' else None)
                assert session is shared and session.viewers == 2
                for _ in range(150):
                    if svc.hls_ready(session):
                        break
                    await asyncio.sleep(0.05)
                assert svc.hls_ready(session), (session.error, session.error_message)
                assert session.engine_session is None and session.stats is None
                assert session.codecs['video'] == 'h264'
                assert 'token=' not in session.error_message
                if media_format == 'subtitles':
                    assert session.subtitle_tracks and session.subtitle_tracks[0].codec == 'webvtt'
                    assert (session.dir / 'index_vtt.m3u8').exists()
                    for _ in range(60):
                        if any('Caption' in path.read_text() for path in session.dir.glob('index*.vtt')):
                            break
                        await asyncio.sleep(0.05)
                    assert any('Caption' in path.read_text() for path in session.dir.glob('index*.vtt')), {path.name: path.read_text() for path in session.dir.glob('index*.vtt')}
                source = session.http_source
            finally:
                await svc.stop()
            assert not svc.sessions
            if source is not None:
                assert source._runner is None and not source._tasks
    asyncio.run(run())


def test_closing_source_cancels_an_active_media_download():
    async def run():
        disconnected = asyncio.Event()
        async def handler(request):
            response = web.StreamResponse()
            await response.prepare(request)
            try:
                while True:
                    await response.write(b'\x47' + b'x' * 65535)
                    await asyncio.sleep(0.01)
            except (ConnectionResetError, asyncio.CancelledError):
                disconnected.set()
            return response
        async with origin(handler) as base:
            source = PlayerHTTPSource(base + '/stream.ts', {})
            await source.start()
            try:
                async with aiohttp.ClientSession() as client:
                    async with client.get(source.playback_url) as response:
                        assert await response.content.read(512)
                        assert source._tasks
                        await source.close()
                        await asyncio.wait_for(disconnected.wait(), 2)
                        assert not source._tasks and source._runner is None
            finally:
                await source.close()
    asyncio.run(run())


@pytest.mark.parametrize('attributes', [
    'SUBTITLES="subs",BANDWIDTH=1000,AUDIO="audio"',
    'BANDWIDTH=1000,SUBTITLES="subs",AUDIO="audio"',
    'BANDWIDTH=1000,AUDIO="audio",SUBTITLES="subs"',
])
def test_master_preserves_guarded_subtitles_and_audio(attributes):
    source = PlayerHTTPSource('https://origin.example/master.m3u8', {})
    text = source.rewrite('#EXTM3U\n'
        '#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",URI="captions.m3u8"\n'
        '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",URI="audio.m3u8"\n'
        f'#EXT-X-STREAM-INF:{attributes}\nvideo.m3u8\n', source.url)
    assert '#EXT-X-STREAM-INF:' + attributes in text
    assert set(source._resources.values()) == {'https://origin.example/captions.m3u8', 'https://origin.example/audio.m3u8', 'https://origin.example/video.m3u8'}


def test_oversized_subtitle_segment_is_bounded(monkeypatch):
    monkeypatch.setattr(http_source, 'MAX_SUBTITLE_BYTES', 1024)
    async def run():
        async def handler(request):
            return web.Response(body=b'WEBVTT\n\n' + b'x' * 2048)
        async with origin(handler) as base:
            source = PlayerHTTPSource(base + '/captions.webvtt', {})
            await source.start()
            try:
                async with aiohttp.ClientSession() as client:
                    async with client.get(source.playback_url) as response:
                        assert response.status == 502
            finally:
                await source.close()
    asyncio.run(run())

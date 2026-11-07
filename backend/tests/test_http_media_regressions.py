"""Actual bounded transports, cancellation and signal identification for HTTP inputs."""
import asyncio
from pathlib import Path
import time

from aiohttp import web
import pytest
import pytest_asyncio

from app.services import hls_manifest, http_stream_check
from app.utils.bounded_source import source_get

MEDIA = (Path(__file__).parent / 'docker/fixtures/sample-h264-ac3.m2ts').read_bytes()


@pytest_asyncio.fixture
async def origin():
    state = {'disconnected': asyncio.Event(), 'bytes_sent': 0}
    async def stream(request):
        if request.path == '/html':
            return web.Response(text='<html>Access denied</html>')
        if request.path == '/media':
            return web.Response(body=MEDIA)
        if request.path == '/redirect':
            raise web.HTTPFound('/html')
        if request.path == '/metadata':
            raise web.HTTPFound('http://169.254.169.254/latest/')
        response = web.StreamResponse(); await response.prepare(request)
        try:
            while True:
                await response.write(b'x' * 8192)
                state['bytes_sent'] += 8192
                await asyncio.sleep(0.01)
        except (ConnectionError, asyncio.CancelledError):
            state['disconnected'].set()
        return response
    app = web.Application(); app.router.add_get('/{path}', stream)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0); await site.start()
    try:
        yield f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}', state
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_range_ignored_still_stops_at_sample_cap(origin):
    url, state = origin
    result = await source_get(url + '/endless', headers={'Range': 'bytes=0-1023'}, max_bytes=1024, sample=True)
    assert len(result.content) == 1024 and result.truncated
    await asyncio.wait_for(state['disconnected'].wait(), 2)
    assert state['bytes_sent'] < 1024 * 1024


@pytest.mark.asyncio
async def test_document_limit_is_enforced_during_transfer(origin):
    url, state = origin
    with pytest.raises(ValueError, match='byte limit'):
        await source_get(url + '/endless', max_bytes=1024)
    await asyncio.wait_for(state['disconnected'].wait(), 2)


@pytest.mark.asyncio
async def test_trickle_cannot_extend_total_read_deadline(origin):
    url, state = origin; started = time.monotonic()
    with pytest.raises(TimeoutError):
        await source_get(url + '/endless', max_bytes=20 * 1024 * 1024, timeout=0.08)
    assert time.monotonic() - started < 1
    await asyncio.wait_for(state['disconnected'].wait(), 2)


@pytest.mark.asyncio
async def test_cancellation_closes_read(origin):
    url, state = origin
    task = asyncio.create_task(source_get(url + '/endless', max_bytes=20 * 1024 * 1024))
    while not state['bytes_sent']:
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    await asyncio.wait_for(state['disconnected'].wait(), 2)


@pytest.mark.asyncio
async def test_html_is_offline_but_real_av_packets_are_online(origin):
    url, _ = origin
    assert await http_stream_check.check(url + '/html') == (False, 'No audio or video packets verified')
    assert await http_stream_check.check(url + '/media') == (True, None)
    assert await http_stream_check.check(url + '/redirect') == (False, 'No audio or video packets verified')


@pytest.mark.asyncio
async def test_redirect_cannot_reach_metadata(origin):
    url, _ = origin
    online, error = await http_stream_check.check(url + '/metadata')
    assert online is None and 'BlockedURLError' in error
    assert '169.254' not in error


def test_window_preserves_relative_keys_maps_ranges_and_discontinuity():
    text = ('#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:20\n#EXT-X-DISCONTINUITY-SEQUENCE:3\n'
            '#EXT-X-KEY:METHOD=AES-128,URI="keys/k.bin"\n'
            '#EXT-X-DISCONTINUITY\n#EXTINF:4,\n#EXT-X-BYTERANGE:188@100\nall.ts\n'
            '#EXTINF:4,\n#EXT-X-BYTERANGE:188\nall.ts\n')
    output = hls_manifest.prune(text, 'https://cdn.example/dir/list.m3u8', window=1)
    assert 'URI="https://cdn.example/dir/keys/k.bin"' in output
    assert '#EXT-X-BYTERANGE:188@288' in output
    assert '#EXT-X-MEDIA-SEQUENCE:21' in output
    assert '#EXT-X-DISCONTINUITY-SEQUENCE:4' in output


def test_invalid_implicit_range_does_not_silently_change_media():
    with pytest.raises(ValueError, match='byte range'):
        hls_manifest.prune('#EXTM3U\n#EXTINF:4,\n#EXT-X-BYTERANGE:188\na.ts\n', 'https://cdn/list.m3u8')


@pytest.mark.asyncio
@pytest.mark.parametrize('cancel_request', [False, True])
async def test_provider_worker_stops_on_deadline_or_cancellation(origin, monkeypatch, cancel_request):
    from threading import Event
    from app.services import live_providers
    from app.services.live_providers import base
    url, state = origin
    stopped = Event()
    def resolve(_url):
        try:
            return base.http.get_text(url + '/endless')
        finally:
            stopped.set()
    monkeypatch.setattr(live_providers, 'resolve', resolve)
    task = asyncio.create_task(live_providers.resolve_async('mediaset://fixture', timeout=0.15 if not cancel_request else 5))
    while not state['bytes_sent']:
        await asyncio.sleep(0.01)
    if cancel_request:
        task.cancel()
    with pytest.raises(asyncio.CancelledError if cancel_request else TimeoutError):
        await task
    await asyncio.wait_for(state['disconnected'].wait(), 1)
    deadline = time.monotonic() + 1
    while not stopped.is_set() and time.monotonic() < deadline:
        await asyncio.sleep(0.01)
    assert stopped.is_set(), 'provider worker must not outlive the cancelled transfer'


@pytest.mark.asyncio
async def test_html_segment_is_not_online(origin, monkeypatch):
    from app.utils.bounded_source import SourceResponse
    url, _ = origin
    original = http_stream_check.source_get
    async def get(target, **kwargs):
        if target.endswith('/list.m3u8'):
            return SourceResponse(200, b'#EXTM3U\n#EXTINF:4,\nhtml\n', {})
        return await original(target, **kwargs)
    monkeypatch.setattr(http_stream_check, 'source_get', get)
    assert await http_stream_check.check(url + '/list.m3u8') == (False, 'No audio or video packets verified')


def test_encrypted_init_order_is_preserved_without_trimming():
    text = ('#EXTM3U\n#EXT-X-KEY:METHOD=AES-128,URI="keys/key.bin",IV=0x1\n'
            '#EXT-X-MAP:URI="init.mp4"\n#EXTINF:4,\na.m4s\n#EXTINF:4,\nb.m4s\n')
    output = hls_manifest.prune(text, 'https://cdn.example/dir/list.m3u8', window=1)
    assert 'URI="https://cdn.example/dir/init.mp4"' in output
    assert output.index('#EXT-X-KEY') < output.index('#EXT-X-MAP') < output.index('#EXTINF')
    assert 'https://cdn.example/dir/a.m4s' in output and 'https://cdn.example/dir/b.m4s' in output


@pytest.mark.asyncio
async def test_fragmented_mp4_init_and_segment_verify_media(tmp_path, monkeypatch):
    import os, shutil, subprocess
    from app.utils.bounded_source import SourceResponse
    ffmpeg = os.environ.get('FFMPEG_TEST_TOOL_PATH') or shutil.which('ffmpeg')
    assert ffmpeg, 'The full validation environment must provide FFmpeg'
    subprocess.run([ffmpeg, '-v', 'error', '-i', str(Path(__file__).parent / 'docker/fixtures/sample-h264-ac3.m2ts'),
                    '-map', '0:v:0', '-c', 'copy', '-t', '4', '-f', 'hls', '-hls_segment_type', 'fmp4',
                    '-hls_time', '2', '-hls_list_size', '0', str(tmp_path / 'list.m3u8')], check=True, timeout=20)
    table = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    asked = []
    async def get(url, **kwargs):
        name = url.rsplit('/', 1)[-1]; asked.append(name)
        return SourceResponse(200, table[name], {})
    monkeypatch.setattr(http_stream_check, 'source_get', get)
    assert await http_stream_check.check('https://cdn.example/list.m3u8') == (True, None)
    assert 'init.mp4' in asked


@pytest.mark.asyncio
async def test_manifest_endpoint_can_handoff_endless_direct_media_after_a_prefix(origin):
    from app.api.endpoints.live import _serve_manifest
    url, state = origin
    response = await _serve_manifest('url:fixture', url + '/endless', {'Referer': 'https://example.com/'})
    assert response.status_code == 302 and response.headers['location'] == url + '/endless'
    await asyncio.wait_for(state['disconnected'].wait(), 2)
    assert state['bytes_sent'] < 1024 * 1024


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['encrypted', 'fragmented', 'byte_ranges'])
async def test_rewritten_manifest_plays_real_media(tmp_path, kind):
    """Let FFmpeg consume the rewritten manifest, keys, maps and byte ranges."""
    import os
    import shutil
    import subprocess
    ffmpeg = os.environ.get('FFMPEG_TEST_TOOL_PATH') or shutil.which('ffmpeg')
    assert ffmpeg, 'The full validation environment must provide FFmpeg'
    options = []
    if kind == 'encrypted':
        key = tmp_path / 'fixture.key'
        key.write_bytes(bytes(range(16)))
        info = tmp_path / 'key-info'
        info.write_text('fixture.key\n' + str(key) + '\n')
        options = ['-hls_key_info_file', str(info)]
    elif kind == 'fragmented':
        options = ['-hls_segment_type', 'fmp4']
    else:
        options = ['-hls_flags', 'single_file']
    subprocess.run([ffmpeg, '-v', 'error', '-stream_loop', '-1', '-i', str(Path(__file__).parent / 'docker/fixtures/sample-h264-ac3.m2ts'),
                    '-map', '0:v:0', '-c', 'copy', '-t', '6', '-f', 'hls', '-hls_time', '1',
                    '-hls_list_size', '0', *options, str(tmp_path / 'list.m3u8')], check=True, timeout=20)
    # Exercise live-window pruning as well as relative URI resolution.
    manifest = (tmp_path / 'list.m3u8').read_text().replace('#EXT-X-ENDLIST\n', '')
    origin = ''
    asked = []
    async def serve(request):
        name = request.match_info['name']
        asked.append(name)
        if name == 'served.m3u8':
            # Seal the finite fixture after live-window rewriting so demuxer
            # probing can reach EOF instead of waiting for nonexistent new segments.
            rewritten = hls_manifest.serve(manifest, origin + '/list.m3u8', lambda url: url, window=2)
            return web.Response(text=rewritten + '#EXT-X-ENDLIST\n',
                                content_type='application/vnd.apple.mpegurl')
        return web.FileResponse(tmp_path / name)
    application = web.Application()
    application.router.add_get('/{name}', serve)
    runner = web.AppRunner(application)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    origin = f'http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}'
    process = None
    try:
        process = await asyncio.create_subprocess_exec(ffmpeg, '-v', 'error', '-nostdin',
            '-allowed_extensions', 'ALL', '-i', origin + '/served.m3u8',
            '-map', '0:v:0', '-t', '0.5', '-c', 'copy', '-f', 'null', '-',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(process.communicate(), 15)
        assert process.returncode == 0, stderr.decode()
        assert 'served.m3u8' in asked
        if kind == 'encrypted':
            assert 'fixture.key' in asked
        elif kind == 'fragmented':
            assert 'init.mp4' in asked
        else:
            assert 'list.ts' in asked
    finally:
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        await runner.cleanup()

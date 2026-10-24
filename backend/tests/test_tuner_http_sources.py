"""HTTP-only tuner channels, mixed startup fallback and real MPEG-TS output."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import os
import subprocess
from unittest.mock import Mock

from aiohttp import web
import pytest

from app.models.models import AcestreamChannel, TVChannel
from app.services import player_http_source, tuner_http_source, tuner_playback_service
from app.services.engine_client import EngineUnavailableError
from app.services.player_http_source import HTTPStreamSource
from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.tuner_service import TunerService

HTTP_ID = 'url:' + 'a' * 40
ACE_ID = 'b' * 40


def test_http_sources_share_freshness_ranking_and_survive_removing_engine_source(db_session):
    tv = TVChannel(name='laSexta', is_active=True)
    db_session.add(tv)
    db_session.flush()
    http = AcestreamChannel(id=HTTP_ID, name='laSexta', tv_channel_id=tv.id,
        stream_url='atresplayer://lasexta', is_active=True, is_online=None)
    ace = AcestreamChannel(id=ACE_ID, name='AceStream', tv_channel_id=tv.id,
        is_active=True, is_online=True, last_checked=datetime.now(timezone.utc))
    db_session.add_all([http, ace])
    db_session.commit()
    service = TunerService(db_session)
    assert service.relay_stream_ids(tv.id) == [ACE_ID, HTTP_ID]
    ace.tv_channel_id = None
    db_session.commit()
    assert service.relay_stream_ids(tv.id) == [HTTP_ID]
    assert http.is_online is None  # Eligibility never fabricates verified status.
    assert service.build_lineup().entries[0].tv_channel_id == tv.id
    http.is_online = False
    http.last_checked = datetime.now(timezone.utc)
    db_session.commit()
    assert service.relay_stream_ids(tv.id) == []
    assert service.stream_ids(tv.id) == [HTTP_ID]  # Still eligible for rechecking.
    http.last_checked -= timedelta(hours=7)
    db_session.commit()
    assert service.relay_stream_ids(tv.id) == [HTTP_ID]
    http.is_active = False
    db_session.commit()
    assert service.stream_ids(tv.id) == []
    assert service.build_lineup().entries == []


def test_http_only_tuner_get_works_without_engine_and_head_has_no_side_effects(alembic_client, alembic_db_session, monkeypatch):
    from app.api.endpoints import tuner
    from app.config.settings import get_settings
    from app.services.tuner_network import get_tuner_gate
    monkeypatch.setenv('TUNER_ALLOWED_NETWORKS', '*')
    get_settings.cache_clear()
    get_tuner_gate.cache_clear()
    tv = TVChannel(name='laSexta', is_active=True)
    alembic_db_session.add(tv)
    alembic_db_session.flush()
    alembic_db_session.add(AcestreamChannel(id=HTTP_ID, name='laSexta', tv_channel_id=tv.id,
        stream_url='atresplayer://lasexta', is_active=True, is_online=None))
    alembic_db_session.commit()
    refresh = Mock(return_value=None)
    engine = Mock(side_effect=EngineUnavailableError('No configured engine'))
    monkeypatch.setattr(tuner, '_engine', engine)
    monkeypatch.setattr(tuner.tuner_probe_service, 'start', refresh)
    opened = []
    async def http(cid, claim, **kwargs):
        opened.append(cid)
        yield b'transport stream'
    monkeypatch.setattr(tuner_playback_service, 'relay_http_stream', http)
    monkeypatch.setattr(tuner_playback_service, 'relay_engine_stream', Mock(side_effect=AssertionError('Engine used')))
    try:
        url = f'/tuner/channel/{tv.id}.ts?transcode=none'
        assert alembic_client.head(url).status_code == 200
        engine.assert_not_called()
        refresh.assert_not_called()
        assert opened == []
        response = alembic_client.get(url)
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('video/mp2t')
        assert response.content == b'transport stream'
        assert opened == [HTTP_ID]
        assert tuner.relay_registry.count_active() == 0
    finally:
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize('http_first', [True, False])
async def test_mixed_sources_fail_over_before_first_byte_with_one_slot(monkeypatch, http_first):
    registry = RelayRegistry()
    ids = [HTTP_ID, ACE_ID] if http_first else [ACE_ID, HTTP_ID]
    claim = registry.try_open(ids[0], 'Plex', 1)
    attempts, closed = [], []
    async def source(cid):
        attempts.append(cid)
        assert registry.try_open('other', 'other', 1) is None
        try:
            if cid == ids[0]:
                raise EngineStreamError('failed start')
            yield b'media'
        finally:
            closed.append(cid)
    def http(cid, *args, **kwargs):
        return source(cid)
    def engine(_engine, cid, *args, **kwargs):
        return source(cid)
    monkeypatch.setattr(tuner_playback_service, '_failures', __import__('collections').OrderedDict())
    monkeypatch.setattr(tuner_playback_service, 'relay_http_stream', http)
    monkeypatch.setattr(tuner_playback_service, 'relay_engine_stream', engine)
    chunks = [chunk async for chunk in tuner_playback_service.relay_ranked_streams(
        Mock(), ids, 'Plex', claim, registry=registry)]
    assert chunks == [b'media']
    assert attempts == closed == ids
    assert registry.count_active() == 0


@pytest.mark.asyncio
async def test_disconnect_drains_a_full_ffmpeg_output_pipe(monkeypatch):
    import sys
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    source = SimpleNamespace(playback_url='http://127.0.0.1/opaque', close=AsyncMock())
    monkeypatch.setattr(tuner_http_source.PlayerHTTPSource, 'open', AsyncMock(return_value=source))
    monkeypatch.setattr(tuner_http_source, 'ffmpeg_binary', lambda: sys.executable)
    monkeypatch.setattr(tuner_http_source, 'http_tuner_argv', lambda *args, **kwargs: [sys.executable, '-c',
        'import os; payload=b"x"*65536\nwhile True: os.write(1,payload)'])
    registry = RelayRegistry()
    claim = registry.try_open(HTTP_ID, 'Plex', 1)
    iterator = tuner_playback_service.relay_ranked_streams(None, [HTTP_ID], 'Plex', claim, registry=registry)
    assert await anext(iterator)
    await asyncio.sleep(.1)  # Let stdout backpressure fill the reader buffer.
    await asyncio.wait_for(iterator.aclose(), 3)
    source.close.assert_awaited_once()
    assert registry.count_active() == 0


@asynccontextmanager
async def origin(handler):
    app = web.Application()
    app.router.add_get('/{path:.*}', handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    try:
        yield f'http://127.0.0.1:{runner.addresses[0][1]}'
    finally:
        await runner.cleanup()


@pytest.fixture
def media_tools():
    try:
        ffmpeg = tuner_http_source.ffmpeg_binary()
    except EngineStreamError:
        pytest.skip('FFmpeg required for transport integration')
    return ffmpeg, os.environ.get('FFMPEG_TEST_TOOL_PATH', ffmpeg)


@pytest.mark.asyncio
@pytest.mark.parametrize('compatible', [False, True])
@pytest.mark.parametrize('kind', ['mpegts', 'hls', 'fmp4', 'encrypted', 'subtitles', 'master'])
async def test_real_http_media_is_remuxed_with_headers_and_no_engine(media_tools, tmp_path, monkeypatch, kind, compatible):
    ffmpeg, fixture_tool = media_tools
    target = tmp_path / ('stream.ts' if kind == 'mpegts' else 'index.m3u8')
    options = ['-f', 'mpegts'] if kind == 'mpegts' else ['-f', 'hls', '-hls_time', '1', '-hls_list_size', '0']
    if kind == 'fmp4':
        options += ['-hls_segment_type', 'fmp4']
    if kind == 'encrypted':
        key = tmp_path / 'key'
        key.write_bytes(b'0123456789abcdef')
        info = tmp_path / 'key-info'
        info.write_text('key\n' + str(key) + '\n')
        options += ['-hls_key_info_file', str(info)]
    subprocess.run([fixture_tool, '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=160x90:rate=25',
        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '4',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-g', '25', '-c:a', 'aac',
        *options, str(target)], check=True, capture_output=True, timeout=20)
    if kind == 'subtitles':
        (tmp_path / 'subtitles.m3u8').write_text('#EXTM3U\n#EXT-X-TARGETDURATION:4\n'
            '#EXTINF:4,\nsubtitles.webvtt\n#EXT-X-ENDLIST\n')
        (tmp_path / 'subtitles.webvtt').write_text('WEBVTT\n\n00:00:00.000 --> 00:00:03.000\nCaption\n')
        target = tmp_path / 'master.m3u8'
        target.write_text('#EXTM3U\n#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="Spanish",'
            'LANGUAGE="es",URI="subtitles.m3u8"\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=1000000,SUBTITLES="subs"\nindex.m3u8\n')
    if kind == 'master':
        subprocess.run([fixture_tool, '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:size=1920x1080:rate=25',
            '-f', 'lavfi', '-i', 'sine=frequency=880:sample_rate=48000', '-t', '4',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-g', '25', '-c:a', 'aac',
            '-f', 'hls', '-hls_time', '1', '-hls_list_size', '0', str(tmp_path / 'high.m3u8')],
            check=True, capture_output=True, timeout=20)
        target = tmp_path / 'master.m3u8'
        target.write_text('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=160x90\nindex.m3u8\n'
            '#EXT-X-STREAM-INF:BANDWIDTH=4000000,RESOLUTION=1920x1080\nhigh.m3u8\n')
    fetched = []
    async def handler(request):
        assert request.headers.get('Referer') == 'https://broadcaster.example/'
        fetched.append(request.path)
        return web.FileResponse(tmp_path / request.match_info['path'])
    children, proxies = [], []
    spawn = asyncio.create_subprocess_exec
    async def tracked_spawn(*args, **kwargs):
        child = await spawn(*args, **kwargs)
        children.append(child)
        return child
    start = player_http_source.PlayerHTTPSource.start
    async def tracked_start(proxy):
        proxies.append(proxy)
        await start(proxy)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', tracked_spawn)
    monkeypatch.setattr(player_http_source.PlayerHTTPSource, 'start', tracked_start)
    async with origin(handler) as base:
        monkeypatch.setattr(player_http_source, 'stored_http_source', lambda _: HTTPStreamSource(
            base + '/' + target.name, {'Referer': 'https://broadcaster.example/'}))
        registry = RelayRegistry()
        claim = registry.try_open(HTTP_ID, 'Plex', 1)
        async with asyncio.timeout(15):
            output = b''.join([chunk async for chunk in tuner_playback_service.relay_ranked_streams(
                None, [HTTP_ID], 'Plex', claim, registry=registry, plex_compatible_audio=compatible)])
    assert len(output) > 188 and len(output) % 188 == 0
    assert all(output[i] == 0x47 for i in range(0, len(output), 188))
    assert claim.bytes_sent == len(output)
    assert registry.count_active() == 0
    assert all(child.returncode is not None for child in children)
    assert all(proxy._runner is None and not proxy._tasks for proxy in proxies)
    if kind == 'encrypted':
        assert '/key' in fetched
    if kind == 'master':
        assert '/high.m3u8' in fetched and '/index.m3u8' not in fetched
        probe = subprocess.run([fixture_tool, '-hide_banner', '-i', 'pipe:0', '-f', 'null', '-'],
            input=output, capture_output=True, timeout=10)
        assert probe.returncode == 0
        assert '1920x1080' in probe.stderr.decode()
    if compatible:
        probe = subprocess.run([fixture_tool, '-hide_banner', '-i', 'pipe:0', '-f', 'null', '-'],
            input=output, capture_output=True, timeout=10)
        assert probe.returncode == 0
        assert 'aac_latm' in probe.stderr.decode()
    # Decode the actual tuner output, not just its transport sync bytes.
    result = subprocess.run([fixture_tool, '-v', 'error', '-i', 'pipe:0', '-map', '0:v:0',
        '-map', '0:a:0', '-f', 'null', '-'], input=output, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr.decode()


@pytest.mark.asyncio
@pytest.mark.parametrize('ending', ['timeout', 'disconnect'])
async def test_http_start_interruption_reaps_process_and_proxy(media_tools, monkeypatch, ending):
    entered = asyncio.Event()
    children, proxies = [], []
    async def handler(request):
        entered.set()
        await asyncio.sleep(1)
        return web.Response(text='not media')
    spawn = asyncio.create_subprocess_exec
    async def tracked_spawn(*args, **kwargs):
        child = await spawn(*args, **kwargs)
        children.append(child)
        return child
    start = player_http_source.PlayerHTTPSource.start
    async def tracked_start(proxy):
        proxies.append(proxy)
        await start(proxy)
    monkeypatch.setattr(asyncio, 'create_subprocess_exec', tracked_spawn)
    monkeypatch.setattr(player_http_source.PlayerHTTPSource, 'start', tracked_start)
    async with origin(handler) as base:
        monkeypatch.setattr(player_http_source, 'stored_http_source', lambda _: HTTPStreamSource(base + '/slow', {}))
        registry = RelayRegistry()
        claim = registry.try_open(HTTP_ID, 'Plex', 1)
        iterator = tuner_playback_service.relay_ranked_streams(None, [HTTP_ID], 'Plex', claim,
            registry=registry, attempt_seconds=.2 if ending == 'timeout' else 5, startup_budget_seconds=5)
        if ending == 'timeout':
            with pytest.raises(EngineStreamError):
                await anext(iterator)
        else:
            read = asyncio.create_task(anext(iterator))
            await asyncio.wait_for(entered.wait(), 3)
            read.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(read, 3)
    assert entered.is_set()
    assert children and all(child.returncode is not None for child in children)
    assert proxies and all(proxy._runner is None and not proxy._tasks for proxy in proxies)
    assert registry.count_active() == 0

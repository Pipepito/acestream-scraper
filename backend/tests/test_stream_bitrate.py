import pytest
from unittest.mock import AsyncMock

from app.services.stream_bitrate_service import sample_bitrate, probe_media


@pytest.mark.parametrize('value', ['N/A', None, -1, 0, 'nan', 'inf'])
def test_unknown_bitrate_is_not_download_speed(value):
    assert sample_bitrate({'format': {'bit_rate': value}, 'speed_down': 99999}) is None


def test_format_and_media_timestamp_estimates():
    assert sample_bitrate({'format': {'bit_rate': '8000000'}}) == 8_000_000
    assert sample_bitrate({'packets': [{'size': '100000', 'pts_time': '1'}, {'size': '100000', 'pts_time': '2'}]}) == 1_600_000


@pytest.mark.asyncio
async def test_probe_rejects_external_and_non_http_targets(monkeypatch):
    monkeypatch.setattr('app.services.stream_bitrate_service.shutil.which', lambda _: '/mock/ffprobe')
    get = AsyncMock()
    monkeypatch.setattr('httpx.AsyncClient.stream', get)
    for target in ['file:///etc/passwd', 'http://evil.test/media', None]:
        assert await probe_media('http://engine.test:6878', target) is None
    get.assert_not_called()


def test_bitrate_migration_preserves_existing_rows(tmp_path):
    from sqlalchemy import create_engine, inspect, text
    from migration_test_utils import upgrade_to_revision, database_url_for, upgrade_to_head
    path = tmp_path / 'bitrate.db'
    upgrade_to_revision(path, '20260903_1200')
    engine = create_engine(database_url_for(path))
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO acestream_channels (id, name) VALUES ('existing', 'Existing stream')"))
    upgrade_to_head(path)
    with engine.connect() as conn:
        assert conn.execute(text('SELECT name, bitrate_bps, bitrate_checked_at FROM acestream_channels')).one() == ('Existing stream', None, None)
    assert {'bitrate_bps', 'bitrate_checked_at'} <= {c['name'] for c in inspect(engine).get_columns('acestream_channels')}
    engine.dispose()


@pytest.mark.asyncio
async def test_media_probe_caps_input_and_reports_audio_without_network_ffprobe(monkeypatch):
    import json
    import httpx
    from unittest.mock import Mock
    from app.services.stream_bitrate_service import probe_media, SAMPLE_BYTES
    monkeypatch.setattr('app.services.stream_bitrate_service.shutil.which', lambda _: '/mock/ffprobe')
    factory = httpx.AsyncClient
    def handler(request):
        return httpx.Response(200, content=b'G' * (SAMPLE_BYTES + 100))
    monkeypatch.setattr('app.services.stream_bitrate_service.httpx.AsyncClient',
        lambda **kwargs: factory(transport=httpx.MockTransport(handler), **kwargs))
    process = Mock(returncode=0)
    process.communicate = AsyncMock(return_value=(json.dumps({'format': {'bit_rate': '8000000'}, 'streams': [
        {'codec_type': 'video'}, {'codec_type': 'audio', 'codec_name': 'ac3', 'channels': 2, 'channel_layout': 'stereo', 'tags': {'language': 'spa'}},
        {'codec_type': 'audio', 'codec_name': 'aac', 'tags': {'language': 'eng'}}]}).encode(), b''))
    spawn = AsyncMock(return_value=process)
    monkeypatch.setattr('app.services.stream_bitrate_service.asyncio.create_subprocess_exec', spawn)
    result = await probe_media('http://engine', 'http://engine/media')
    assert result['bitrate_bps'] == 8_000_000
    assert [track['language'] for track in result['audio_tracks']] == ['spa', 'eng']
    assert [track['index'] for track in result['audio_tracks']] == [0, 1]
    assert len(process.communicate.call_args.args[0]) == SAMPLE_BYTES
    argv = spawn.call_args.args
    assert argv[argv.index('-protocol_whitelist') + 1] == 'pipe'
    assert argv[-1] == 'pipe:0'


@pytest.mark.asyncio
async def test_probe_rejects_redirect_before_contacting_other_host(monkeypatch):
    import httpx
    from app.services.stream_bitrate_service import probe_media
    monkeypatch.setattr('app.services.stream_bitrate_service.shutil.which', lambda _: '/mock/ffprobe')
    factory = httpx.AsyncClient
    requested = []
    def handler(request):
        requested.append(request.url.host)
        return httpx.Response(302, headers={'location': 'http://evil/media'})
    monkeypatch.setattr('app.services.stream_bitrate_service.httpx.AsyncClient',
        lambda **kwargs: factory(transport=httpx.MockTransport(handler), **kwargs))
    assert await probe_media('http://engine', 'http://engine/media') is None
    assert requested == ['engine']

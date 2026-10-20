"""IPTV streams are checked over HTTP, never through the acestream engine.

An IPTV stream has an opaque `url:<sha1>` id. The engine cannot resolve it:
asked, it reports the stream missing, and the check would mark the whole
IPTV half of the catalogue -- 592 of 1,599 sources on a real installation -- dead.
They used to be skipped, so they stayed unknown forever; now they are
checked the way a player opens them: playlist, variant, a segment.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.models import AcestreamChannel
from app.services import http_stream_check, live_providers
from app.services.channel_status_service import ChannelStatusService


@pytest.fixture(autouse=True)
def isolated_queue(monkeypatch):
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue',
                        ProbeQueue(cooldown=0, outage_backoff=0))


@pytest.fixture
def probe(db_session, monkeypatch):
    service = ChannelStatusService(db_session)
    service._get_engine_url = lambda: 'http://engine.test:6878'
    service._get_timeout = lambda: 0.015
    service._engine_ready = AsyncMock(return_value=True)
    # If anyone asks the engine, it shows: it answers "not found".
    service._fetch_engine_response = AsyncMock(
        return_value=(200, {'response': None, 'error': 'not found'}, None))
    service.channel_repository = MagicMock()
    monkeypatch.setattr('app.services.channel_status_service.run_database_write',
                        AsyncMock(side_effect=lambda fn, *a, **k: fn(*a, **k)))
    return service


def _iptv(**kw):
    return AcestreamChannel(id='url:' + 'a' * 40, name='La 1',
                            stream_url='https://cdn.example.com/la1/master.m3u8',
                            stream_headers={'Referer': 'https://rtve.es/'}, **kw)


@pytest.mark.asyncio
async def test_engine_is_not_asked(probe, monkeypatch):
    monkeypatch.setattr(http_stream_check, 'check', lambda url, headers: (True, None))
    await probe.check_channel_status(_iptv(is_online=True))
    probe._fetch_engine_response.assert_not_awaited()


@pytest.mark.asyncio
async def test_checked_over_http_with_its_headers_and_saved(probe, monkeypatch):
    asked = []
    monkeypatch.setattr(http_stream_check, 'check', lambda url, headers: asked.append((url, headers)) or (False, 'HTTP 404 from the playlist'))
    result = await probe.check_channel_status(_iptv(is_online=True))
    assert asked == [('https://cdn.example.com/la1/master.m3u8', {'Referer': 'https://rtve.es/'})]
    assert result['is_online'] is False and result['status'] == 'offline'
    assert result['error'] == 'HTTP 404 from the playlist'
    probe.channel_repository.update_channel_status.assert_called_once_with(
        'url:' + 'a' * 40, False, 'HTTP 404 from the playlist')


@pytest.mark.asyncio
async def test_no_engine_needed(probe, monkeypatch):
    """An install without engine (such as a test container) still checks them."""
    probe._get_engine_url = lambda: None
    monkeypatch.setattr(http_stream_check, 'check', lambda url, headers: (True, None))
    result = await probe.check_channel_status(_iptv())
    assert result['status'] == 'online'


@pytest.mark.asyncio
async def test_nothing_written_without_persist(probe, monkeypatch):
    monkeypatch.setattr(http_stream_check, 'check', lambda url, headers: (True, None))
    await probe.check_channel_status(_iptv(), persist=False)
    assert not probe.channel_repository.method_calls


@pytest.mark.asyncio
async def test_acestream_still_goes_to_engine(probe):
    ace = AcestreamChannel(id='1' * 40, name='Canal', is_online=None)
    await probe.check_channel_status(ace)
    probe._fetch_engine_response.assert_awaited()


# --- the HTTP check itself ---------------------------------------------------

class FakeResponse:
    def __init__(self, status=200, body=b'', headers=None):
        self.status_code = status
        self.content = body
        self.headers = headers or {}


MASTER = b'#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\nhd/chunklist.m3u8\n#EXT-X-STREAM-INF:BANDWIDTH=2\nsd/chunklist.m3u8\n'
CHUNKLIST = b'#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:7\n#EXTINF:4,\nseg_7.ts\n#EXTINF:4,\nseg_8.ts\n'


@pytest.fixture
def origin(monkeypatch):
    table, asked = {}, []

    def fake_get(url, timeout=None, headers=None):
        asked.append((url, dict(headers or {})))
        if url not in table:
            return FakeResponse(404)
        return table[url]
    monkeypatch.setattr(http_stream_check, 'source_get', fake_get)
    return table, asked


def test_alive_via_master_variant_and_segment(origin):
    table, asked = origin
    table['https://cdn/la1/master.m3u8'] = FakeResponse(body=MASTER)
    table['https://cdn/la1/hd/chunklist.m3u8'] = FakeResponse(body=CHUNKLIST)
    table['https://cdn/la1/hd/seg_8.ts'] = FakeResponse(206, b'\x47' * 1024)
    assert http_stream_check.check('https://cdn/la1/master.m3u8', {'Referer': 'r'}) == (True, None)
    urls = [u for u, _ in asked]
    # The NEWEST segment: on a live list the oldest may already be gone.
    assert urls == ['https://cdn/la1/master.m3u8', 'https://cdn/la1/hd/chunklist.m3u8', 'https://cdn/la1/hd/seg_8.ts']
    assert all(h['Referer'] == 'r' for _, h in asked)
    # Only the first KB: the video is not downloaded.
    assert asked[-1][1]['Range'] == 'bytes=0-1023'


def test_unreachable_segment_means_dead(origin):
    table, _ = origin
    table['https://cdn/x.m3u8'] = FakeResponse(body=CHUNKLIST)
    alive, why = http_stream_check.check('https://cdn/x.m3u8')
    assert alive is False and 'segment' in why


def test_403_is_dead_and_says_where(origin):
    table, _ = origin
    table['https://cdn/x.m3u8'] = FakeResponse(403)
    assert http_stream_check.check('https://cdn/x.m3u8') == (False, 'HTTP 403 from the playlist')


def test_playlist_without_segments_is_dead(origin):
    table, _ = origin
    table['https://cdn/x.m3u8'] = FakeResponse(body=b'#EXTM3U\n#EXT-X-VERSION:3\n')
    assert http_stream_check.check('https://cdn/x.m3u8') == (False, 'Playlist without segments')


def test_redirects_followed_and_relative_urls_resolve_against_final(origin):
    table, _ = origin
    table['https://a/x.m3u8'] = FakeResponse(302, headers={'Location': 'https://b/live/x.m3u8'})
    table['https://b/live/x.m3u8'] = FakeResponse(body=CHUNKLIST)
    table['https://b/live/seg_8.ts'] = FakeResponse(200, b'\x47')
    assert http_stream_check.check('https://a/x.m3u8') == (True, None)


def test_origin_serving_video_directly_is_alive(origin):
    table, _ = origin
    table['https://cdn/stream.ts'] = FakeResponse(body=b'\x47' * 188)
    assert http_stream_check.check('https://cdn/stream.ts') == (True, None)


def test_network_failure_does_not_crash(monkeypatch):
    def boom(url, timeout=None, headers=None):
        raise ConnectionError('refused')
    monkeypatch.setattr(http_stream_check, 'source_get', boom)
    alive, why = http_stream_check.check('https://cdn/x.m3u8')
    assert alive is False and 'refused' in why


def test_broadcaster_stream_is_only_resolved(origin, monkeypatch):
    """A login and an ad-stitching request per check would be too much for
    Mediaset; a signed link is what breaks when they change their API."""
    _table, asked = origin
    monkeypatch.setattr(live_providers, 'resolve', lambda url: 'https://dai/master.m3u8')
    assert http_stream_check.check('mediaset://T5') == (True, None)
    monkeypatch.setattr(live_providers, 'resolve', lambda url: None)
    assert http_stream_check.check('mediaset://T5') == (False, 'The broadcaster did not return a live link')
    assert asked == []


def test_empty_segment_is_not_alive(origin):
    table, _ = origin
    table['https://cdn/x.m3u8'] = FakeResponse(body=CHUNKLIST)
    table['https://cdn/seg_8.ts'] = FakeResponse(200, b'')
    assert http_stream_check.check('https://cdn/x.m3u8') == (False, 'Empty segment')


def test_relative_variant_resolves_against_master_redirect_target(origin):
    table, asked = origin
    table['https://a/master.m3u8'] = FakeResponse(302, headers={'Location': 'https://b/live/master.m3u8'})
    table['https://b/live/master.m3u8'] = FakeResponse(body=MASTER)
    table['https://b/live/hd/chunklist.m3u8'] = FakeResponse(body=CHUNKLIST)
    table['https://b/live/hd/seg_8.ts'] = FakeResponse(200, b'\x47')
    assert http_stream_check.check('https://a/master.m3u8') == (True, None)


# --- the scheduled pass without an engine ------------------------------------
# HTTP streams need no engine, but the pass used to return before looking at
# any stream when none was configured: an install without an engine never
# checked its HTTP streams.

def test_the_pass_checks_http_streams_without_an_engine(db_session, monkeypatch):
    import threading
    from app.models.models import AcestreamChannel
    from app.services.task_service import task_service
    from app.tasks import channel_status_task
    # A fresh shutdown flag: an earlier test that stops the app leaves the
    # process-wide one set, and the pass would stop before checking anything.
    monkeypatch.setattr(task_service, 'shutdown_event', threading.Event())
    db_session.add_all([
        AcestreamChannel(id='url:' + 'a' * 40, name='HTTP', is_active=True,
                         stream_url='https://cdn.example.com/a.m3u8'),
        AcestreamChannel(id='b' * 40, name='Ace', is_active=True),
    ])
    db_session.commit()
    checked = []

    class Service:
        def __init__(self, db):
            pass

        def _get_engine_url(self):
            return None

        async def check_channel_status(self, channel, **kwargs):
            checked.append(channel.id)
            return {"status": "checked", "is_online": True}

    monkeypatch.setattr(channel_status_task, 'SessionLocal', lambda: db_session)
    monkeypatch.setattr(channel_status_task, 'ChannelStatusService', Service)
    monkeypatch.setattr(db_session, 'close', lambda: None)
    result = channel_status_task.run_channel_status_task()
    assert checked == ['url:' + 'a' * 40]
    assert result['checked'] == 1


def test_without_an_engine_or_http_streams_the_pass_is_disabled(db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.tasks import channel_status_task
    db_session.add(AcestreamChannel(id='b' * 40, name='Ace', is_active=True))
    db_session.commit()

    class Service:
        def __init__(self, db):
            pass

        def _get_engine_url(self):
            return None

    monkeypatch.setattr(channel_status_task, 'SessionLocal', lambda: db_session)
    monkeypatch.setattr(channel_status_task, 'ChannelStatusService', Service)
    monkeypatch.setattr(db_session, 'close', lambda: None)
    result = channel_status_task.run_channel_status_task()
    assert result['checked'] == 0
    assert 'No engine configured' in result['message']


def test_run_now_without_an_engine_runs_when_there_are_http_streams(client, db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.services.task_service import task_service
    monkeypatch.setattr(task_service, 'run_task_now', lambda job_id: 'triggered')
    disabled = client.post('/api/v1/background-tasks/channel_status/run').json()
    db_session.add(AcestreamChannel(id='url:' + 'c' * 40, name='HTTP', is_active=True,
                                    stream_url='https://cdn.example.com/c.m3u8'))
    db_session.commit()
    queued = client.post('/api/v1/background-tasks/channel_status/run').json()
    assert disabled['status'] == 'disabled'
    assert queued['status'] == 'triggered'

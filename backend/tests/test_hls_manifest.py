"""HLS streams with headers: their manifests are served whole, by us.

Each rule comes with what it was measured against (2026-10-01):

  the prune      cdnmedia's chunklist carries 2,656 segments and ffmpeg
                 stopped at 8,635 of 108,546 bytes; a window of 10 fixes it.
  the segments   stay on the CDN ON PURPOSE: ffmpeg sends them the pipe's
                 headers. Rewritten through us, the video of every such
                 channel would cross the server unnoticed.
  the master     EVERY variant is rewritten; pointing at one played 720p
                 where there was 1080p.
  the sequence   pruning without recomputing it makes the player believe
                 the broadcast restarts at each reload.
  the signature  without it the server is an open proxy for the LAN.
"""
import pytest

from app.models.models import AcestreamChannel
from app.services import hls_manifest
from app.services.hls_manifest import is_master, is_signed, prune, rewrite_master, serve, sign
from app.services.m3u_service import M3UService
from app.services.playlist_service import PlaylistService

ORIGIN = 'https://cdn.example/dir/playlist.m3u8?DVR'

MASTER = '\n'.join([
    '#EXTM3U',
    '#EXT-X-VERSION:3',
    '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3160000,RESOLUTION=1280x720',
    '/live/alta/chunklist.m3u8?DVR',
    '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=825000,RESOLUTION=640x368',
    'baja/chunklist.m3u8?DVR',
])


def _link(url):
    return f'/live/x?u={url}&s={sign(url)}'


def _chunklist(n, first=1000):
    lines = ['#EXTM3U', '#EXT-X-VERSION:3', '#EXT-X-TARGETDURATION:10', f'#EXT-X-MEDIA-SEQUENCE:{first}']
    for i in range(n):
        lines += ['#EXTINF:6.0,', f'media_{first + i}.ts']
    return '\n'.join(lines)


def _urls(text):
    return [x for x in text.splitlines() if x and not x.startswith('#')]


def _encrypted(n, first=1000, every=5):
    """A chunklist whose key rotates every `every` segments."""
    lines = ['#EXTM3U', '#EXT-X-VERSION:3', '#EXT-X-TARGETDURATION:10', f'#EXT-X-MEDIA-SEQUENCE:{first}']
    for i in range(n):
        if i % every == 0:
            lines.append(f'#EXT-X-KEY:METHOD=AES-128,URI="https://scrt/k{i // every}"')
        lines += ['#EXTINF:4.0,', f'media_{first + i}.ts']
    return '\n'.join(lines)


def _every_segment_has_a_key(text):
    key = None
    for line in text.splitlines():
        if line.startswith('#EXT-X-KEY'):
            key = line
        elif line and not line.startswith('#'):
            if key is None:
                return False
    return True


# --- the rewriting ----------------------------------------------------------

def test_master_is_told_apart_from_chunklist():
    assert is_master(MASTER)
    assert not is_master(_chunklist(3))


def test_master_keeps_both_qualities():
    out = rewrite_master(MASTER, ORIGIN, _link)
    assert len(_urls(out)) == 2
    assert out.count('RESOLUTION=1280x720') == 1 and out.count('RESOLUTION=640x368') == 1


def test_variants_route_through_us_absolute_and_signed():
    out = rewrite_master(MASTER, ORIGIN, _link)
    urls = _urls(out)
    assert all(u.startswith('/live/x?u=') for u in urls)
    # Relative ones are resolved against the origin BEFORE signing: on the
    # other side there is no telling where they came from.
    assert '/live/x?u=https://cdn.example/dir/baja/chunklist.m3u8?DVR&s=' in out
    assert '/live/x?u=https://cdn.example/live/alta/chunklist.m3u8?DVR&s=' in out


def test_prune_keeps_exactly_the_window():
    assert len(_urls(prune(_chunklist(2656), ORIGIN, window=10))) == 10


def test_segments_stay_on_the_cdn():
    for url in _urls(prune(_chunklist(50), ORIGIN, window=5)):
        assert url.startswith('https://cdn.example/dir/media_')


def test_media_sequence_is_recomputed():
    out = prune(_chunklist(50, first=1000), ORIGIN, window=5)
    assert '#EXT-X-MEDIA-SEQUENCE:1045' in out.splitlines()


def test_completed_playlist_keeps_endlist():
    """A genuinely completed stream must retain its ending."""
    assert '#EXT-X-ENDLIST' in prune(_chunklist(20) + '\n#EXT-X-ENDLIST', ORIGIN, window=5)


def test_signature_rejects_any_other_url():
    url = 'https://cdn.example/dir/chunklist.m3u8'
    assert is_signed(url, sign(url))
    assert not is_signed('https://elsewhere.example/anything', sign(url))
    assert not is_signed(url, '')
    assert not is_signed(url, 'a' * 32)


def test_chunklist_without_segments_does_not_crash():
    assert prune('#EXTM3U\n#EXT-X-VERSION:3\n', ORIGIN).startswith('#EXTM3U')


def test_serve_picks_master_or_chunklist():
    assert '/live/x?u=' in serve(MASTER, ORIGIN, _link)
    chunklist = serve(_chunklist(30), ORIGIN, _link, window=3)
    assert len(_urls(chunklist)) == 3 and '/live/' not in chunklist


def test_no_segment_is_left_without_its_key():
    """A key holds from where it appears to the next one. Measured with
    RTV Cardedeu: the origin's chunklist played 2 of 4, ours 0 of 4, with
    every tag present but the key AFTER two segments."""
    out = prune(_encrypted(100), ORIGIN, window=7)
    assert _every_segment_has_a_key(out)
    assert len(_urls(out)) == 7


def test_key_is_not_repeated_per_segment():
    assert prune(_encrypted(100, every=50), ORIGIN, window=10).count('#EXT-X-KEY') == 1


def test_all_keys_kept_when_key_rotates_inside_window():
    out = prune(_encrypted(100, every=3), ORIGIN, window=10)
    assert out.count('#EXT-X-KEY') >= 3
    assert _every_segment_has_a_key(out)


def test_init_map_comes_first():
    text = ('#EXTM3U\n#EXT-X-VERSION:7\n#EXT-X-MEDIA-SEQUENCE:100\n'
            '#EXT-X-MAP:URI="https://cdn/init.mp4"\n'
            + ''.join(f'#EXTINF:4.0,\nseg_{i}.m4s\n' for i in range(40)))
    out = prune(text, ORIGIN, window=5)
    assert out.index('#EXT-X-MAP') < out.index('seg_35.m4s')


def test_discontinuity_stays_with_its_segment():
    text = ('#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:4.0,\na.ts\n'
            '#EXT-X-DISCONTINUITY\n#EXTINF:4.0,\nb.ts\n#EXTINF:4.0,\nc.ts\n')
    lines = prune(text, ORIGIN, window=3).splitlines()
    position = lines.index('#EXT-X-DISCONTINUITY')
    assert lines[position + 2].endswith('b.ts')
    assert lines.count('#EXT-X-DISCONTINUITY') == 1


def test_key_holds_wherever_it_falls():
    """The bug was heads or tails on every reload: the window moves, and the
    key fell before it (played) or inside it (did not). One position can
    pass by luck, so all of them are tried."""
    for every in (1, 2, 3, 5, 7, 11):
        for window in (1, 2, 5, 10, 13):
            for total in (20, 37, 100):
                out = prune(_encrypted(total, every=every), ORIGIN, window=window)
                assert _every_segment_has_a_key(out), (every, window, total)


# --- the playlist -----------------------------------------------------------

HEADERS = {'Referer': 'https://player.instantvideocloud.net/', 'User-Agent': 'Mozilla/5.0 (X11) Chrome/1'}
URL = 'https://liveingesta318.cdnmedia.tv/101weblive/malaga/playlist.m3u8'


def test_with_headers_playlist_points_to_live_and_carries_them():
    """The headers still travel: the segments go straight to the CDN."""
    link = PlaylistService._stream_link('http://engine/', 'url:abc', stream_url=URL, stream_headers=HEADERS,
                                        live_base_url='http://192.168.1.5:8000')
    assert link.startswith('http://192.168.1.5:8000/live/url%3Aabc|')
    assert 'Referer=https%3A%2F%2Fplayer.instantvideocloud.net%2F' in link


def test_without_headers_link_stays_direct():
    assert PlaylistService._stream_link('http://engine/', 'url:abc', stream_url=URL,
                                        live_base_url='http://192.168.1.5:8000') == URL


def test_without_public_address_output_is_unchanged():
    """Callers that do not know the public address keep the old output."""
    link = PlaylistService._stream_link('http://engine/', 'url:abc', stream_url=URL, stream_headers=HEADERS)
    assert link.startswith(URL + '|')


# --- the route --------------------------------------------------------------

class FakeResponse:
    def __init__(self, status=200, body=b'', headers=None):
        self.status_code = status
        self.content = body
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')


@pytest.fixture
def lan(monkeypatch):
    from app.config.settings import get_settings
    from app.services.tuner_network import get_tuner_gate
    try:
        with monkeypatch.context() as scoped:
            scoped.setenv("TUNER_ALLOWED_NETWORKS", "*")
            get_settings.cache_clear(); get_tuner_gate.cache_clear()
            yield
    finally:
        get_settings.cache_clear(); get_tuner_gate.cache_clear()


@pytest.fixture
def origin(monkeypatch):
    """The CDN, as a table of URL -> response; records what was asked."""
    from app.api.endpoints import live
    table, asked = {}, []

    async def fake_get(url, timeout=None, headers=None, **kwargs):
        asked.append((url, dict(headers or {})))
        if url not in table:
            raise AssertionError(f'unexpected fetch: {url}')
        return table[url]
    monkeypatch.setattr(live, 'source_get', fake_get)
    return table, asked


def _add(db_session, url=URL, headers=HEADERS):
    stream = AcestreamChannel(id=M3UService._stream_id(url), name='101TV Málaga',
                              stream_url=url, stream_headers=headers)
    db_session.add(stream)
    db_session.commit()
    return stream


def test_chunklist_is_served_pruned_with_content_length(lan, client, db_session, origin):
    table, asked = origin
    stream = _add(db_session)
    table[URL] = FakeResponse(body=_chunklist(2656).encode())
    response = client.get(f'/live/{stream.id}')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('application/vnd.apple.mpegurl')
    # Served whole, never chunked: what ffmpeg reads to the end.
    assert int(response.headers['content-length']) == len(response.content)
    assert 'transfer-encoding' not in response.headers
    segments = _urls(response.text)
    assert len(segments) == hls_manifest.WINDOW
    assert all(s.startswith('https://liveingesta318.cdnmedia.tv/101weblive/malaga/media_') for s in segments)
    # Fetched with the headers the playlist publishes.
    assert asked == [(URL, HEADERS)]


def test_master_variants_are_fetched_signed(lan, client, db_session, origin):
    table, asked = origin
    stream = _add(db_session)
    table[URL] = FakeResponse(body=MASTER.encode())
    master = client.get(f'/live/{stream.id}').text
    variant = [u for u in _urls(master) if 'baja' in u][0]
    assert variant.startswith(f'/live/{stream.id.replace(":", "%3A")}?u=')
    table['https://liveingesta318.cdnmedia.tv/101weblive/malaga/baja/chunklist.m3u8?DVR'] = FakeResponse(body=_chunklist(30).encode())
    response = client.get(variant)
    assert response.status_code == 200
    assert len(_urls(response.text)) == hls_manifest.WINDOW
    assert asked[-1] == ('https://liveingesta318.cdnmedia.tv/101weblive/malaga/baja/chunklist.m3u8?DVR', HEADERS)


def test_unsigned_url_is_not_fetched(lan, client, db_session, origin):
    """Not an open proxy: nobody on the LAN can make the server fetch anything."""
    _table, asked = origin
    stream = _add(db_session)
    response = client.get(f'/live/{stream.id}', params={'u': 'http://169.254.169.254/latest/', 's': 'a' * 32})
    assert response.status_code == 403
    assert asked == []


def test_redirects_are_followed_and_relative_ones_resolved(lan, client, db_session, origin):
    table, asked = origin
    stream = _add(db_session)
    table[URL] = FakeResponse(status=302, headers={'Location': '/edge/playlist.m3u8'})
    table['https://liveingesta318.cdnmedia.tv/edge/playlist.m3u8'] = FakeResponse(body=_chunklist(5).encode())
    response = client.get(f'/live/{stream.id}')
    assert response.status_code == 200
    # Segments resolve against where the manifest really came from.
    assert _urls(response.text)[0].startswith('https://liveingesta318.cdnmedia.tv/edge/media_')
    assert [u for u, _ in asked] == [URL, 'https://liveingesta318.cdnmedia.tv/edge/playlist.m3u8']


def test_origin_serving_video_is_handed_to_kodi(lan, client, db_session, origin):
    table, _ = origin
    stream = _add(db_session)
    table[URL] = FakeResponse(body=b'\x47' * 4000)
    response = client.get(f'/live/{stream.id}', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == URL


def test_origin_failure_is_502(lan, client, db_session, origin):
    table, _ = origin
    stream = _add(db_session)
    table[URL] = FakeResponse(status=403)
    assert client.get(f'/live/{stream.id}').status_code == 502


def test_head_makes_no_outbound_request(lan, client, db_session, origin):
    _table, asked = origin
    stream = _add(db_session)
    response = client.head(f'/live/{stream.id}')
    assert response.status_code == 200
    assert asked == []


def test_iptv_without_headers_is_not_served_here(lan, client, db_session, origin):
    _table, asked = origin
    stream = _add(db_session, url='https://cdn.example/libre.m3u8', headers=None)
    assert client.get(f'/live/{stream.id}').status_code == 404
    assert asked == []


def test_hung_origin_is_also_time_limited(lan, client, db_session, monkeypatch):
    import time as clock
    from app.api.endpoints import live
    stream = _add(db_session)
    monkeypatch.setattr(live, 'OPEN_BUDGET_SECONDS', 0.3)
    import asyncio
    cancelled = []
    async def hang(*args, **kwargs):
        try:
            await asyncio.sleep(2)
        finally:
            cancelled.append(True)
    monkeypatch.setattr(live, 'source_get', hang)
    started = clock.monotonic()
    assert client.get(f'/live/{stream.id}').status_code == 502
    assert clock.monotonic() - started < 1.5
    assert cancelled == [True]

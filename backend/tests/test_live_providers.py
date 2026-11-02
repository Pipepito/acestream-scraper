"""Broadcasters' live channels: imported from their website, resolved when opened.

No network: `base.http` is replaced by a fake that answers from a table and
fails the test on any URL it was not given.
"""
import pytest

from app.models.models import AcestreamChannel
from app.services import live_providers
from app.services.live_providers import apunt, atresplayer, base, mediaset, sietetv, telemadrid
from app.services.m3u_service import M3UService
from app.services.playlist_service import PlaylistService


class FakeHttp:
    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def _answer(self, method, url, headers, body=None):
        self.calls.append((method, url, dict(headers or {}), body))
        for prefix, answer in self.answers.items():
            if url.startswith(prefix):
                if isinstance(answer, Exception):
                    raise answer
                return answer(url) if callable(answer) else answer
        raise AssertionError(f'unexpected request: {method} {url}')

    def get_json(self, url, headers=None):
        return self._answer('GET', url, headers)

    def post_json(self, url, body, headers=None):
        return self._answer('POST', url, headers, body)

    def get_text(self, url, headers=None, max_bytes=None):
        self.max_bytes = max_bytes
        return self._answer('GET', url, headers)


@pytest.fixture
def fake(monkeypatch):
    def install(answers):
        http = FakeHttp(answers)
        monkeypatch.setattr(base, 'http', http)
        return http
    monkeypatch.setattr(telemadrid, '_policy_key', None)
    monkeypatch.setattr(apunt, '_policy_key', None)
    monkeypatch.setattr(apunt, '_live_ids', {})
    return install


# --- which source and which stream belongs to whom --------------------------

@pytest.mark.parametrize('url, provider', [
    ('https://www.atresplayer.com/directos/', atresplayer),
    ('https://atresplayer.com', atresplayer),
    ('https://www.mediasetinfinity.es/', mediaset),
    ('https://www.7riojaplay.tv/', sietetv),
    ('https://www.telemadrid.es/', telemadrid),
    ('https://www.apuntmedia.es/', apunt),
    ('https://apuntmedia.es/directe/directe-tv_136_1392524.html', apunt),
])
def test_broadcaster_website_is_recognised(url, provider):
    assert live_providers.for_source_url(url) is provider


@pytest.mark.parametrize('url', [
    'https://evil-atresplayer.com/', 'https://atresplayer.com.example.org/',
    'https://evil-apuntmedia.es/', 'https://apuntmedia.es.example.org/', 'https://apuntmedia.es.evil.test/',
    'https://www.tdtchannels.com/lists/tv.m3u', '',
])
def test_lookalike_website_is_not_recognised(url):
    assert live_providers.for_source_url(url) is None


def test_scheme_selects_resolver():
    assert live_providers.for_stream_url('mediaset://T5') is mediaset
    assert live_providers.for_stream_url('7riojaplay://x8dhao1') is sietetv
    assert live_providers.for_stream_url('apunt://6137605659001') is apunt
    assert live_providers.for_stream_url('apuntmedia://6137605659001') is None
    assert live_providers.for_stream_url('https://cdn.example.com/a.m3u8') is None
    assert live_providers.for_stream_url(None) is None


# --- importing them ---------------------------------------------------------

def _imported(provider):
    return {name: meta for _id, name, meta in
            M3UService().extract_channels_from_content(live_providers.playlist(provider))}


def test_mediaset_imported_with_referer_and_guide():
    streams = _imported(mediaset)
    assert set(streams) == {'Telecinco', 'Cuatro', 'FDF', 'Divinity', 'Energy', 'Be Mad', 'Boing'}
    telecinco = streams['Telecinco']
    assert telecinco['stream_url'] == 'mediaset://T5'
    # Without the Referer the manifest answers 403.
    assert telecinco['stream_headers'] == {'Referer': mediaset.REFERER}
    assert telecinco['tvg_id'] == 'Telecinco.TV'
    assert telecinco['group_title'] == 'Generalistas'


def test_apunt_imported_with_name_guide_and_group():
    streams = _imported(apunt)
    assert set(streams) == {'À Punt'}
    channel = streams['À Punt']
    assert channel['stream_url'] == 'apunt://6137605659001'
    assert channel['tvg_id'] == 'APunt.TV'
    assert channel['group_title'] == 'Valencia'
    # Playback needs no header, so none is stored or sent.
    assert apunt.PLAY_HEADERS == {}
    assert 'stream_headers' not in channel


@pytest.mark.parametrize('provider', [atresplayer, mediaset, sietetv, telemadrid, apunt])
def test_every_play_header_survives_the_import(provider, fake):
    """Checks, /live/ and the player use the headers the import stored, so one
    the import drops is never sent. 7 TV's CDN answers 403 without Sec-Fetch-Mode."""
    if provider is atresplayer:
        fake({f'{atresplayer.API}/client/v1/info/channels': [{'title': 'Antena 3', 'id': 'a3'}]})
    for meta in _imported(provider).values():
        assert meta.get('stream_headers', {}) == provider.PLAY_HEADERS


def test_sec_fetch_mode_reaches_kodi():
    link = PlaylistService._stream_link('x', 'url:x', stream_url='https://cdn/live.m3u8',
                                        stream_headers=dict(sietetv.PLAY_HEADERS))
    assert '&Sec-Fetch-Mode=cors' in link, link


def test_atresplayer_fetches_channels_and_keeps_only_tv(fake):
    fake({f'{atresplayer.API}/client/v1/info/channels': [
        {'title': 'Antena 3', 'id': 'a3'}, {'title': 'Nova', 'id': 'nv'},
        {'title': 'Flooxer', 'id': 'fx'}, {'title': 'laSexta'},
    ]})
    streams = _imported(atresplayer)
    assert set(streams) == {'Antena 3', 'Nova'}
    assert streams['Nova']['stream_url'] == 'atresplayer://nv'
    assert 'stream_headers' not in streams['Nova']
    # dobleM's ids: the only public guide found with all six.
    assert streams['Antena 3']['tvg_id'] == 'Antena 3 HD'
    assert streams['Nova']['tvg_id'] == 'Nova'


def test_broadcaster_website_is_not_downloaded(fake, monkeypatch):
    """Scraping the website imports its channels without fetching the page."""
    import asyncio
    from app.models.url_types import RegularURL
    from app.scrapers.http import HTTPScraper

    async def no_fetch(self, url):
        raise AssertionError('the website itself must not be fetched')
    monkeypatch.setattr(HTTPScraper, 'fetch_content', no_fetch)

    async def no_status(self, url, status, error=None):
        return None
    monkeypatch.setattr(HTTPScraper, 'update_url_status', no_status)

    scraper = HTTPScraper(RegularURL('https://www.telemadrid.es/'))
    channels, status = asyncio.run(scraper.scrape())
    assert status == 'OK'
    assert {(name, meta['stream_url']) for _id, name, meta in channels} == {
        ('Telemadrid', 'telemadrid://ref:Live_Telemadrid'), ('La Otra', 'telemadrid://ref:Live_LaOtra')}


# --- the playlist -----------------------------------------------------------

def _stream(stream_url, headers=None):
    return AcestreamChannel(id=M3UService._stream_id(stream_url), name='X',
                            stream_url=stream_url, stream_headers=headers)


def test_playlist_points_to_live_with_headers():
    stream = _stream('mediaset://T5', {'Referer': mediaset.REFERER})
    link = PlaylistService._stream_link('http://engine:6878/ace/getstream?id=', stream.id,
                                        stream_url=stream.stream_url, stream_headers=stream.stream_headers,
                                        live_base_url='http://192.168.1.5:8000/')
    assert link == ('http://192.168.1.5:8000/live/' + stream.id.replace(':', '%3A')
                    + '|Referer=https%3A%2F%2Fwww.mediasetinfinity.es%2F')


def test_plain_iptv_link_is_emitted_unchanged():
    link = PlaylistService._stream_link('http://engine/', 'url:abc',
                                        stream_url='https://cdn.example.com/a.m3u8',
                                        live_base_url='http://192.168.1.5:8000')
    assert link == 'https://cdn.example.com/a.m3u8'


def test_without_public_address_no_link_is_invented():
    with pytest.raises(ValueError):
        PlaylistService._stream_link('http://engine/', 'url:abc', stream_url='mediaset://T5')


def test_server_playlist_uses_public_address(client, db_session):
    db_session.add(_stream('telemadrid://ref:Live_LaOtra'))
    db_session.commit()
    body = client.get('/playlist.m3u?only_online=false').text
    assert '/live/url%3A' in body
    assert 'telemadrid://' not in body


# --- opening them -----------------------------------------------------------

@pytest.fixture
def lan(monkeypatch):
    """The test client is not a LAN address; open the gate like the tuner tests do."""
    from app.config.settings import get_settings
    from app.services.tuner_network import get_tuner_gate
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    yield
    get_settings.cache_clear(); get_tuner_gate.cache_clear()


def test_not_opened_outside_allowed_networks(client, db_session, monkeypatch):
    """Token-free, so gated like the tuner: no outbound request for strangers."""
    stream = _stream('mediaset://T5')
    db_session.add(stream)
    db_session.commit()
    monkeypatch.setattr(live_providers, 'resolve', lambda url: pytest.fail('must not resolve'))
    assert client.get(f'/live/{stream.id}', follow_redirects=False).status_code == 403

def test_open_redirects_to_freshly_signed_link(lan, client, db_session, monkeypatch):
    stream = _stream('mediaset://T5', {'Referer': mediaset.REFERER})
    db_session.add(stream)
    db_session.commit()
    from app.api.endpoints import live
    monkeypatch.setattr(live, '_recent', {})
    asked = []
    monkeypatch.setattr(live_providers, 'resolve',
                        lambda url: asked.append(url) or 'https://dai.example/master.m3u8?hdnea=1')
    response = client.get(f'/live/{stream.id}', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['location'] == 'https://dai.example/master.m3u8?hdnea=1'
    assert asked == ['mediaset://T5']


def test_one_open_resolves_once_and_head_does_not_wait(lan, client, db_session, monkeypatch):
    """Kodi opens with HEAD, then two GETs: one resolution, not three."""
    from app.api.endpoints import live
    stream = _stream('mediaset://T5')
    db_session.add(stream)
    db_session.commit()
    asked = []
    monkeypatch.setattr(live_providers, 'resolve', lambda url: asked.append(url) or f'https://dai/{len(asked)}.m3u8')
    monkeypatch.setattr(live, '_recent', {})
    clock = [1000.0]
    monkeypatch.setattr(live.time, 'monotonic', lambda: clock[0])
    head = client.head(f'/live/{stream.id}', follow_redirects=False)
    # Answered at once, without resolving: Kodi gives it five seconds and
    # Mediaset takes about six.
    assert head.status_code == 200
    assert head.headers['content-type'] == 'application/vnd.apple.mpegurl'
    assert asked == []
    for _ in range(2):
        assert client.get(f'/live/{stream.id}', follow_redirects=False).headers['location'] == 'https://dai/1.m3u8'
    assert len(asked) == 1
    # A reconnect later must sign a new link: an old master answers 403.
    clock[0] += live.REUSE_SECONDS + 1
    assert client.get(f'/live/{stream.id}', follow_redirects=False).headers['location'] == 'https://dai/2.m3u8'


def test_no_link_from_broadcaster_is_502(lan, client, db_session, monkeypatch):
    stream = _stream('mediaset://T5')
    db_session.add(stream)
    db_session.commit()
    from app.api.endpoints import live
    monkeypatch.setattr(live, '_recent', {})
    monkeypatch.setattr(live_providers, 'resolve', lambda url: None)
    assert client.get(f'/live/{stream.id}', follow_redirects=False).status_code == 502


@pytest.mark.parametrize('stream_url', [None, 'https://cdn.example.com/a.m3u8'])
def test_non_broadcaster_stream_is_json_404_not_spa(lan, client, db_session, monkeypatch, stream_url):
    """An unknown id answers JSON 404: the SPA fallback would answer HTTP 200
    with index.html, which a player would try to play."""
    monkeypatch.setattr(live_providers, 'resolve', lambda url: pytest.fail('nothing to resolve'))
    stream_id = 'url:nothing'
    if stream_url:
        stream = _stream(stream_url)
        db_session.add(stream)
        db_session.commit()
        stream_id = stream.id
    response = client.get(f'/live/{stream_id}', follow_redirects=False)
    assert response.status_code == 404
    assert response.headers['content-type'].startswith('application/json')
    assert client.head(f'/live/{stream_id}', follow_redirects=False).status_code == 404


# --- resolving each one -----------------------------------------------------

def test_broadcaster_failure_is_not_an_exception(fake):
    fake({atresplayer.API: ConnectionError('down')})
    assert live_providers.resolve('atresplayer://nv') is None


def test_atresplayer_takes_first_source(fake):
    fake({f'{atresplayer.API}/player/v1/live/nv': {'sourcesLive': [
        {'src': ' '}, {'src': 'https://a/hlsts/nova.m3u8'}, {'src': 'https://a/legacy.m3u8'}]}})
    assert live_providers.resolve('atresplayer://nv') == 'https://a/hlsts/nova.m3u8'


def test_mediaset_makes_three_calls(fake):
    http = fake({
        f'{mediaset.API}/idm/v3.0/anonymous/login': {'response': {'sid': 's 1', 'beToken': 'tok'}},
        f'{mediaset.API}/playback/v3.0/check': {'isOk': True, 'response': {'dai': {'assetKey': 'k/1'}}},
        'https://pubads.g.doubleclick.net/ssai/event/': {'stream_manifest': 'https://dai/master.m3u8'},
    })
    assert live_providers.resolve('mediaset://T5') == 'https://dai/master.m3u8'
    login, check, dai = http.calls
    assert check[1].endswith('check?sid=s%201')
    assert check[2]['Authorization'] == 'Bearer tok'
    assert check[3]['channelCode'] == 'T5'
    assert dai[1] == 'https://pubads.g.doubleclick.net/ssai/event/k/1/streams'
    assert dai[2]['Referer'] == mediaset.REFERER


def test_mediaset_refusal_stops_there(fake):
    http = fake({
        f'{mediaset.API}/idm/v3.0/anonymous/login': {'response': {'sid': 's', 'beToken': 't'}},
        # A refusal is trusted even if the body still carries a key.
        f'{mediaset.API}/playback/v3.0/check': {'isOk': False, 'error': {'message': "doesn't have rights to"},
                                                'response': {'dai': {'assetKey': 'k'}}},
    })
    assert live_providers.resolve('mediaset://AC') is None
    assert len(http.calls) == 2


def test_7tv_without_embed_permission_gives_no_link(fake):
    http = fake({'https://geo.dailymotion.com/videos/x8dhao1': {
        'error': {'code': 'DM016', 'reason': 'embed_rules'}}})
    assert live_providers.resolve('7riojaplay://x8dhao1') is None
    # Asked the way the broadcaster's embedded player asks.
    headers = http.calls[0][2]
    assert headers['x-dm-geo-embedder'] == sietetv.WEB
    assert (headers['x-dm-geo-player-id'], headers['x-dm-geo-publisher-id']) == ('x11h8c', 'x2mgfup')


def test_7tv_returns_master(fake):
    fake({'https://geo.dailymotion.com/videos/x8dhao1': {
        'stream': {'stream_type': 'live', 'url': 'https://cdndirector/live/x8dhao1.m3u8?sec=1'}}})
    assert live_providers.resolve('7riojaplay://x8dhao1') == 'https://cdndirector/live/x8dhao1.m3u8?sec=1'


def test_pluto_and_7tv_masters_are_served_not_redirected():
    """Behind WARP a redirect hands the player a master bound to the server's
    address: both 7 TV and Pluto answered it 403."""
    from app.services.live_providers import pluto
    assert sietetv.SERVE_MANIFEST and pluto.SERVE_MANIFEST


def test_7tv_plays_like_a_browser():
    """Measured on 2026-10-15: without a browser User-Agent AND Sec-Fetch-Mode: cors
    the manifest answers 403; with them, 200."""
    assert sietetv.PLAY_HEADERS['Sec-Fetch-Mode'] == 'cors'
    assert sietetv.PLAY_HEADERS['User-Agent'].startswith('Mozilla/5.0')


def _brightcove(duration=-1):
    return {'duration': duration, 'sources': [
        {'type': 'application/dash+xml', 'src': 'https://bc/live.mpd'},
        {'type': 'application/x-mpegURL', 'src': 'https://bc/live.m3u8'}]}


def test_telemadrid_reads_its_player_script_past_the_default_bound(fake):
    """The script weighs 3.5 MB (02-11), more than the 2 MiB bound: the key is
    in it, so it is asked for with room enough."""
    from app.services.live_providers import telemadrid
    http = fake({telemadrid.PLAYER_JS: 'x={policyKey:"PK1"}',
                 'https://edge.api.brightcove.com/': _brightcove()})
    assert live_providers.resolve('telemadrid://ref:Live_Telemadrid') == 'https://bc/live.m3u8'
    assert http.max_bytes >= 4 * 1024 * 1024


def test_telemadrid_returns_hls_and_caches_key(fake):
    http = fake({telemadrid.PLAYER_JS: 'x={policyKey:"PK1"}',
                 'https://edge.api.brightcove.com/': _brightcove()})
    assert live_providers.resolve('telemadrid://ref:Live_Telemadrid') == 'https://bc/live.m3u8'
    assert live_providers.resolve('telemadrid://ref:Live_LaOtra') == 'https://bc/live.m3u8'
    player_downloads = [c for c in http.calls if c[1] == telemadrid.PLAYER_JS]
    assert len(player_downloads) == 1
    assert http.calls[1][2]['Accept'] == 'application/json;pk=PK1'
    assert http.calls[1][1].endswith('/videos/ref%3ALive_Telemadrid')


def test_telemadrid_rereads_rotated_key_once(fake, monkeypatch):
    keys = iter(['x={policyKey:"OLD"}', 'x={policyKey:"NEW"}'])
    def api(url):
        accept = http.calls[-1][2]['Accept']
        if accept.endswith('OLD'):
            raise PermissionError('INVALID_POLICY_KEY')
        return _brightcove()
    http = fake({telemadrid.PLAYER_JS: lambda url: next(keys),
                 'https://edge.api.brightcove.com/': api})
    assert live_providers.resolve('telemadrid://ref:Live_Telemadrid') == 'https://bc/live.m3u8'
    assert telemadrid._policy_key == 'NEW'


def test_telemadrid_recording_is_not_taken_as_live(fake):
    fake({telemadrid.PLAYER_JS: 'x={policyKey:"PK"}',
          'https://edge.api.brightcove.com/': _brightcove(duration=3600000)})
    assert live_providers.resolve('telemadrid://ref:Live_Telemadrid') is None


# --- À Punt: one numeric video id that the broadcaster may replace -----------

STORED = '6137605659001'
MOVED = '6399000000112'
_KEY_SCRIPT = 'x={policyKey:"PK1"}'


def _video(ident):
    return apunt.API % ident


def _page(ident):
    """The player settings as the live page carried them on 2026-11-10:
    JSON inside an attribute, so every quote arrives as an HTML entity."""
    return ('<div data-mrf-video="{&quot;sources&quot;:[]},&quot;bcId&quot;:&quot;' + ident
            + '&quot;,&quot;bcPlayer&quot;:&quot;wM4NX8x9T&quot;,&quot;bcEmbed&quot;:&quot;default&quot;}"></div>')


def _requests(http):
    """Each request as a short label, in order: every count below is exact."""
    labels = {apunt.PLAYER_JS: 'key', apunt.LIVE_PAGE: 'page',
              _video(STORED): 'stored', _video(MOVED): 'moved'}
    return [labels.get(call[1], call[1]) for call in http.calls]


def test_apunt_returns_hls_caches_key_and_reads_the_whole_player_script(fake):
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): _brightcove(duration=0)})
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    # The key is read once and the stored id asked for directly, nothing else.
    assert _requests(http) == ['key', 'stored', 'stored']
    assert http.max_bytes >= 4 * 1024 * 1024
    assert http.calls[1][2]['Accept'] == 'application/json;pk=PK1'
    assert http.calls[1][2]['Referer'] == apunt.WEB
    assert http.calls[1][1].endswith('/videos/' + STORED)


@pytest.mark.parametrize('hls_type', [
    'application/vnd.apple.mpegurl',                     # what Brightcove answered on 2026-11-10
    'application/x-mpegURL', 'application/x-mpegurl', 'Application/VND.Apple.MpegURL',
])
def test_apunt_takes_either_hls_type_and_never_dash(fake, hls_type):
    fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): {'duration': 0, 'sources': [
        {'type': 'application/dash+xml', 'src': 'https://bc/live.mpd'},
        {'type': hls_type},
        {'type': hls_type, 'src': 'https://fastly.live.brightcove.com/x/master.m3u8'}]}})
    assert live_providers.resolve('apunt://' + STORED) == 'https://fastly.live.brightcove.com/x/master.m3u8'


@pytest.mark.parametrize('page', [
    '{"bcId":"%s"}', '{"bcId": %s}', '{&quot;bcId&quot;:&quot;%s&quot;}',
    # The structured data's player link, slashes escaped as JSON does.
    '"contentUrl":"https:\\/\\/players.brightcove.net\\/6057955885001\\/wM4NX8x9T_default\\/index.html?videoId=%s","thumbnailUrl":""',
    '<iframe src="https://players.brightcove.net/6057955885001/wM4NX8x9T_default/index.html?videoId=%s"></iframe>',
])
def test_apunt_reads_the_live_id_in_every_form_the_page_uses(fake, page):
    fake({apunt.LIVE_PAGE: page % MOVED})
    assert apunt._page_live_id() == MOVED


def test_apunt_ignores_another_players_video_on_the_live_page(fake):
    fake({apunt.LIVE_PAGE: '<iframe src="https://players.brightcove.net/1/other_default/index.html?videoId=%s">' % MOVED})
    assert apunt._page_live_id() is None


@pytest.mark.parametrize('answer', [
    {'duration': -1}, {'duration': 0}, {'duration': None}, {},
])
def test_apunt_live_durations_are_accepted(fake, answer):
    """-1 is a live stream, 0 a live stream with a rewind window."""
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): dict(_brightcove(), **answer)
                 if answer else {'sources': _brightcove()['sources']}})
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert _requests(http) == ['key', 'stored']


def test_apunt_without_policy_key_asks_for_nothing_else(fake):
    http = fake({apunt.PLAYER_JS: 'x={somethingElse:"1"}'})
    assert live_providers.resolve('apunt://' + STORED) is None
    assert _requests(http) == ['key']
    assert apunt._policy_key is None


def test_apunt_rereads_a_rejected_key_once_without_the_website(fake):
    """Recovering from a rotated key must not depend on the live page: it is
    not asked for at all when the new key works."""
    keys = iter(['x={policyKey:"OLD"}', 'x={policyKey:"NEW"}'])

    def api(url):
        if http.calls[-1][2]['Accept'].endswith('OLD'):
            raise PermissionError('INVALID_POLICY_KEY')
        return _brightcove(duration=0)
    http = fake({apunt.PLAYER_JS: lambda url: next(keys), _video(STORED): api,
                 apunt.LIVE_PAGE: TimeoutError('the website hangs')})
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert _requests(http) == ['key', 'stored', 'key', 'stored']
    assert apunt._policy_key == 'NEW'
    assert apunt._live_ids == {}


def test_apunt_rejected_key_with_no_new_key_stops(fake):
    keys = iter(['x={policyKey:"OLD"}', 'x={nothing:1}'])
    http = fake({apunt.PLAYER_JS: lambda url: next(keys),
                 _video(STORED): PermissionError('INVALID_POLICY_KEY')})
    assert live_providers.resolve('apunt://' + STORED) is None
    assert _requests(http) == ['key', 'stored', 'key']


def test_apunt_follows_a_replaced_video_id_and_remembers_it(fake):
    """The stored id answers with an error: after the key is ruled out, the
    live page names the id in use, and later opens go straight to it."""
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): LookupError('VIDEO_NOT_FOUND'),
                 apunt.LIVE_PAGE: _page(MOVED), _video(MOVED): _brightcove(duration=0)})
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert _requests(http) == ['key', 'stored', 'key', 'stored', 'page', 'moved']
    assert http.calls[4][2]['Referer'] == apunt.WEB
    assert apunt._live_ids == {STORED: MOVED}
    http.calls.clear()
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert _requests(http) == ['moved']


@pytest.mark.parametrize('unusable', [
    _brightcove(duration=3600000),                       # a recording left under the old id
    {'duration': 0, 'sources': []},                      # readable, but nothing to play
    {'duration': 0, 'sources': [{'type': 'application/dash+xml', 'src': 'https://bc/live.mpd'}]},
    {'duration': 0, 'sources': [{'type': 'application/x-mpegURL', 'src': ''}]},
    ['not', 'an', 'object'],
])
def test_apunt_looks_for_the_live_id_when_the_stored_one_answers_without_it(fake, unusable):
    """An HTTP 200 that is not the live stream is no reason to give up: the
    live page may embed another id. The key was accepted, so it is kept."""
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): unusable,
                 apunt.LIVE_PAGE: _page(MOVED), _video(MOVED): _brightcove(duration=0)})
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert _requests(http) == ['key', 'stored', 'page', 'moved']
    assert apunt._live_ids == {STORED: MOVED}


def test_apunt_recording_is_never_served_even_under_the_new_id(fake):
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): _brightcove(duration=3600000),
                 apunt.LIVE_PAGE: _page(MOVED), _video(MOVED): _brightcove(duration=1800000)})
    assert live_providers.resolve('apunt://' + STORED) is None
    assert _requests(http) == ['key', 'stored', 'page', 'moved']
    assert apunt._live_ids == {}


def test_apunt_page_naming_the_same_id_is_not_asked_again(fake):
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): _brightcove(duration=3600000),
                 apunt.LIVE_PAGE: _page(STORED)})
    assert live_providers.resolve('apunt://' + STORED) is None
    assert _requests(http) == ['key', 'stored', 'page']


@pytest.mark.parametrize('page', [
    ConnectionError('the website is down'),
    TimeoutError('the website hangs'),
    '<html>no player here</html>',
    '{"bcId":"abc"}',
    '{"bcId":"12345"}',                                  # too short for a video id
    '{"bcId":"' + '9' * 21 + '"}',                       # too long for one
    '{"bcId":null}',
    '',
])
def test_apunt_unreadable_live_page_is_a_clean_failure(fake, page):
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): {'duration': 0, 'sources': []},
                 apunt.LIVE_PAGE: page})
    assert live_providers.resolve('apunt://' + STORED) is None
    assert _requests(http) == ['key', 'stored', 'page']
    assert apunt._live_ids == {}


def test_apunt_gives_up_after_the_new_id_is_refused_too(fake):
    """The longest path there is: six requests, then a clean failure from the
    public resolver even though the last request raised."""
    http = fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): LookupError('VIDEO_NOT_FOUND'),
                 apunt.LIVE_PAGE: _page(MOVED), _video(MOVED): ConnectionError('down')})
    assert live_providers.resolve('apunt://' + STORED) is None
    assert _requests(http) == ['key', 'stored', 'key', 'stored', 'page', 'moved']
    assert apunt._live_ids == {}
    with pytest.raises(ConnectionError):
        apunt.resolve(STORED)


def test_apunt_forgets_a_remembered_id_that_stops_serving_the_live(fake, monkeypatch):
    monkeypatch.setattr(apunt, '_live_ids', {STORED: MOVED})
    monkeypatch.setattr(apunt, '_policy_key', 'PK1')
    http = fake({_video(MOVED): _brightcove(duration=3600000),
                 apunt.LIVE_PAGE: _page(STORED), _video(STORED): _brightcove(duration=0)})
    assert live_providers.resolve('apunt://' + STORED) == 'https://bc/live.m3u8'
    assert _requests(http) == ['moved', 'page', 'stored']
    assert apunt._live_ids == {STORED: STORED}


def test_apunt_live_page_cannot_use_up_the_resolution_budget(fake, monkeypatch):
    """The page gets a short deadline of its own, and the request after it
    sees the caller's deadline again. Without this a slow website took the
    whole 15 s and the last request was never made."""
    import time
    clock = [5000.0]
    monkeypatch.setattr(apunt.time, 'monotonic', lambda: clock[0])
    caller_deadline = clock[0] + 15
    seen = {}

    def page(url):
        seen['page'] = base.resolution_limits.get()
        return _page(MOVED)

    def moved(url):
        seen['moved'] = base.resolution_limits.get()
        return _brightcove(duration=0)
    fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): {'duration': 0, 'sources': []},
          apunt.LIVE_PAGE: page, _video(MOVED): moved})
    cancelled = object()
    token = base.resolution_limits.set((caller_deadline, cancelled))
    try:
        assert apunt.resolve(STORED) == 'https://bc/live.m3u8'
    finally:
        base.resolution_limits.reset(token)
    assert seen['page'] == (clock[0] + apunt.LIVE_PAGE_SECONDS, cancelled)
    assert seen['moved'] == (caller_deadline, cancelled)
    assert apunt.LIVE_PAGE_SECONDS < 15


def test_apunt_live_page_never_outlives_a_nearer_caller_deadline(fake, monkeypatch):
    clock = [5000.0]
    monkeypatch.setattr(apunt.time, 'monotonic', lambda: clock[0])
    seen = {}

    def page(url):
        seen['page'] = base.resolution_limits.get()
        raise TimeoutError('Provider resolution deadline exceeded')
    fake({apunt.PLAYER_JS: _KEY_SCRIPT, _video(STORED): {'duration': 0, 'sources': []},
          apunt.LIVE_PAGE: page})
    token = base.resolution_limits.set((clock[0] + 1.5, None))
    try:
        assert apunt.resolve(STORED) is None
        assert base.resolution_limits.get() == (clock[0] + 1.5, None)
    finally:
        base.resolution_limits.reset(token)
    assert seen['page'] == (clock[0] + 1.5, None)


def test_apunt_website_is_imported_without_being_downloaded(fake, monkeypatch):
    import asyncio
    from app.models.url_types import RegularURL
    from app.scrapers.http import HTTPScraper

    async def no_fetch(self, url):
        raise AssertionError('the website itself must not be fetched')
    monkeypatch.setattr(HTTPScraper, 'fetch_content', no_fetch)

    async def no_status(self, url, status, error=None):
        return None
    monkeypatch.setattr(HTTPScraper, 'update_url_status', no_status)
    http = fake({})
    channels, status = asyncio.run(HTTPScraper(RegularURL('https://www.apuntmedia.es/')).scrape())
    assert status == 'OK'
    assert {(name, meta['stream_url']) for _id, name, meta in channels} == {('À Punt', 'apunt://' + STORED)}
    assert http.calls == []


def test_hung_broadcaster_does_not_keep_kodi_waiting(lan, client, db_session, monkeypatch):
    """Kodi waits on this GET in its interface thread. With a hung
    broadcaster the remote went dead for 20 s; past the budget it must get
    the 502 it handles cleanly."""
    import time as clock
    from app.api.endpoints import live
    stream = _stream('mediaset://T5')
    db_session.add(stream)
    db_session.commit()
    monkeypatch.setattr(live, '_recent', {})
    monkeypatch.setattr(live, 'OPEN_BUDGET_SECONDS', 0.3)
    monkeypatch.setattr(live_providers, 'resolve', lambda url: clock.sleep(2) or 'https://late/x.m3u8')
    started = clock.monotonic()
    response = client.get(f'/live/{stream.id}', follow_redirects=False)
    assert response.status_code == 502
    assert clock.monotonic() - started < 1.5


def test_live_links_carry_mimetype_and_direct_links_do_not(client, db_session):
    """Without it IPTV Simple opens the link in Kodi's interface thread to
    learn its type: 16 s of dead remote against a hung broadcaster, even
    with the budget. With it, 0 s (measured on a test machine, fake provider)."""
    db_session.add_all([_stream('mediaset://T5'), _stream('https://cdn.example.com/directo.m3u8')])
    db_session.commit()
    lines = client.get('/playlist.m3u?only_online=false').text.splitlines()
    live = [i for i, line in enumerate(lines) if '/live/' in line and not line.startswith('#')]
    direct = lines.index('https://cdn.example.com/directo.m3u8')
    assert len(live) == 1
    assert lines[live[0] - 1] == '#KODIPROP:mimetype=application/vnd.apple.mpegurl'
    # A direct link may be MPEG-TS or anything else: no type is guessed for it.
    assert not lines[direct - 1].startswith('#KODIPROP')


@pytest.mark.parametrize('path', ['/api/v1/playlists/tv-channels/m3u', '/api/v1/playlists/all-streams/m3u'])
def test_mimetype_also_in_other_playlists(client, db_session, path):
    from app.models.models import TVChannel
    tv = TVChannel(name='Telecinco', is_active=True)
    db_session.add(tv)
    db_session.flush()
    stream = _stream('mediaset://T5')
    stream.tv_channel_id = tv.id
    db_session.add_all([stream, _stream('telemadrid://ref:Live_LaOtra')])
    db_session.commit()
    lines = client.get(path).text.splitlines()
    live = [i for i, line in enumerate(lines) if '/live/' in line and not line.startswith('#')]
    assert live
    assert all(lines[i - 1] == '#KODIPROP:mimetype=application/vnd.apple.mpegurl' for i in live)

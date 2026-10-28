"""Free ad-supported channels (Pluto TV, Plex, Samsung TV Plus) for Spain.

Same shape as the broadcasters in test_live_providers: imported from a
website-style source URL, stored as `<scheme>://<channel id>`, resolved when
opened. No network: `base.http` is a fake that fails on any URL it was not given.
"""
import asyncio
import gzip
import json

import pytest

from app.services import live_providers
from app.services.live_providers import base, plex, pluto, samsung
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

    def get_location(self, url, headers=None):
        return self._answer('GET', url, headers)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(base, 'now', clock)
    return clock


@pytest.fixture
def fake(monkeypatch, clock):
    def install(answers):
        http = FakeHttp(answers)
        monkeypatch.setattr(base, 'http', http)
        return http
    for module in live_providers.PROVIDERS:
        getattr(module, 'forget', lambda: None)()
    yield install
    for module in live_providers.PROVIDERS:
        getattr(module, 'forget', lambda: None)()


def _imported(provider):
    return {name: meta for _id, name, meta in
            M3UService().extract_channels_from_content(live_providers.playlist(provider))}


# --- which source and which stream belongs to whom --------------------------

@pytest.mark.parametrize('url, provider', [
    ('https://pluto.tv/es/live-tv', pluto),
    ('https://watch.plex.tv/es/live-tv', plex),
    ('https://www.samsungtvplus.com/', samsung),
])
def test_website_is_recognised(url, provider):
    assert live_providers.for_source_url(url) is provider


def test_scheme_selects_resolver():
    assert live_providers.for_stream_url('pluto://abcdef0123456789abcdef01') is pluto
    assert live_providers.for_stream_url('plex://a-b') is plex
    assert live_providers.for_stream_url('samsung://ESXX0000003CC') is samsung


# --- Pluto TV ---------------------------------------------------------------

PLUTO_ID = 'abcdef01aaaaaaaaaaaaaaaa'
BOOT = {'sessionToken': 'jwt.one', 'session': {'countryCode': 'ES'},
        'servers': {'channels': 'https://service-channels.example'}}


def _pluto_channel(ident, name, **extra):
    channel = {'id': ident, 'name': name, 'isStitched': True, 'plutoOfficeOnly': False,
               'images': [{'type': 'solidLogoPNG', 'url': f'https://img/{ident}/solid.png'},
                          {'type': 'colorLogoPNG', 'url': f'https://img/{ident}/color.png'}]}
    channel.update(extra)
    return channel


def _pluto(boot=BOOT, channels=None):
    return {pluto.BOOT: boot,
            'https://service-channels.example/v2/guide/channels': {'data': channels or []}}


def test_pluto_imports_spains_live_list(fake):
    http = fake(_pluto(channels=[
        _pluto_channel(PLUTO_ID, 'Misterio & Ejemplo'),
        _pluto_channel('aaaaaaaaaaaaaaaaaaaaaaa1', 'Oficina', plutoOfficeOnly=True),
        _pluto_channel('aaaaaaaaaaaaaaaaaaaaaaa2', 'Sin stitcher', isStitched=False),
    ]))
    streams = _imported(pluto)
    assert set(streams) == {'Misterio & Ejemplo'}
    channel = streams['Misterio & Ejemplo']
    assert channel['stream_url'] == f'pluto://{PLUTO_ID}'
    assert channel['tvg_logo'] == f'https://img/{PLUTO_ID}/color.png'
    assert channel['group_title'] == 'Pluto TV'
    # No guide we use carries Pluto's ids.
    assert 'tvg_id' not in channel
    # The list is asked with the session's token.
    assert http.calls[1][2]['Authorization'] == 'Bearer jwt.one'


def test_pluto_outside_spain_imports_nothing(fake):
    """The list is the region of the address that asks: another country's
    list would fill the grid with channels that do not play here."""
    http = fake(_pluto(boot=dict(BOOT, session={'countryCode': 'US'}),
                       channels=[_pluto_channel(PLUTO_ID, 'X')]))
    assert pluto.channels() == []
    assert len(http.calls) == 1


def test_pluto_plays_with_a_browser_user_agent(fake):
    """Measured 28-10: Pluto's CloudFront answers 403 to Kodi's User-Agent."""
    fake(_pluto(channels=[_pluto_channel(PLUTO_ID, 'Misterio & Ejemplo')]))
    meta = _imported(pluto)['Misterio & Ejemplo']
    assert meta['stream_headers'] == {'User-Agent': base.USER_AGENT}
    assert not meta['stream_headers']['User-Agent'].startswith('Kodi')
    link = PlaylistService._stream_link('x', 'url:x', stream_url=meta['stream_url'],
                                        stream_headers=meta['stream_headers'],
                                        live_base_url='http://192.168.1.5:8000')
    # Percent-encoded whole: Kodi cuts a header value at its first space.
    assert link.endswith('|User-Agent=Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%29'
                         '%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29'
                         '%20Chrome%2F140.0%20Safari%2F537.36')


def test_pluto_resolves_to_v2_with_shared_session(fake, clock):
    """The old /stitch/ path serves a takedown slate for every channel; /v2/
    with the boot JWT and masterJWTPassthrough serves the channel."""
    http = fake(_pluto())
    first = live_providers.resolve(f'pluto://{PLUTO_ID}')
    assert first == (f'https://stitcher.pluto.tv/v2/stitch/hls/channel/{PLUTO_ID}/master.m3u8'
                     '?jwt=jwt.one&masterJWTPassthrough=true')
    clock.now += 60
    live_providers.resolve('pluto://bbbbbbbbbbbbbbbbbbbbbbbb')
    assert len(http.calls) == 1, 'one JWT serves every channel'
    clock.now += pluto.SESSION_SECONDS
    http.answers[pluto.BOOT] = dict(BOOT, sessionToken='jwt.two')
    assert 'jwt=jwt.two' in live_providers.resolve(f'pluto://{PLUTO_ID}')
    assert len(http.calls) == 2


def test_pluto_boot_has_the_fields_it_requires(fake):
    http = fake(_pluto())
    live_providers.resolve(f'pluto://{PLUTO_ID}')
    url = http.calls[0][1]
    for name in ('appName=', 'appVersion=', 'deviceVersion=', 'deviceModel=', 'deviceMake=',
                 'deviceType=', 'clientID=', 'clientModelNumber='):
        assert name in url


def test_pluto_rejects_a_made_up_id(fake):
    http = fake({})
    assert live_providers.resolve('pluto://../../x') is None
    assert http.calls == []


# --- Plex -------------------------------------------------------------------

PLEX_ID = 'cccccccccccccccccccccccc-dddddddddddddddddddddddd'


def _plex_list(token='tok-1'):
    return {'headers': {'user-agent': 'Mozilla/5.0', 'X-Plex-Token': token},
            'regions': {'es': {'name': 'Spain'}},
            'channels': {
                PLEX_ID: {'name': 'Serie Ejemplo', 'logo': 'https://plex/logo.png', 'regions': ['es']},
                'cccccccccccccccccccccccc-aaaaaaaaaaaaaaaaaaaaaaaa': {'name': 'Solo EE. UU.', 'regions': ['us']},
            }}


def test_plex_imports_spanish_channels(fake):
    fake({plex.LIST: _plex_list()})
    streams = _imported(plex)
    assert set(streams) == {'Serie Ejemplo'}
    assert streams['Serie Ejemplo']['stream_url'] == f'plex://{PLEX_ID}'
    assert streams['Serie Ejemplo']['tvg_logo'] == 'https://plex/logo.png'
    assert streams['Serie Ejemplo']['group_title'] == 'Plex'


def test_plex_resolves_without_the_redirector(fake):
    """jmp2.uk only adds the list's shared token to Plex's own URL, and
    answers 429 after ~35 requests: the link is built here instead."""
    http = fake({plex.LIST: _plex_list()})
    plex.channels()
    link = live_providers.resolve(f'plex://{PLEX_ID}')
    assert link == f'https://epg.provider.plex.tv/library/parts/{PLEX_ID}.m3u8?X-Plex-Token=tok-1'
    assert len(http.calls) == 1, 'the token from the import is reused'


def test_plex_reads_the_token_once_after_a_restart(fake, clock):
    http = fake({plex.LIST: _plex_list()})
    assert live_providers.resolve(f'plex://{PLEX_ID}').endswith('tok-1')
    assert live_providers.resolve(f'plex://{PLEX_ID}').endswith('tok-1')
    assert len(http.calls) == 1
    clock.now += plex.TOKEN_SECONDS + 1
    http.answers[plex.LIST] = _plex_list('tok-2')
    assert live_providers.resolve(f'plex://{PLEX_ID}').endswith('tok-2')


def test_plex_rejects_a_made_up_id(fake):
    http = fake({})
    assert live_providers.resolve('plex://x?y=1') is None
    assert http.calls == []


# --- Samsung TV Plus --------------------------------------------------------

def _samsung_list():
    return {'slug': 'stvp-{id}', 'regions': {'es': {'channels': {
        'ESXX0000001AA': {'name': 'Cine Ejemplo', 'logo': 'https://s/ce.png', 'group': 'Cine'},
        'ESXX0000002BB': {'name': 'Canal Uno', 'license_url': 'https://widevine/x'},
    }}}}


def test_samsung_leaves_out_drm_channels(fake):
    """13 of 189 carry a Widevine licence: Kodi cannot play them here."""
    fake({samsung.LIST: _samsung_list()})
    streams = _imported(samsung)
    assert set(streams) == {'Cine Ejemplo'}
    assert streams['Cine Ejemplo']['stream_url'] == 'samsung://ESXX0000001AA'
    assert streams['Cine Ejemplo']['tvg_logo'] == 'https://s/ce.png'
    assert streams['Cine Ejemplo']['group_title'] == 'Samsung TV Plus'


def test_samsung_keeps_the_redirectors_answer(fake, clock):
    http = fake({'https://jmp2.uk/stvp-ESXX0000001AA': 'https://cdn/cine-ejemplo.m3u8'})
    assert live_providers.resolve('samsung://ESXX0000001AA') == 'https://cdn/cine-ejemplo.m3u8'
    clock.now += 3600
    assert live_providers.resolve('samsung://ESXX0000001AA') == 'https://cdn/cine-ejemplo.m3u8'
    assert len(http.calls) == 1


def test_samsung_caps_redirector_requests(fake, clock):
    """The redirector answered 429 after ~35 requests in 25 minutes."""
    http = fake({'https://jmp2.uk/stvp-': lambda url: 'https://cdn/' + url.rsplit('-', 1)[1]})
    for n in range(samsung.REDIRECTS_PER_HOUR):
        assert live_providers.resolve(f'samsung://ES{n:08d}') == f'https://cdn/ES{n:08d}'
    assert live_providers.resolve('samsung://ES99999999') is None
    assert len(http.calls) == samsung.REDIRECTS_PER_HOUR
    clock.now += 3601
    assert live_providers.resolve('samsung://ES99999999') == 'https://cdn/ES99999999'


def test_samsung_waits_after_429_and_keeps_old_links(fake, clock):
    http = fake({'https://jmp2.uk/stvp-ES00000001': 'https://cdn/one.m3u8',
                 'https://jmp2.uk/stvp-': ValueError('HTTP 429')})
    assert live_providers.resolve('samsung://ES00000001') == 'https://cdn/one.m3u8'
    clock.now += samsung.LINK_SECONDS + 1
    assert live_providers.resolve('samsung://ES00000002') is None
    asked = len(http.calls)
    # Expired, but the redirector is resting: the old link beats no link.
    assert live_providers.resolve('samsung://ES00000001') == 'https://cdn/one.m3u8'
    assert live_providers.resolve('samsung://ES00000002') is None
    assert len(http.calls) == asked
    clock.now += samsung.PAUSE_AFTER_REFUSAL
    del http.answers['https://jmp2.uk/stvp-']
    http.answers['https://jmp2.uk/stvp-ES00000002'] = 'https://cdn/two.m3u8'
    assert live_providers.resolve('samsung://ES00000002') == 'https://cdn/two.m3u8'


def test_samsung_status_checks_never_ask_the_redirector(fake):
    """A status sweep over 176 channels would spend the redirector's quota
    in minutes: checks only use links already resolved for playback."""
    http = fake({'https://jmp2.uk/stvp-ES00000001': 'https://cdn/one.m3u8'})
    assert asyncio.run(live_providers.resolve_async('samsung://ES00000001', checking=True)) is None
    assert http.calls == []
    assert asyncio.run(live_providers.resolve_async('samsung://ES00000001')) == 'https://cdn/one.m3u8'
    assert asyncio.run(live_providers.resolve_async('samsung://ES00000001', checking=True)) == 'https://cdn/one.m3u8'
    assert len(http.calls) == 1


def test_samsung_rejects_a_made_up_id(fake):
    http = fake({})
    assert live_providers.resolve('samsung://../x') is None
    assert http.calls == []



# --- the shared HTTP client -------------------------------------------------

def _source(monkeypatch, responses):
    from app.utils.bounded_source import SourceResponse
    asked = []

    async def source_request(url, **kwargs):
        asked.append(url)
        status, body, headers = responses[len(asked) - 1]
        return SourceResponse(status, body, headers)
    monkeypatch.setattr(base, 'source_request', source_request)
    return asked


def test_http_reads_a_gzip_json_file(monkeypatch):
    """i.mjh.nz publishes `.channels.json.gz` as a gzip file, not as a
    gzip-encoded response."""
    _source(monkeypatch, [(200, gzip.compress(json.dumps({'a': 1}).encode()), {})])
    assert base.Http().get_json('https://i.mjh.nz/x/.channels.json.gz') == {'a': 1}


def test_http_location_is_not_followed(monkeypatch):
    asked = _source(monkeypatch, [(302, b'', {'Location': 'https://cdn/x.m3u8'})])
    assert base.Http().get_location('https://jmp2.uk/stvp-X') == 'https://cdn/x.m3u8'
    assert asked == ['https://jmp2.uk/stvp-X']


def test_http_location_refusal_raises(monkeypatch):
    _source(monkeypatch, [(429, b'', {})])
    with pytest.raises(ValueError, match='429'):
        base.Http().get_location('https://jmp2.uk/stvp-X')

def test_stream_check_resolves_as_a_check(monkeypatch):
    from app.services import http_stream_check
    seen = []

    def resolve(stream_url):
        seen.append(base.checking.get())
        return None
    monkeypatch.setattr(live_providers, 'resolve', resolve)
    online, _error = asyncio.run(http_stream_check.check('mediaset://T5'))
    assert online is None
    assert seen == [True]

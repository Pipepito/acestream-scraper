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
from app.services.live_providers import base
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

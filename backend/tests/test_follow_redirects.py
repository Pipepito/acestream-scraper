"""follow_redirects / source_get_following: the one redirect walk for source reads."""
import pytest

from app.utils.bounded_source import SourceResponse, source_get_following
from app.utils.outbound_http import follow_redirects
from app.utils.url_guard import BlockedURLError


class _Response:
    def __init__(self, status, location=None):
        self.status = status
        self.headers = {'Location': location} if location else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _Session:
    def __init__(self, answers):
        self.answers = dict(answers)
        self.calls = []

    def get(self, url, *, headers, allow_redirects, **kwargs):
        assert allow_redirects is False
        self.calls.append((url, dict(headers)))
        return self.answers[url]


@pytest.mark.asyncio
async def test_follows_relative_redirects_and_checks_every_hop():
    session = _Session({'https://a.example/list': _Response(302, '/moved'),
                        'https://a.example/moved': _Response(200)})
    checked = []
    async with follow_redirects(session, 'https://a.example/list', check=checked.append) as (url, response):
        assert (url, response.status) == ('https://a.example/moved', 200)
    assert checked == ['https://a.example/list', 'https://a.example/moved']


@pytest.mark.asyncio
async def test_credentials_stay_on_their_origin():
    session = _Session({'https://a.example/x': _Response(301, 'https://b.example/y'),
                        'https://b.example/y': _Response(200)})
    headers = {'Authorization': 'Bearer t', 'Cookie': 'c=1', 'Referer': 'https://a.example/'}
    async with follow_redirects(session, 'https://a.example/x', headers=headers):
        pass
    assert session.calls[1][1] == {'Referer': 'https://a.example/'}


@pytest.mark.asyncio
async def test_missing_location_and_too_many_hops_are_refused():
    session = _Session({'https://a.example/x': _Response(302)})
    with pytest.raises(ValueError, match='no destination'):
        async with follow_redirects(session, 'https://a.example/x'):
            pass
    loop = _Session({'https://a.example/x': _Response(302, '/x')})
    with pytest.raises(BlockedURLError):
        async with follow_redirects(loop, 'https://a.example/x', max_redirects=2, too_many=BlockedURLError):
            pass
    assert len(loop.calls) == 3


@pytest.mark.asyncio
async def test_source_get_following_shares_one_budget():
    budgets = []

    async def get(url, *, timeout, **kwargs):
        budgets.append(timeout)
        if url.endswith('/a'):
            return SourceResponse(302, b'', {'Location': '/b'})
        return SourceResponse(200, b'ok', {})

    url, response = await source_get_following('https://a.example/a', budget=10, get=get)
    assert (url, response.content) == ('https://a.example/b', b'ok')
    assert budgets[0] <= 10 and budgets[1] <= budgets[0]

import ssl
from types import SimpleNamespace

import pytest

from app.models.url_types import RegularURL
from app.scrapers import http as http_scraper_module
from app.scrapers.http import HTTPScraper


@pytest.mark.asyncio
async def test_http_scraper_uses_certifi_ssl_context(monkeypatch):
    url = RegularURL(url="https://example.com/test.m3u")
    scraper = HTTPScraper(url)

    expected_context = ssl.create_default_context()
    session_kwargs = {}

    class MockResponse:
        status = 200
        headers = {}

        async def text(self):
            return "#EXTM3U\n#EXTINF:-1,Example\nacestream://abc\n"

        def raise_for_status(self):
            return None

    class MockResponseContext:
        async def __aenter__(self):
            return MockResponse()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponseContext()

    class MockSessionContext:
        async def __aenter__(self):
            return MockSession()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def fake_create_default_context(*, cafile=None, capath=None, cadata=None):
        session_kwargs["cafile"] = cafile
        return expected_context

    def fake_client_session(*args, **kwargs):
        session_kwargs.update(kwargs)
        return MockSessionContext()

    monkeypatch.setattr(http_scraper_module, "ssl", SimpleNamespace(create_default_context=fake_create_default_context), raising=False)
    monkeypatch.setattr(http_scraper_module, "certifi", SimpleNamespace(where=lambda: "/tmp/certifi.pem"), raising=False)
    monkeypatch.setattr(http_scraper_module.aiohttp, "ClientSession", fake_client_session)

    content = await scraper.fetch_content("https://example.com/test.m3u")

    assert content.startswith("#EXTM3U")
    assert session_kwargs["connector"]._ssl is expected_context
    assert session_kwargs["cafile"] == "/tmp/certifi.pem"

import ssl
from types import SimpleNamespace

import aiohttp
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

    # URL-policy behavior is covered separately. Keep this SSL wiring test fully
    # offline so it is deterministic in network-isolated CI.
    monkeypatch.setattr(http_scraper_module, "validate_outbound_url", lambda _url: None)
    monkeypatch.setattr(http_scraper_module, "ssl", SimpleNamespace(create_default_context=fake_create_default_context), raising=False)
    monkeypatch.setattr(http_scraper_module, "certifi", SimpleNamespace(where=lambda: "/tmp/certifi.pem"), raising=False)
    monkeypatch.setattr(aiohttp, "ClientSession", fake_client_session)

    content = await scraper.fetch_content("https://example.com/test.m3u")

    assert content.startswith("#EXTM3U")
    assert session_kwargs["connector"]._ssl is expected_context
    assert session_kwargs["cafile"] == "/tmp/certifi.pem"


@pytest.mark.asyncio
async def test_playlist_with_byte_order_mark_is_not_reported_as_invalid(monkeypatch, caplog):
    playlist = "\ufeff#EXTM3U\n#EXTINF:-1,Web\nhttp://example.com/web/index.m3u8\n"

    class MockResponse:
        status = 200
        headers = {}

        async def text(self):
            return playlist

        def raise_for_status(self):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    class MockSession:
        def get(self, *args, **kwargs):
            return MockResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(http_scraper_module, "validate_outbound_url", lambda _url: None)
    monkeypatch.setattr(http_scraper_module, "source_session", lambda **kwargs: MockSession())
    scraper = HTTPScraper(RegularURL(url="https://example.com/test.m3u"))

    with caplog.at_level("WARNING", logger="app.scrapers.http"):
        assert await scraper.fetch_content("https://example.com/test.m3u") == playlist
    assert "doesn't appear to be a valid M3U file" not in caplog.text

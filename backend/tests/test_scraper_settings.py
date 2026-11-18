"""The source timeout/retry settings shown under Advanced reach the scrapers."""
import pytest

from app import scrapers
from app.scrapers import create_scraper_for_url


@pytest.mark.asyncio
async def test_regular_and_zeronet_scrapers_use_their_settings(monkeypatch):
    # The ZeroNet scraper builds an aiohttp cookie jar, which needs a running loop.
    monkeypatch.setattr(scrapers.settings, 'SCRAPER_TIMEOUT', 42)
    monkeypatch.setattr(scrapers.settings, 'SCRAPER_RETRIES', 7)
    monkeypatch.setattr(scrapers.settings, 'ZERONET_TIMEOUT', 99)
    monkeypatch.setattr(scrapers.settings, 'ZERONET_RETRIES', 1)
    regular = create_scraper_for_url('https://lists.example/channels.m3u', 'regular')
    zeronet = create_scraper_for_url('zero://example.bit/lists/sports', 'zeronet')
    assert (regular.timeout, regular.retries) == (42, 7)
    assert (zeronet.timeout, zeronet.retries) == (99, 1)


def test_explicit_values_still_win(monkeypatch):
    monkeypatch.setattr(scrapers.settings, 'SCRAPER_TIMEOUT', 42)
    scraper = create_scraper_for_url('https://lists.example/channels.m3u', 'regular', timeout=5, retries=2)
    assert (scraper.timeout, scraper.retries) == (5, 2)

"""The M3U header must tell players where the guide is (issue #204).

Without `url-tvg` a player has nowhere to fetch the XMLTV from, so the EPG
never appears however well the `tvg-id` values match. The URL is resolved the
same way as every other externally visible URL in the app (spec 4.3), so a
configured public base URL and a reverse proxy both come out right.
"""
import pytest
from fastapi import status

from app.config.settings import get_settings

M3U_ROUTES = (
    "/api/v1/playlists/m3u",
    "/api/v1/playlists/playlists/m3u",
    "/api/v1/playlists/tv-channels/m3u",
    "/api/v1/playlists/all-streams/m3u",
    # The v1 URLs are the ones already configured in people's players.
    "/api/playlists/m3u",
    "/api/playlists/tv-channels/m3u",
    "/api/playlists/all-streams/m3u",
    "/playlists/m3u",
    "/playlist.m3u",
)


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize("route", M3U_ROUTES)
def test_header_advertises_the_guide(alembic_client, clean_env, route):
    response = alembic_client.get(route)
    assert response.status_code == status.HTTP_200_OK
    header = response.text.splitlines()[0]
    assert header == '#EXTM3U url-tvg="http://testserver/api/v1/epg/xml"', route


def test_the_advertised_guide_is_a_route_that_answers(alembic_client, clean_env):
    """A url-tvg pointing at a 404 would be worse than none at all."""
    header = alembic_client.get("/api/v1/playlists/m3u").text.splitlines()[0]
    url = header.split('url-tvg="', 1)[1].rstrip('"')
    path = url[len("http://testserver"):]
    guide = alembic_client.get(path)
    assert guide.status_code == status.HTTP_200_OK
    assert guide.text.lstrip().startswith("<?xml")


def test_the_configured_public_url_wins(alembic_client, clean_env):
    """Behind a proxy the player never sees the host the app is bound to."""
    put = alembic_client.put(
        "/api/v1/config/public_base_url",
        json={"value": "https://scraper.example.com/"},
    )
    assert put.status_code == status.HTTP_200_OK
    header = alembic_client.get("/api/v1/playlists/m3u").text.splitlines()[0]
    assert header == '#EXTM3U url-tvg="https://scraper.example.com/api/v1/epg/xml"'


def test_the_entries_are_untouched(client, clean_env, seed_channels):
    """Only the header changes: an entry is still #EXTINF plus its URL."""
    lines = client.get("/api/v1/playlists/m3u").text.splitlines()
    assert lines[0].startswith("#EXTM3U ")
    assert any(line.startswith("#EXTINF:") for line in lines[1:])
    assert not any(line.startswith("#EXTM3U") for line in lines[1:])

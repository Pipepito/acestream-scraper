"""
Contract tests for the legacy/public playlist routes served outside /api/v1.

/playlist.m3u is the URL v1 users have configured in their IPTV players; it
must keep serving a real M3U (not the SPA fallback) after the v2 cutover.
"""

from fastapi import status


class TestLegacyPlaylistRoute:
    """Test the legacy /playlist.m3u route."""

    def test_playlist_m3u_returns_m3u_not_spa(self, client, seed_channels):
        """The legacy URL must serve M3U content, never the SPA index.html."""
        response = client.get("/playlist.m3u")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        content = response.text
        assert content.startswith("#EXTM3U")
        assert "<html" not in content.lower()

    def test_playlist_m3u_matches_public_route(self, client, seed_channels):
        """The legacy URL must return the same playlist as /playlists/m3u."""
        legacy = client.get("/playlist.m3u")
        public = client.get("/playlists/m3u")
        assert legacy.status_code == status.HTTP_200_OK
        assert public.status_code == status.HTTP_200_OK
        assert legacy.text == public.text

    def test_playlist_m3u_download_headers(self, client, seed_channels):
        """The legacy URL must offer the playlist as an .m3u download."""
        response = client.get("/playlist.m3u")
        assert "attachment" in response.headers["content-disposition"]
        assert ".m3u" in response.headers["content-disposition"]

    def test_playlist_m3u_honors_search_param(self, client, seed_channels):
        """The v1 search query param must keep filtering the playlist."""
        response = client.get("/playlist.m3u?search=Alpha")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "Alpha Channel" in content
        assert "Beta Channel" not in content
        assert "Gamma Channel" not in content

    def test_playlist_m3u_honors_base_url_param(self, client, seed_channels):
        """The v1 base_url query param must keep rewriting stream URLs."""
        custom_base = "http://custom.example.com"
        response = client.get(f"/playlist.m3u?base_url={custom_base}")
        assert response.status_code == status.HTTP_200_OK
        assert custom_base in response.text

    def test_playlist_m3u_ignores_unknown_legacy_params(self, client, seed_channels):
        """Old clients may still send refresh=true; it must not error."""
        response = client.get("/playlist.m3u?refresh=true")
        assert response.status_code == status.HTTP_200_OK
        assert response.text.startswith("#EXTM3U")


class TestPublicPlaylistRoute:
    """Test the public /playlists/m3u route (no /api prefix)."""

    def test_playlists_m3u_returns_m3u(self, client, seed_channels):
        response = client.get("/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert response.text.startswith("#EXTM3U")

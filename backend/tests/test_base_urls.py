"""
Tests for named stream base URLs (#62): CRUD, default resolution, and
mask-based link rendering.
"""

from app.services.playlist_service import PlaylistService

CID = "a" * 40


class TestStreamLinkRendering:
    def test_plain_prefix_behaves_like_legacy(self):
        assert PlaylistService._stream_link("acestream://", CID) == f"acestream://{CID}"

    def test_prefix_with_pid_appends_ampersand(self):
        link = PlaylistService._stream_link("http://h:6878/ace/getstream?id=", CID, pid=3)
        assert link == f"http://h:6878/ace/getstream?id={CID}&pid=3"

    def test_mask_substitution(self):
        link = PlaylistService._stream_link(
            "http://h:8080/ace/stream?id={channel_id}&pid={pid}", CID, pid=7
        )
        assert link == f"http://h:8080/ace/stream?id={CID}&pid=7"

    def test_mask_without_pid_strips_dangling_parameter(self):
        link = PlaylistService._stream_link(
            "http://h:8080/ace/stream?id={channel_id}&pid={pid}", CID
        )
        assert link == f"http://h:8080/ace/stream?id={CID}"

    def test_mask_with_pid_as_first_query_param(self):
        pattern = "http://h/ace/stream?pid={pid}&id={channel_id}"
        # pid filled: straightforward substitution
        assert PlaylistService._stream_link(pattern, CID, pid=4) == (
            f"http://h/ace/stream?pid=4&id={CID}"
        )
        # pid disabled: the parameter is removed and the next one is
        # promoted to '?' so the URL stays valid
        assert PlaylistService._stream_link(pattern, CID) == (
            f"http://h/ace/stream?id={CID}"
        )

    def test_pid_without_channel_id_never_leaks_the_placeholder(self):
        # Can't be persisted (schema validation) but can arrive via an
        # explicit ?base_url= string.
        with_pid = PlaylistService._stream_link("http://h/play?pid={pid}", CID, pid=5)
        without_pid = PlaylistService._stream_link("http://h/play?pid={pid}", CID)
        assert "{pid}" not in with_pid
        assert "{pid}" not in without_pid
        assert CID in with_pid
        assert CID in without_pid


class TestBaseUrlCrud:
    def test_create_list_and_conflict(self, client):
        response = client.post(
            "/api/v1/base-urls",
            json={"name": "Engine LAN", "pattern": "http://nas:6878/ace/getstream?id={channel_id}"},
        )
        assert response.status_code == 201
        created = response.json()
        assert created["is_default"] is False

        assert client.post(
            "/api/v1/base-urls",
            json={"name": "Engine LAN", "pattern": "x"},
        ).status_code == 409

        listed = client.get("/api/v1/base-urls").json()
        assert any(e["name"] == "Engine LAN" for e in listed)

    def test_set_default_clears_previous_default(self, client):
        first = client.post(
            "/api/v1/base-urls", json={"name": "One", "pattern": "acestream://", "is_default": True}
        ).json()
        second = client.post(
            "/api/v1/base-urls", json={"name": "Two", "pattern": "http://h/{channel_id}"}
        ).json()

        response = client.patch(
            f"/api/v1/base-urls/{second['id']}", json={"is_default": True}
        )
        assert response.status_code == 200
        listed = {e["name"]: e for e in client.get("/api/v1/base-urls").json()}
        assert listed["Two"]["is_default"] is True
        assert listed["One"]["is_default"] is False

    def test_pid_only_pattern_is_rejected(self, client):
        response = client.post(
            "/api/v1/base-urls",
            json={"name": "Broken", "pattern": "http://h/play?pid={pid}"},
        )
        assert response.status_code == 422

        entry = client.post(
            "/api/v1/base-urls", json={"name": "Fine", "pattern": "acestream://"}
        ).json()
        response = client.patch(
            f"/api/v1/base-urls/{entry['id']}", json={"pattern": "x?pid={pid}"}
        )
        assert response.status_code == 422

    def test_delete_and_missing(self, client):
        entry = client.post(
            "/api/v1/base-urls", json={"name": "Gone", "pattern": "x://"}
        ).json()
        assert client.delete(f"/api/v1/base-urls/{entry['id']}").status_code == 204
        assert client.delete(f"/api/v1/base-urls/{entry['id']}").status_code == 404
        assert client.patch(
            f"/api/v1/base-urls/{entry['id']}", json={"name": "Nope"}
        ).status_code == 404


class TestPlaylistResolution:
    def _add_channel(self, client):
        response = client.post(
            "/api/v1/channels",
            json={"id": CID, "name": "Test Channel"},
        )
        assert response.status_code in (200, 201), response.text
        return CID

    def test_playlist_uses_default_named_base_url(self, client):
        self._add_channel(client)
        client.post(
            "/api/v1/base-urls",
            json={
                "name": "Masked",
                "pattern": "http://nas:8080/ace/stream?id={channel_id}",
                "is_default": True,
            },
        )
        content = client.get("/api/v1/playlists/m3u?only_online=false").text
        assert f"http://nas:8080/ace/stream?id={CID}" in content

    def test_playlist_base_url_id_selects_named_entry(self, client):
        self._add_channel(client)
        client.post(
            "/api/v1/base-urls",
            json={"name": "Default", "pattern": "acestream://", "is_default": True},
        )
        other = client.post(
            "/api/v1/base-urls",
            json={"name": "Acexy", "pattern": "http://acexy:8080/ace/getstream?id={channel_id}"},
        ).json()

        content = client.get(
            f"/api/v1/playlists/m3u?only_online=false&base_url_id={other['id']}"
        ).text
        assert f"http://acexy:8080/ace/getstream?id={CID}" in content

    def test_explicit_base_url_string_wins(self, client):
        self._add_channel(client)
        client.post(
            "/api/v1/base-urls",
            json={"name": "Default", "pattern": "http://nope/{channel_id}", "is_default": True},
        )
        content = client.get(
            "/api/v1/playlists/m3u?only_online=false&base_url=custom://"
        ).text
        assert f"custom://{CID}" in content

    def test_unknown_base_url_id_is_404(self, client):
        self._add_channel(client)
        response = client.get("/api/v1/playlists/m3u?only_online=false&base_url_id=99999")
        assert response.status_code == 404

    def test_unknown_base_url_id_is_404_on_player_routes(self, client):
        self._add_channel(client)
        for path in ("/playlists/m3u", "/playlist.m3u"):
            response = client.get(f"{path}?only_online=false&base_url_id=99999")
            assert response.status_code == 404, path
            assert response.text.startswith("#EXTM3U")

    def test_without_entries_falls_back_to_legacy_setting(self, client):
        self._add_channel(client)
        content = client.get("/api/v1/playlists/m3u?only_online=false").text
        assert f"acestream://{CID}" in content
